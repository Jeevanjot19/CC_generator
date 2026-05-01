from __future__ import annotations

import math
import statistics
import wave
from pathlib import Path

from .config import AudioConfig
from .event import Event


class AudioBackendError(RuntimeError):
    pass


def _read_wav_mono(path: Path) -> tuple[list[float], int]:
    with wave.open(str(path), "rb") as reader:
        channels = reader.getnchannels()
        sample_width = reader.getsampwidth()
        sample_rate = reader.getframerate()
        frames = reader.readframes(reader.getnframes())

    if sample_width != 2:
        raise ValueError("Only 16-bit PCM WAV is supported by the demo detector.")

    samples: list[float] = []
    step = sample_width * channels
    scale = 32768.0
    for index in range(0, len(frames), step):
        channel_values = []
        for channel in range(channels):
            start = index + channel * sample_width
            value = int.from_bytes(frames[start : start + 2], "little", signed=True)
            channel_values.append(value / scale)
        samples.append(sum(channel_values) / len(channel_values))
    return samples, sample_rate


def _rms(samples: list[float]) -> float:
    if not samples:
        return 0.0
    return math.sqrt(sum(sample * sample for sample in samples) / len(samples))


# Heuristic classification thresholds (empirically determined, not optimized)
AUDIO_HEURISTIC_SHARP_IMPACT_DURATION_MAX = 0.38  # Max duration for "sharp" classification
AUDIO_HEURISTIC_SHARP_IMPACT_ENERGY_MIN = 0.10   # Min energy for "sharp" classification
AUDIO_HEURISTIC_SUSTAINED_DURATION_MIN = 1.35    # Min duration for "sustained" classification

# Confidence calculation parameters for heuristic detector
AUDIO_HEURISTIC_BASE_CONFIDENCE = 0.45  # Minimum confidence floor
AUDIO_HEURISTIC_MAX_CONFIDENCE_DELTA = 0.5  # Maximum additional confidence from energy
AUDIO_HEURISTIC_PEAK_RATIO_SENSITIVITY = 3.0  # Divisor for energy normalization


def _classify(duration: float, peak_energy: float) -> str:
    """Classify audio event by duration and energy (heuristic, not ML-based).
    
    This is a simple baseline classifier without external ML dependencies.
    For production use, integrate YAMNet which provides 500+ audio classes.
    """
    if duration <= AUDIO_HEURISTIC_SHARP_IMPACT_DURATION_MAX and peak_energy >= AUDIO_HEURISTIC_SHARP_IMPACT_ENERGY_MIN:
        return "sharp_impact"
    if duration >= AUDIO_HEURISTIC_SUSTAINED_DURATION_MIN:
        return "sustained_sound"
    return "loud_sound"


def detect_heuristic_events(wav_path: Path, config: AudioConfig) -> list[Event]:
    samples, sample_rate = _read_wav_mono(wav_path)
    if not samples:
        return []

    frame_size = max(1, int(config.frame_seconds * sample_rate))
    hop_size = max(1, int(config.hop_seconds * sample_rate))

    frames: list[tuple[float, float]] = []
    for start in range(0, max(1, len(samples) - frame_size + 1), hop_size):
        chunk = samples[start : start + frame_size]
        frames.append((start / sample_rate, _rms(chunk)))

    if not frames:
        return []

    noise_floor = statistics.median(energy for _, energy in frames)
    threshold = max(config.energy_threshold, noise_floor * config.noise_ratio)

    spans: list[tuple[float, float, float]] = []
    current_start: float | None = None
    current_end = 0.0
    current_peak = 0.0

    for frame_start, energy in frames:
        frame_end = frame_start + config.frame_seconds
        if energy >= threshold:
            if current_start is None:
                current_start = frame_start
                current_peak = energy
            current_end = frame_end
            current_peak = max(current_peak, energy)
        elif current_start is not None:
            spans.append((current_start, current_end, current_peak))
            current_start = None
            current_peak = 0.0
    if current_start is not None:
        spans.append((current_start, current_end, current_peak))

    merged: list[tuple[float, float, float]] = []
    for start, end, peak in spans:
        if not merged or start - merged[-1][1] > config.gap_tolerance:
            merged.append((start, end, peak))
        else:
            prev_start, prev_end, prev_peak = merged[-1]
            merged[-1] = (prev_start, max(prev_end, end), max(prev_peak, peak))

    events: list[Event] = []
    for start, end, peak in merged:
        duration = end - start
        if duration < config.min_event_duration:
            continue
        # Confidence is base + energy-normalized delta, bounded to [0.45, 0.95]
        confidence = (AUDIO_HEURISTIC_BASE_CONFIDENCE + 
                     min(AUDIO_HEURISTIC_MAX_CONFIDENCE_DELTA, 
                         max(0.0, (peak / threshold - 1.0) / AUDIO_HEURISTIC_PEAK_RATIO_SENSITIVITY)))
        events.append(Event.candidate(start, end, _classify(duration, peak), confidence))
    return events


