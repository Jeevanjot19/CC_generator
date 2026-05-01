from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_config
from .media import MediaDependencyError
from .pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Suggest meaningful non-speech closed captions for a media file."
    )
    parser.add_argument("--input", required=True, type=Path, help="Input .wav or video file")
    parser.add_argument("--output", required=True, type=Path, help="Output .srt or .sls path")
    parser.add_argument(
        "--format",
        choices=["srt", "sls", "both"],
        default="srt",
        help="Caption output format",
    )
    parser.add_argument("--events-json", type=Path, help="Optional debug event JSON path")
    parser.add_argument("--report-html", type=Path, help="Optional HTML report path")
    parser.add_argument("--config", type=Path, help="Optional .json/.yaml config path")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        config = load_config(args.config)
        events, metrics = run_pipeline(
            args.input,
            args.output,
            args.format,
            args.events_json,
            args.report_html,
            config,
        )
    except MediaDependencyError as exc:
        print(f"Dependency error: {exc}")
        return 2
    except Exception as exc:
        print(f"Pipeline error: {exc}")
        return 1

    accepted = sum(1 for event in events if event.cc_decision)
    print(f"Detected {len(events)} audio candidate(s); accepted {accepted} CC suggestion(s).")
    print(f"Wrote {args.format} output to {args.output}")
    if args.events_json:
        print(f"Wrote event details to {args.events_json}")
    if args.report_html:
        print(f"Wrote HTML report to {args.report_html}")
    print(f"Pipeline metrics: total={metrics.total_time:.3f}s, audio={metrics.audio_detection_time:.3f}s, "
          f"visual={metrics.visual_detection_time:.3f}s, fusion={metrics.fusion_time:.3f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
