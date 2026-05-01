from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AudioConfig:
    model: str = "heuristic"
    yamnet_model_path: str = "models/yamnet.tflite"
    sample_rate: int = 16_000
    frame_seconds: float = 0.25
    hop_seconds: float = 0.125
    min_event_duration: float = 0.18
    gap_tolerance: float = 0.35
    energy_threshold: float = 0.035
    noise_ratio: float = 3.2


@dataclass(frozen=True)
class VisualConfig:
    backend: str = "opencv_motion"
    pose_model_path: str = "models/pose_landmarker_lite.task"
    face_model_path: str = "models/face_landmarker.task"
    context_before: float = 1.0
    context_after: float = 2.0
    fps: int = 4
    width: int = 64
    height: int = 36
    reaction_threshold: float = 0.35


@dataclass(frozen=True)
class FusionConfig:
    """Fusion configuration for combining audio and visual signals.
    
    ⚠️  CRITICAL: These thresholds are DEFAULT VALUES and have NOT been validated
    on real ground truth data. They appear to be reasonable heuristics but lack
    empirical justification. 
    
    To optimize for your content:
    1. Collect annotated videos with ground truth event labels
    2. Run threshold sweep: python -m cc_suggester.tuning --predictions ... --ground-truth ...
    3. Use reported optimal thresholds instead of defaults
    
    See TUNING_GUIDE.md for detailed optimization workflow.
    """
    
    # Weights for combining audio and visual signals
    # Default: 60% audio-driven, 40% visual-driven
    # These should be tuned based on your language/region/content type
    alpha: float = 0.60  # Weight for audio confidence
    beta: float = 0.40   # Weight for visual reaction score
    
    # Decision thresholds - REQUIRES VALIDATION
    # Currently these are untested defaults; adjust based on ground truth evaluation
    decision_threshold: float = 0.55  # Minimum fusion score for acceptance
    audio_override_threshold: float = 0.92  # Accept if audio alone very confident
    reaction_override_threshold: float = 0.88  # Accept if visual reaction very clear


@dataclass(frozen=True)
class PipelineConfig:
    audio: AudioConfig = field(default_factory=AudioConfig)
    visual: VisualConfig = field(default_factory=VisualConfig)
    fusion: FusionConfig = field(default_factory=FusionConfig)
    label_taxonomy: dict[str, str] = field(
        default_factory=lambda: {
            "sharp_impact": "[Impact sound]",
            "loud_sound": "[Loud sound]",
            "sustained_sound": "[Sustained sound]",
            "sound_event": "[Sound effect]",
        }
    )


DEFAULT_CONFIG = PipelineConfig()


def _section(data: dict[str, Any], name: str) -> dict[str, Any]:
    value = data.get(name, {})
    if not isinstance(value, dict):
        raise ValueError(f"Config section '{name}' must be a mapping.")
    return value


def config_from_dict(data: dict[str, Any]) -> PipelineConfig:
    return PipelineConfig(
        audio=AudioConfig(**_section(data, "audio")),
        visual=VisualConfig(**_section(data, "visual")),
        fusion=FusionConfig(**_section(data, "fusion")),
        label_taxonomy={
            **DEFAULT_CONFIG.label_taxonomy,
            **_section(data, "label_taxonomy"),
        },
    )


def load_config(path: Path | None) -> PipelineConfig:
    if path is None:
        return DEFAULT_CONFIG
    if not path.exists():
        raise FileNotFoundError(f"Config file does not exist: {path}")

    suffix = path.suffix.lower()
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
    elif suffix in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError(
                "YAML config support requires PyYAML. Install requirements.txt "
                "or use config/default.json."
            ) from exc
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    else:
        raise ValueError("Config file must be .json, .yaml, or .yml")

    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ValueError("Config root must be a mapping.")
    return config_from_dict(data)
