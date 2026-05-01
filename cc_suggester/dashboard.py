from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_event_rows(path: Path) -> list[dict[str, Any]]:
    events = json.loads(path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for event in events:
        rows.append(
            {
                "start": event["t_start"],
                "end": event["t_end"],
                "label": event.get("cc_label") or event.get("audio_class"),
                "audio": event.get("audio_confidence", 0.0),
                "reaction": event.get("reaction_score", 0.0),
                "fusion": event.get("fusion_score", 0.0),
                "decision": "Accepted" if event.get("cc_decision") else "Rejected",
                "notes": ", ".join(event.get("notes") or []),
            }
        )
    return rows


def main() -> None:
    import streamlit as st

    st.set_page_config(page_title="CC Suggestion Reviewer", layout="wide")
    st.title("Intelligent CC Suggestion Reviewer")
    st.caption("Review event-level scores and generated caption suggestions.")

    path_text = st.text_input("Events JSON path", value="out/video_events.json")
    path = Path(path_text)
    if not path.exists():
        st.warning("Run the pipeline first, or enter a valid events JSON path.")
        return

    rows = load_event_rows(path)
    accepted = sum(1 for row in rows if row["decision"] == "Accepted")
    rejected = len(rows) - accepted

    col1, col2, col3 = st.columns(3)
    col1.metric("Audio candidates", len(rows))
    col2.metric("Accepted captions", accepted)
    col3.metric("Rejected events", rejected)

    st.dataframe(rows, use_container_width=True, hide_index=True)

    accepted_rows = [row for row in rows if row["decision"] == "Accepted"]
    if accepted_rows:
        st.subheader("SRT Preview")
        preview = []
        for index, row in enumerate(accepted_rows, start=1):
            preview.append(f"{index}\n{row['start']:.3f} --> {row['end']:.3f}\n{row['label']}")
        st.code("\n\n".join(preview), language="text")


if __name__ == "__main__":
    main()
