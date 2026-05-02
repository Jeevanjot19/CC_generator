from __future__ import annotations

import copy
import json
import logging
import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import NamedTuple

from .audio import detect_audio_events
from .config import DEFAULT_CONFIG, PipelineConfig
from .event import Event
from .media import VIDEO_EXTENSIONS, WAV_EXTENSIONS, extract_wav, require_ffmpeg
from .output import write_events_json, write_sls, write_srt
from .report import write_html_report
from .visual import score_visual_reactions


# Configure structured logging
def setup_logging(log_file: Path | None = None) -> logging.Logger:
    """Configure logging with optional file output."""
    logger = logging.getLogger("cc_suggester.pipeline")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        logger.addHandler(console)
        
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    return logger


class PipelineMetrics(NamedTuple):
    """Metrics from pipeline execution for monitoring and optimization."""
    total_time: float
    audio_detection_time: float
    visual_detection_time: float
    fusion_time: float
    num_audio_candidates: int
    num_accepted: int
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return self._asdict()


def apply_decisions(events: list[Event], config: PipelineConfig) -> list[Event]:
    fusion = config.fusion
    for event in events:
        score = fusion.alpha * event.audio_confidence + fusion.beta * event.reaction_score
        event.fusion_score = round(max(0.0, min(1.0, score)), 3)
        event.cc_label = config.label_taxonomy.get(event.audio_class, "[Sound effect]")
        event.cc_decision = (
            event.fusion_score >= fusion.decision_threshold
            or event.audio_confidence >= fusion.audio_override_threshold
            or event.reaction_score >= fusion.reaction_override_threshold
        )
    return events


def _split_long_captions(events: list[Event], max_duration: float) -> list[Event]:
    """Split captions longer than max_duration into multiple shorter captions.
    
    Professional subtitle standards recommend captions no longer than 2-3 seconds.
    This function splits longer captions to meet accessibility and readability standards.
    """
    result = []
    for event in events:
        duration = event.t_end - event.t_start
        if duration <= max_duration:
            result.append(event)
        else:
            # Split into multiple parts
            num_parts = math.ceil(duration / max_duration)
            part_duration = duration / num_parts
            for i in range(num_parts):
                t_start = event.t_start + i * part_duration
                t_end = min(event.t_end, t_start + part_duration)
                part = copy.deepcopy(event)
                part.t_start = t_start
                part.t_end = t_end
                result.append(part)
    return result


