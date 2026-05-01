from __future__ import annotations

import json
from pathlib import Path

from .event import Event


def format_srt_timestamp(seconds: float) -> str:
    millis = int(round(seconds * 1000))
    hours, remainder = divmod(millis, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def write_events_json(events: list[Event], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([event.to_dict() for event in events], indent=2),
        encoding="utf-8",
    )


def write_srt(events: list[Event], path: Path, embed_scores: bool = False) -> None:
    accepted = [event for event in events if event.cc_decision]
    blocks: list[str] = []
    for index, event in enumerate(accepted, start=1):
        text = event.cc_label or "[Sound effect]"
        if embed_scores:
            text = (
                f"{text}\n"
                f"NOTE audio={event.audio_confidence:.2f} "
                f"reaction={event.reaction_score:.2f} fusion={event.fusion_score:.2f}"
            )
        blocks.append(
            "\n".join(
                [
                    str(index),
                    f"{format_srt_timestamp(event.t_start)} --> {format_srt_timestamp(event.t_end)}",
                    text,
                ]
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n\n".join(blocks) + ("\n" if blocks else ""), encoding="utf-8")


def write_sls(events: list[Event], path: Path) -> None:
    accepted = [event for event in events if event.cc_decision]
    lines = ["# PlanetRead Intelligent CC Suggestion Tool - SLS demo output"]
    for event in accepted:
        lines.append(
            "|".join(
                [
                    f"{event.t_start:.3f}",
                    f"{event.t_end:.3f}",
                    event.cc_label or "[Sound effect]",
                    f"audio={event.audio_confidence:.3f}",
                    f"reaction={event.reaction_score:.3f}",
                    f"fusion={event.fusion_score:.3f}",
                ]
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
