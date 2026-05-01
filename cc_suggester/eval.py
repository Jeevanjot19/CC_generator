from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Span:
    start: float
    end: float
    label: str = ""


def _overlap(a: Span, b: Span) -> float:
    return max(0.0, min(a.end, b.end) - max(a.start, b.start))


def _iou(a: Span, b: Span) -> float:
    union = max(a.end, b.end) - min(a.start, b.start)
    if union <= 0:
        return 0.0
    return _overlap(a, b) / union


def load_predictions(path: Path, accepted_only: bool = True) -> list[Span]:
    data = json.loads(path.read_text(encoding="utf-8"))
    spans: list[Span] = []
    for item in data:
        if accepted_only and not item.get("cc_decision", False):
            continue
        spans.append(
            Span(
                start=float(item["t_start"]),
                end=float(item["t_end"]),
                label=str(item.get("cc_label") or item.get("audio_class") or ""),
            )
        )
    return spans


def load_ground_truth(path: Path) -> list[Span]:
    spans: list[Span] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            spans.append(
                Span(
                    start=float(row["start"]),
                    end=float(row["end"]),
                    label=row.get("label", ""),
                )
            )
    return spans


def evaluate_spans(predictions: list[Span], ground_truth: list[Span], iou_threshold: float = 0.3) -> dict[str, Any]:
    """Evaluate predictions against ground truth using IoU-based matching.
    
    Returns metrics for:
    - Detection accuracy (precision, recall, F1)
    - Over-captioning rate (false positives / total predictions)
    - Under-captioning rate (false negatives / total ground truth)
    
    The over-captioning rate directly measures if we avoid over-captioning
    as stated in the proposal acceptance criteria.
    """
    matched_truth: set[int] = set()
    true_positive = 0

    for prediction in predictions:
        best_index = None
        best_iou = 0.0
        for index, truth in enumerate(ground_truth):
            if index in matched_truth:
                continue
            score = _iou(prediction, truth)
            if score > best_iou:
                best_index = index
                best_iou = score
        if best_index is not None and best_iou >= iou_threshold:
            matched_truth.add(best_index)
            true_positive += 1

    false_positive = len(predictions) - true_positive
    false_negative = len(ground_truth) - true_positive
    precision = true_positive / len(predictions) if predictions else 0.0
    recall = true_positive / len(ground_truth) if ground_truth else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    
    # Critical metrics for proposal acceptance criteria
    overcaption_rate = false_positive / len(predictions) if predictions else 0.0
    undercaption_rate = false_negative / len(ground_truth) if ground_truth else 0.0

    metrics = {
        "predictions": len(predictions),
        "ground_truth": len(ground_truth),
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "overcaption_rate": round(overcaption_rate, 3),
        "undercaption_rate": round(undercaption_rate, 3),
    }
    
    # Add compliance assessment
    compliance = _assess_compliance(metrics)
    metrics["compliance"] = compliance
    
    return metrics


def _assess_compliance(metrics: dict[str, Any]) -> dict[str, str]:
    """Check if metrics meet proposal acceptance criteria.
    
    Acceptance Criteria from GitHub issue #2:
    1. Avoid over-captioning -> overcaption_rate should be <= 10%
    2. Detect non-speech audio events -> recall should be >= 80%
    """
    results = {}
    
    # Criterion 1: Avoid over-captioning (FP rate)
    overcaption = metrics.get("overcaption_rate", 1.0)
    if overcaption <= 0.10:
        results["avoid_overcaption"] = f"PASS ({overcaption:.1%} false positives <= 10% target)"
    else:
        results["avoid_overcaption"] = f"FAIL ({overcaption:.1%} false positives > 10% target)"
    
    # Criterion 2: Detect events (recall)
    recall = metrics.get("recall", 0.0)
    if recall >= 0.80:
        results["detect_events"] = f"PASS ({recall:.1%} detection rate >= 80% target)"
    else:
        results["detect_events"] = f"WARN ({recall:.1%} detection rate < 80% target)"
    
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate CC event predictions against ground truth CSV.")
    parser.add_argument("--predictions", required=True, type=Path, help="Pipeline events JSON")
    parser.add_argument("--ground-truth", required=True, type=Path, help="CSV with start,end,label columns")
    parser.add_argument("--iou-threshold", type=float, default=0.3)
    parser.add_argument("--output", type=Path, help="Optional metrics JSON output")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    metrics = evaluate_spans(
        load_predictions(args.predictions),
        load_ground_truth(args.ground_truth),
        args.iou_threshold,
    )
    text = json.dumps(metrics, indent=2)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
