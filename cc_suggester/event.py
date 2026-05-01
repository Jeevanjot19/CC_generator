from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
from uuid import uuid4


@dataclass
class Event:
    event_id: str
    t_start: float
    t_end: float
    audio_class: str
    audio_confidence: float
    reaction_score: float = 0.0
    reaction_type: str | None = None
    fusion_score: float = 0.0
    cc_decision: bool = False
    cc_label: str | None = None
    notes: list[str] | None = None

    @classmethod
    def candidate(
        cls,
        t_start: float,
        t_end: float,
        audio_class: str,
        audio_confidence: float,
    ) -> "Event":
        return cls(
            event_id=str(uuid4()),
            t_start=round(max(0.0, t_start), 3),
            t_end=round(max(t_start, t_end), 3),
            audio_class=audio_class,
            audio_confidence=round(max(0.0, min(1.0, audio_confidence)), 3),
            notes=[],
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["duration"] = round(self.t_end - self.t_start, 3)
        return data
