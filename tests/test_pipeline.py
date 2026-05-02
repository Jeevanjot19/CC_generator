from __future__ import annotations

from pathlib import Path
import importlib.util

import pytest

from cc_suggester.config import DEFAULT_CONFIG, load_config
from cc_suggester.demo_data import create_demo_wav
from cc_suggester.event import Event
from cc_suggester.media import MediaDependencyError, ffmpeg_path
from cc_suggester.output import format_srt_timestamp
from cc_suggester.pipeline import apply_decisions, run_pipeline
from cc_suggester.audio import AudioBackendError
from cc_suggester.visual import VisualBackendError, score_visual_reactions
from cc_suggester.eval import Span, evaluate_spans, load_ground_truth
from cc_suggester.dashboard import load_event_rows


def test_timestamp_formatting() -> None:
    assert format_srt_timestamp(65.432) == "00:01:05,432"


def test_demo_pipeline_writes_srt_and_events() -> None:
    output_dir = Path("test-output")
    wav_path = output_dir / "demo.wav"
    srt_path = output_dir / "demo.srt"
    json_path = output_dir / "events.json"
    create_demo_wav(wav_path)

    events, metrics = run_pipeline(wav_path, srt_path, "srt", json_path)

    assert events
    assert any(event.cc_decision for event in events)
    assert metrics.total_time > 0
    assert srt_path.read_text(encoding="utf-8").strip()
    assert "fusion_score" in json_path.read_text(encoding="utf-8")


def test_pipeline_writes_html_report() -> None:
    output_dir = Path("test-output")
    wav_path = output_dir / "report-demo.wav"
    srt_path = output_dir / "report-demo.srt"
    report_path = output_dir / "report.html"
    create_demo_wav(wav_path)

    events, metrics = run_pipeline(wav_path, srt_path, "srt", report_html=report_path)

    assert events
    assert metrics.audio_detection_time >= 0
    report = report_path.read_text(encoding="utf-8")
    assert "Intelligent CC Suggestion Report" in report
    assert "Accepted captions" in report
    assert "[Loud sound]" in report


def test_pipeline_rejects_missing_input() -> None:
    with pytest.raises(FileNotFoundError, match="Input file does not exist"):
        run_pipeline(Path("missing.mp4"), Path("test-output/missing.srt"))


def test_pipeline_rejects_unsupported_extension() -> None:
    path = Path("test-output/input.txt")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not media", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported input extension"):
        run_pipeline(path, Path("test-output/input.srt"))


def test_video_input_reports_missing_ffmpeg_when_unavailable() -> None:
    if ffmpeg_path() is not None:
        pytest.skip("FFmpeg is installed in this environment.")

    path = Path("test-output/dummy.mp4")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not real video", encoding="utf-8")

    with pytest.raises(MediaDependencyError, match="FFmpeg is required"):
        run_pipeline(path, Path("test-output/dummy.srt"))


def test_apply_decisions_uses_reaction_to_accept_borderline_audio() -> None:
    event = Event.candidate(1.0, 1.5, "sharp_impact", 0.45)
    event.reaction_score = 0.8

    [decided] = apply_decisions([event], DEFAULT_CONFIG)

    assert decided.cc_decision is True
    assert decided.fusion_score == 0.59
    assert decided.cc_label == "[Impact sound]"


def test_load_json_config_overrides_defaults() -> None:
    path = Path("test-output/config.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """
        {
          "fusion": {"decision_threshold": 0.75},
          "label_taxonomy": {"loud_sound": "[Custom loud event]"}
        }
        """,
        encoding="utf-8",
    )

    config = load_config(path)

    assert config.fusion.decision_threshold == 0.75
    assert config.audio.sample_rate == 16000
    assert config.label_taxonomy["loud_sound"] == "[Custom loud event]"


def test_yamnet_backend_reports_missing_dependency() -> None:
    if importlib.util.find_spec("mediapipe") is not None:
        pytest.skip("MediaPipe AudioClassifier is installed in this environment.")

    path = Path("test-output/yamnet-config.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"audio": {"model": "yamnet"}}', encoding="utf-8")
    config = load_config(path)
    wav_path = Path("test-output/yamnet-demo.wav")
    create_demo_wav(wav_path)

    with pytest.raises(AudioBackendError, match="YAMNet backend uses MediaPipe"):
        run_pipeline(wav_path, Path("test-output/yamnet.srt"), config=config)


def test_yamnet_backend_runs_when_mediapipe_is_available() -> None:
    if importlib.util.find_spec("mediapipe") is None:
        pytest.skip("MediaPipe AudioClassifier is not installed in this environment.")
    if not Path("models/yamnet.tflite").exists():
        pytest.skip("YAMNet model file is not available.")

    path = Path("test-output/yamnet-run-config.json")
    path.write_text(
        '{"audio": {"model": "yamnet", "energy_threshold": 0.003}}',
        encoding="utf-8",
    )
    config = load_config(path)
    wav_path = Path("test-output/yamnet-run-demo.wav")
    create_demo_wav(wav_path)

    events, metrics = run_pipeline(wav_path, Path("test-output/yamnet-run.srt"), config=config)

    assert isinstance(events, list)


def test_mediapipe_backend_reports_missing_dependency() -> None:
    if importlib.util.find_spec("mediapipe") is not None:
        pytest.skip("MediaPipe is installed in this environment.")

    path = Path("test-output/mediapipe-config.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"visual": {"backend": "mediapipe"}}', encoding="utf-8")
    config = load_config(path)
    event = Event.candidate(0.0, 0.5, "loud_sound", 0.9)

    with pytest.raises(VisualBackendError, match="MediaPipe backend requires"):
        score_visual_reactions(Path("test-output/dummy.mp4"), [event], config.visual)


def test_visual_backend_can_be_disabled() -> None:
    path = Path("test-output/no-visual-config.json")
    path.write_text('{"visual": {"backend": "none"}}', encoding="utf-8")
    config = load_config(path)
    event = Event.candidate(0.0, 0.5, "loud_sound", 0.9)

    [scored] = score_visual_reactions(Path("test-output/dummy.mp4"), [event], config.visual)

    assert scored.reaction_score == 0.0
    assert scored.notes == ["visual_skipped:disabled"]


def test_evaluate_spans_computes_detection_metrics() -> None:
    predictions = [Span(0.9, 1.5, "a"), Span(4.0, 4.5, "b")]
    ground_truth = [Span(1.0, 1.4, "a"), Span(2.0, 2.5, "c")]

    metrics = evaluate_spans(predictions, ground_truth, iou_threshold=0.25)

    assert metrics["true_positive"] == 1
    assert metrics["false_positive"] == 1
    assert metrics["false_negative"] == 1
    assert metrics["precision"] == 0.5
    assert metrics["recall"] == 0.5


def test_load_ground_truth_csv() -> None:
    path = Path("test-output/ground_truth.csv")
    path.write_text("start,end,label\n0.0,1.0,[Sound]\n", encoding="utf-8")

    spans = load_ground_truth(path)

    assert spans == [Span(0.0, 1.0, "[Sound]")]


def test_dashboard_loads_event_rows() -> None:
    wav_path = Path("test-output/dashboard-demo.wav")
    events_path = Path("test-output/dashboard-events.json")
    create_demo_wav(wav_path)
    run_pipeline(wav_path, Path("test-output/dashboard.srt"), events_json=events_path)

    rows = load_event_rows(events_path)

    assert rows
    assert rows[0]["decision"] == "Accepted"
    assert "audio" in rows[0]