def detect_yamnet_events(wav_path: Path, config: AudioConfig) -> list[Event]:
    try:
        import mediapipe as mp
        import numpy as np
    except ImportError as exc:
        raise AudioBackendError(
            "The YAMNet backend uses MediaPipe's AudioClassifier and requires "
            "mediapipe plus numpy in the active environment. Install them in the "
            "project venv or use audio.model='heuristic'."
        ) from exc

    model_path = Path(config.yamnet_model_path)
    if not model_path.exists():
        raise AudioBackendError(
            f"YAMNet model file does not exist: {model_path}. "
            "Download yamnet.tflite into the models directory."
        )

    samples, sample_rate = _read_wav_mono(wav_path)
    if not samples:
        return []

    audio_data = mp.tasks.components.containers.AudioData.create_from_array(
        np.asarray(samples, dtype=np.float32),
        sample_rate,
    )
    options = mp.tasks.audio.AudioClassifierOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(model_path)),
        running_mode=mp.tasks.audio.RunningMode.AUDIO_CLIPS,
        max_results=8,
    )
    blocklist = {
        "Silence",
        "Speech",
        "Inside, small room",
        "Music",
        "Musical instrument",
        "Singing",
        "Narration, monologue",
    }

    candidates: list[Event] = []
    with mp.tasks.audio.AudioClassifier.create_from_options(options) as classifier:
        results = classifier.classify(audio_data)
        for result in results:
            timestamp = max(0.0, result.timestamp_ms / 1000.0)
            categories = result.classifications[0].categories if result.classifications else []
            chosen = None
            for category in categories:
                if category.category_name in blocklist:
                    continue
                if category.score >= config.energy_threshold:
                    chosen = category
                    break
            if chosen is None:
                continue
            candidates.append(
                Event.candidate(
                    timestamp,
                    timestamp + 0.975,
                    chosen.category_name,
                    float(chosen.score),
                )
            )

    if not candidates:
        return []

    merged: list[Event] = []
    for event in candidates:
        if (
            merged
            and merged[-1].audio_class == event.audio_class
            and event.t_start - merged[-1].t_end <= config.gap_tolerance
        ):
            merged[-1].t_end = event.t_end
            merged[-1].audio_confidence = round(
                max(merged[-1].audio_confidence, event.audio_confidence),
                3,
            )
        else:
            merged.append(event)
    return [event for event in merged if event.t_end - event.t_start >= config.min_event_duration]


def detect_audio_events(wav_path: Path, config: AudioConfig) -> list[Event]:
    if config.model == "heuristic":
        return detect_heuristic_events(wav_path, config)
    if config.model == "yamnet":
        return detect_yamnet_events(wav_path, config)
    raise AudioBackendError(
        f"Unknown audio model '{config.model}'. Supported models: heuristic, yamnet."
    )