def run_pipeline(
    input_path: Path,
    output_path: Path,
    output_format: str = "srt",
    events_json: Path | None = None,
    report_html: Path | None = None,
    config: PipelineConfig = DEFAULT_CONFIG,
    log_file: Path | None = None,
) -> tuple[list[Event], PipelineMetrics]:
    """Run the full CC suggestion pipeline with logging and timing.
    
    Returns:
        Tuple of (events, metrics) where metrics includes execution timing
        and can be logged for performance monitoring.
    """
    logger = setup_logging(log_file)
    
    if not input_path.exists():
        logger.error(f"Input file does not exist: {input_path}")
        raise FileNotFoundError(f"Input file does not exist: {input_path}")

    pipeline_start = time.time()
    logger.info(f"Starting pipeline with {input_path.name} (format: {output_format})")
    
    audio_time = 0.0
    visual_time = 0.0
    
    suffix = input_path.suffix.lower()
    if suffix in WAV_EXTENSIONS:
        wav_path = input_path
        video_path = None
        logger.info(f"Detected WAV input, starting audio detection")
        
        audio_start = time.time()
        events = detect_audio_events(wav_path, config.audio)
        audio_time = time.time() - audio_start
        logger.info(f"Audio detection: {len(events)} candidates in {audio_time:.3f}s")
        
        visual_start = time.time()
        score_visual_reactions(video_path, events, config.visual)
        visual_time = time.time() - visual_start
        logger.info(f"Visual scoring skipped for WAV input")
        
    elif suffix in VIDEO_EXTENSIONS:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        require_ffmpeg()
        wav_path = output_path.with_name(f"{output_path.stem}.audio.tmp.wav")
        video_path = input_path
        
        logger.info(f"Extracting audio from video: {input_path.name}")
        extract_wav(input_path, wav_path, config.audio.sample_rate)
        
        logger.info(f"Starting audio detection on extracted WAV")
        audio_start = time.time()
        events = detect_audio_events(wav_path, config.audio)
        audio_time = time.time() - audio_start
        logger.info(f"Audio detection: {len(events)} candidates in {audio_time:.3f}s")
        
        logger.info(f"Scoring visual reactions for {len(events)} events")
        visual_start = time.time()
        score_visual_reactions(video_path, events, config.visual)
        visual_time = time.time() - visual_start
        logger.info(f"Visual scoring completed in {visual_time:.3f}s")
        
        wav_path.unlink(missing_ok=True)
    else:
        logger.error(f"Unsupported input extension: {suffix}")
        raise ValueError(f"Unsupported input extension: {suffix}")

    logger.info(f"Applying fusion logic and making CC decisions")
    fusion_start = time.time()
    apply_decisions(events, config)
    fusion_time = time.time() - fusion_start
    
    num_candidates = len(events)
    logger.info(f"Fusion complete: {num_candidates} candidates → {sum(1 for e in events if e.cc_decision)} accepted")
    
    # Split long captions to meet subtitle duration standard (≤3s)
    # Apply to entire events list so JSON and SRT are consistent
    events = _split_long_captions(events, config.audio.max_caption_duration)
    logger.info(f"Caption splitting: max {config.audio.max_caption_duration}s applied")
    
    # Now get accepted list from split events
    accepted = [e for e in events if e.cc_decision]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "srt":
        write_srt(accepted, output_path)
        logger.info(f"Wrote SRT output to {output_path}")
    elif output_format == "sls":
        write_sls(accepted, output_path)
        logger.info(f"Wrote SLS output to {output_path}")
    elif output_format == "both":
        write_srt(accepted, output_path.with_suffix(".srt"))
        write_sls(accepted, output_path.with_suffix(".sls"))
        logger.info(f"Wrote SRT and SLS outputs")
    else:
        logger.error(f"Invalid output format: {output_format}")
        raise ValueError("--format must be one of: srt, sls, both")

    # Compute metrics before writing outputs
    total_time = time.time() - pipeline_start
    metrics = PipelineMetrics(
        total_time=total_time,
        audio_detection_time=audio_time,
        visual_detection_time=visual_time,
        fusion_time=fusion_time,
        num_audio_candidates=len(events),
        num_accepted=len(accepted),
    )
    
    # Convert to ReportMetrics for HTML display
    from .report import ReportMetrics
    report_metrics = ReportMetrics(
        total_time=metrics.total_time,
        audio_detection_time=metrics.audio_detection_time,
        visual_detection_time=metrics.visual_detection_time,
        fusion_time=metrics.fusion_time,
        num_audio_candidates=metrics.num_audio_candidates,
        num_accepted=metrics.num_accepted,
    )

    if events_json:
        write_events_json(events, events_json)
        logger.info(f"Wrote events JSON to {events_json}")
        
        # Save metrics alongside events
        metrics_path = events_json.with_name(f"{events_json.stem}.metrics.json")
        metrics_path.write_text(json.dumps(metrics._asdict(), indent=2), encoding="utf-8")
        logger.info(f"Wrote performance metrics to {metrics_path}")
        
    if report_html:
        write_html_report(events, input_path, output_path, report_html, report_metrics)
        logger.info(f"Wrote HTML report to {report_html}")
    
    logger.info(f"Pipeline completed in {total_time:.3f}s (audio: {audio_time:.3f}s, "
                f"visual: {visual_time:.3f}s, fusion: {fusion_time:.3f}s)")
    
    return events, metrics
