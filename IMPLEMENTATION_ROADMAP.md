# Actionable Improvements: Code Changes & Implementation Roadmap

## PRIORITY 1: Critical Fixes (Required for Proposal Demo)

### 1.1 Extract Magic Numbers to Named Constants

**File:** [cc_suggester/config.py](cc_suggester/config.py)

**Issue:** Constants like 0.45, 0.5, 0.6, 0.4 scattered throughout code without documentation

**Change:**
```python
# Add to config.py
@dataclass(frozen=True)
class AudioHeuristicParams:
    """Heuristic audio detection tuning parameters - calibrated without training data."""
    base_confidence: float = 0.45  # Minimum confidence offset
    max_confidence_delta: float = 0.5  # Max additional confidence from energy ratio
    peak_ratio_sensitivity: float = 3.0  # Divisor for energy normalization
    
@dataclass(frozen=True)
class FusionConfig:
    # Current (untested) values - REQUIRES VALIDATION ON GROUND TRUTH
    alpha: float = 0.60  # Audio weight (increase → more audio-driven)
    beta: float = 0.40   # Visual weight (increase → more visual-driven)
    
    # Decision thresholds - THESE VALUES REQUIRE TUNING
    decision_threshold: float = 0.55  # Minimum fusion score for acceptance
    audio_override_threshold: float = 0.92  # Override if audio alone very high
    reaction_override_threshold: float = 0.88  # Override if visual alone very high
    
    # These thresholds ARE ARBITRARY and must be validated on real data
    # TODOs:
    # - Sweep thresholds to find optimal Precision/Recall tradeoff
    # - Report optimal thresholds with validation metrics
    # - Consider class-specific thresholds (explosion vs. traffic noise)
```

**Benefits:**
- ✅ Clarifies that these values are untested/arbitrary
- ✅ Single point of change for threshold tuning
- ✅ Self-documents that this requires validation

---

### 1.2 Add Over-Captioning Metric to Evaluation

**File:** [cc_suggester/eval.py](cc_suggester/eval.py)

**Current:** Only precision/recall/F1 computed

**Enhancement:**
```python
@dataclass
class EvaluationMetrics:
    """Evaluation results with over-captioning analysis."""
    predictions: int
    ground_truth: int
    true_positive: int
    false_positive: int
    false_negative: int
    precision: float
    recall: float
    f1: float
    
    # NEW: Over-captioning metrics
    overcaption_rate: float = 0.0  # FP / (TP + FP) - fraction of captions that are wrong
    undercaption_rate: float = 0.0  # FN / (TP + FN) - fraction of correct events missed
    
    def assess_compliance(self) -> dict[str, str]:
        """Check if metrics meet proposal acceptance criteria."""
        results = {}
        
        # Acceptance Criteria: "avoid over-captioning"
        if self.overcaption_rate <= 0.10:  # ≤10% false positives
            results["over_caption"] = "✅ PASS: <10% false positives"
        else:
            results["over_caption"] = f"❌ FAIL: {self.overcaption_rate:.1%} false positives (target: <10%)"
        
        # Acceptance Criteria: "detect non-speech audio events"
        if self.recall >= 0.80:  # ≥80% detection rate
            results["detection"] = "✅ PASS: ≥80% detection rate"
        else:
            results["detection"] = f"⚠️ WARN: {self.recall:.1%} detection rate (target: ≥80%)"
        
        return results

def evaluate_spans(...) -> EvaluationMetrics:
    """Enhanced evaluation with over-captioning analysis."""
    # ... existing code ...
    
    overcaption_rate = false_positive / len(predictions) if predictions else 0.0
    undercaption_rate = false_negative / len(ground_truth) if ground_truth else 0.0
    
    return EvaluationMetrics(
        predictions=len(predictions),
        ground_truth=len(ground_truth),
        true_positive=true_positive,
        false_positive=false_positive,
        false_negative=false_negative,
        precision=round(precision, 3),
        recall=round(recall, 3),
        f1=round(f1, 3),
        overcaption_rate=round(overcaption_rate, 3),
        undercaption_rate=round(undercaption_rate, 3),
    )
```

**Usage:**
```bash
python -m cc_suggester.eval \
  --predictions test-output/events.json \
  --ground-truth samples/ground_truth.csv \
  --output test-output/metrics.json

# Output includes:
# {
#   "overcaption_rate": 0.05,  # ✅ 5% false positives (good)
#   "undercaption_rate": 0.15  # ⚠️ 15% missed events (needs improvement)
# }
```

---

### 1.3 Add Temporal Alignment Validation

**File:** [cc_suggester/visual.py](cc_suggester/visual.py)

**Issue:** Visual reaction detection doesn't check if reaction is temporally aligned to audio event

**New Function:**
```python
def validate_temporal_alignment(
    reaction_score: float,
    reaction_latency: float,  # Time between audio onset and peak visual reaction
    max_acceptable_latency: float = 1.0,  # seconds
    penalty_factor: float = 0.5,
) -> float:
    """
    Penalize visual reactions that are not temporally aligned to audio events.
    
    Example:
    - Audio event: 10:00:00 (onset)
    - Peak visual reaction: 10:00:00.8 (latency = 0.8s) ✅ aligned
    - Score: 0.8 * (1.0 - penalty) ≈ high
    
    - Peak visual reaction: 10:00:05 (latency = 5.0s) ❌ likely unrelated
    - Score: 0.8 * (1.0 - large_penalty) ≈ low
    """
    if reaction_latency <= max_acceptable_latency:
        # Within expected neurological response time (~200-800ms)
        return reaction_score  # No penalty
    
    # Outside expected window - likely unrelated coincidence
    excess_latency = reaction_latency - max_acceptable_latency
    penalty = penalty_factor * min(1.0, excess_latency / max_acceptable_latency)
    adjusted = reaction_score * (1.0 - penalty)
    return max(0.0, adjusted)

# Integration into score_mediapipe_reactions():
# Compute reaction_latency as time of peak landmark distance
# Apply penalty before returning reaction_score
```

**Impact:**
- Reduces false positives from coincidental reactions
- Adds semantic correctness (reactions should follow sound)

---

### 1.4 Add Logging Infrastructure

**File:** [cc_suggester/pipeline.py](cc_suggester/pipeline.py)

**Current:** Only print() statements

**Enhancement:**
```python
import logging
import json
import time
from typing import NamedTuple

class PipelineMetrics(NamedTuple):
    """Structured logging of pipeline execution."""
    total_time: float
    audio_detection_time: float
    visual_detection_time: float
    fusion_time: float
    num_audio_candidates: int
    num_accepted: int
    
    def to_dict(self) -> dict:
        return self._asdict()

def setup_logging(log_file: Path | None = None) -> logging.Logger:
    """Configure structured logging."""
    logger = logging.getLogger("cc_suggester")
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)
    
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def run_pipeline(...) -> tuple[list[Event], PipelineMetrics]:
    """Enhanced pipeline with timing and structured logging."""
    logger = setup_logging()
    
    start_time = time.time()
    
    # Audio detection with timing
    logger.info(f"Detecting audio events from {input_path}")
    audio_start = time.time()
    events = detect_audio_events(wav_path, config.audio)
    audio_time = time.time() - audio_start
    logger.info(f"Audio detection: {len(events)} candidates in {audio_time:.3f}s")
    
    # Visual scoring with timing
    logger.info(f"Scoring visual reactions")
    visual_start = time.time()
    score_visual_reactions(video_path, events, config.visual)
    visual_time = time.time() - visual_start
    logger.info(f"Visual scoring completed in {visual_time:.3f}s")
    
    # Fusion with timing
    fusion_start = time.time()
    apply_decisions(events, config)
    fusion_time = time.time() - fusion_start
    
    total_time = time.time() - start_time
    accepted = sum(1 for event in events if event.cc_decision)
    
    metrics = PipelineMetrics(
        total_time=total_time,
        audio_detection_time=audio_time,
        visual_detection_time=visual_time,
        fusion_time=fusion_time,
        num_audio_candidates=len(events),
        num_accepted=accepted,
    )
    
    logger.info(f"Pipeline completed in {total_time:.3f}s: "
                f"{len(events)} candidates → {accepted} accepted")
    
    # Save metrics for analysis
    if events_json:
        metrics_path = events_json.with_name(f"{events_json.stem}.metrics.json")
        metrics_path.write_text(json.dumps(metrics.to_dict()), encoding="utf-8")
    
    return events, metrics
```

**Benefit:** ✅ Enables performance profiling, debugging, and operational monitoring

---

## PRIORITY 2: High-Impact Features (for Proposal Demo)

### 2.1 Model Download Script

**File:** [scripts/download_models.sh](scripts/download_models.sh) (NEW)

```bash
#!/bin/bash
# Download required ML models for full pipeline

set -e

MODELS_DIR="models"
mkdir -p "$MODELS_DIR"

echo "Downloading YAMNet model..."
wget -O "$MODELS_DIR/yamnet.tflite" \
  "https://storage.googleapis.com/mediapipe-models/audio_classifier/yamnet/float32/1/yamnet.tflite" \
  --quiet --show-progress

echo "Downloading MediaPipe Pose Landmarker..."
wget -O "$MODELS_DIR/pose_landmarker_lite.task" \
  "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite.task" \
  --quiet --show-progress

echo "Downloading MediaPipe Face Landmarker..."
wget -O "$MODELS_DIR/face_landmarker.task" \
  "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker.task" \
  --quiet --show-progress

echo "✅ All models downloaded successfully!"
```

**Windows version:** [scripts/download_models.ps1](scripts/download_models.ps1) (NEW)

```powershell
# PowerShell equivalent
$ModelsDir = "models"
New-Item -ItemType Directory -Force -Path $ModelsDir | Out-Null

Write-Host "Downloading YAMNet model..."
Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/audio_classifier/yamnet/float32/1/yamnet.tflite" `
  -OutFile "$ModelsDir/yamnet.tflite"

Write-Host "Downloading MediaPipe Pose Landmarker..."
Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite.task" `
  -OutFile "$ModelsDir/pose_landmarker_lite.task"

Write-Host "Downloading MediaPipe Face Landmarker..."
Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker.task" `
  -OutFile "$ModelsDir/face_landmarker.task"

Write-Host "✅ All models downloaded successfully!"
```

**Usage:**
```bash
# Linux/Mac
bash scripts/download_models.sh

# Windows PowerShell
powershell -ExecutionPolicy Bypass -File scripts/download_models.ps1

# Auto-download on first run
python -m cc_suggester.cli --input video.mp4 --output captions.srt --auto-download-models
```

---

### 2.2 Ground Truth Annotation Template

**File:** [samples/ground_truth_template.csv](samples/ground_truth_template.csv) (NEW)

```csv
start,end,label,speaker_reaction,audio_class
0.5,1.2,honking,yes,car_horn
2.3,2.8,glass_breaking,yes,glass
5.1,6.5,laughter,subtle,speech
8.0,9.2,siren,yes,alarm
...
```

**Usage Guide:** [ANNOTATION_GUIDE.md](ANNOTATION_GUIDE.md) (NEW)

```markdown
# Annotation Guide for CC Suggestion Ground Truth

## CSV Format
- **start** (float): Event start time in seconds
- **end** (float): Event end time in seconds  
- **label** (string): Event class (e.g., "honking", "laughter")
- **speaker_reaction** (yes/no/subtle): Did speaker react visibly?
- **audio_class** (string): YAMNet class if available

## Protocol
1. Watch video and listen for non-speech audio events
2. For each event, record start/end timestamps
3. Classify by audio class (or use heuristic: sharp/sustained/loud)
4. Note if speaker reacted visibly (yes/no/subtle)
5. Consensus: 2 annotators, resolve disagreements

## Quality Criteria
- Timing precision: ±0.1s
- Class agreement: ≥80% inter-annotator agreement
- Minimum events per video: ≥5
```

---

### 2.3 Validation Report Enhancement

**File:** [cc_suggester/report.py](cc_suggester/report.py) (Enhanced)

```python
def render_validation_report(
    events: list[Event],
    input_path: Path,
    output_path: Path,
    metrics: EvaluationMetrics | None = None,  # Optional ground truth comparison
    logs: dict[str, Any] | None = None,  # Performance logs
) -> str:
    """
    Generate HTML report with:
    1. Event detection summary
    2. Fusion decision breakdown
    3. Over-captioning metrics (if ground truth provided)
    4. Performance profile (if logs provided)
    """
    
    # Existing content + NEW sections:
    
    # Section: Over-Captioning Risk Assessment
    overcaption_section = ""
    if metrics:
        overcaption_section = f"""
        <section>
          <h2>Proposal Compliance Check</h2>
          <div class="compliance">
            <h3>Acceptance Criteria: "Avoid Over-Captioning"</h3>
            <div class="metric">
              <label>False Positive Rate:</label>
              <value class="{'pass' if metrics.overcaption_rate <= 0.1 else 'fail'}">
                {metrics.overcaption_rate:.1%}
              </value>
              <status>{'✅ PASS' if metrics.overcaption_rate <= 0.1 else '❌ FAIL'}</status>
            </div>
            <h3>Acceptance Criteria: "Successfully Detect Events"</h3>
            <div class="metric">
              <label>Recall (Detection Rate):</label>
              <value class="{'pass' if metrics.recall >= 0.8 else 'fail'}">
                {metrics.recall:.1%}
              </value>
              <status>{'✅ PASS' if metrics.recall >= 0.8 else '⚠️ NEEDS WORK'}</status>
            </div>
          </div>
        </section>
        """
    
    # Section: Performance Profile
    perf_section = ""
    if logs:
        perf_section = f"""
        <section>
          <h2>Performance Profile</h2>
          <table>
            <tr>
              <td>Audio Detection:</td>
              <td>{logs.get('audio_time', 0):.3f}s</td>
            </tr>
            <tr>
              <td>Visual Scoring:</td>
              <td>{logs.get('visual_time', 0):.3f}s</td>
            </tr>
            <tr>
              <td>Total Pipeline:</td>
              <td>{logs.get('total_time', 0):.3f}s</td>
            </tr>
          </table>
        </section>
        """
    
    return f"... existing HTML ... {overcaption_section} {perf_section}"
```

---

## PRIORITY 3: Medium-Term Improvements

### 3.1 Multi-Class Threshold Tuning

**File:** [cc_suggester/tuning.py](cc_suggester/tuning.py) (NEW)

```python
"""
Threshold tuning utilities for finding optimal decision thresholds.
Usage: Sweep decision thresholds to maximize F1 or minimize over-captioning.
"""

from dataclasses import dataclass
import numpy as np

@dataclass
class ThresholdTuningResult:
    threshold: float
    precision: float
    recall: float
    f1: float
    overcaption_rate: float

def sweep_thresholds(
    events: list[Event],
    ground_truth: list[Span],
    thresholds: np.ndarray,  # e.g., np.linspace(0.3, 0.8, 50)
) -> list[ThresholdTuningResult]:
    """Sweep decision thresholds and compute metrics."""
    results = []
    for threshold in thresholds:
        # Temporarily set decision based on this threshold
        for event in events:
            event.cc_decision = (
                event.fusion_score >= threshold
                or event.audio_confidence >= 0.92
                or event.reaction_score >= 0.88
            )
        
        metrics = evaluate_spans(
            load_predictions_from_events(events),
            ground_truth,
        )
        
        results.append(ThresholdTuningResult(
            threshold=threshold,
            precision=metrics.precision,
            recall=metrics.recall,
            f1=metrics.f1,
            overcaption_rate=metrics.overcaption_rate,
        ))
    
    return results

def recommend_threshold(
    results: list[ThresholdTuningResult],
    target: str = "f1",  # or "overcaption_rate"
) -> float:
    """Recommend threshold that maximizes F1 or minimizes over-captions."""
    if target == "f1":
        best = max(results, key=lambda r: r.f1)
        print(f"Recommended threshold: {best.threshold:.3f} (F1={best.f1:.3f})")
    elif target == "overcaption_rate":
        valid = [r for r in results if r.overcaption_rate <= 0.10]
        best = max(valid, key=lambda r: r.f1) if valid else results[0]
        print(f"Recommended threshold: {best.threshold:.3f} "
              f"(F1={best.f1:.3f}, over-caption={best.overcaption_rate:.1%})")
    
    return best.threshold
```

**CLI Usage:**
```bash
python -m cc_suggester.tuning \
  --predictions test-output/events.json \
  --ground-truth samples/ground_truth.csv \
  --output test-output/tuning_curves.html \
  --target f1
```

---

### 3.2 Multi-Language Label Support

**File:** [cc_suggester/labels.py](cc_suggester/labels.py) (NEW)

```python
from dataclasses import dataclass
from typing import dict

@dataclass
class MultilingualLabel:
    """Label with translations."""
    english: str
    hindi: str
    tamil: str | None = None
    bengali: str | None = None

MULTILINGUAL_TAXONOMY = {
    "sharp_impact": MultilingualLabel(
        english="[Impact sound]",
        hindi="[प्रभाव ध्वनि]",
        tamil="[தாக்க ஒலி]",
        bengali="[প্রভাব শব্দ]",
    ),
    "honking": MultilingualLabel(
        english="[Car horn]",
        hindi="[कार सींग]",
        tamil="[கார் ஊதல்]",
        bengali="[গাড়ির শিঙা]",
    ),
    # ... more labels
}

def get_label(audio_class: str, language: str = "en") -> str:
    """Get localized label for event class."""
    label_obj = MULTILINGUAL_TAXONOMY.get(audio_class)
    if not label_obj:
        return f"[{audio_class}]"
    
    attr = {"en": "english", "hi": "hindi", "ta": "tamil", "bn": "bengali"}.get(language, "english")
    return getattr(label_obj, attr) or label_obj.english
```

**Usage:**
```json
{
  "language": "hi",
  "label_taxonomy": "auto"  // Use MULTILINGUAL_TAXONOMY with Hindi labels
}
```

---

## PRIORITY 4: Documentation Improvements

### 4.1 Architecture Decision Record (ADR)

**File:** [docs/ADR-001-fusion-strategy.md](docs/ADR-001-fusion-strategy.md) (NEW)

```markdown
# ADR-001: Fusion Strategy for Audio + Visual Signals

## Context
To avoid over-captioning ambient sounds, we combine:
- Audio confidence (detected event likelihood)
- Visual reaction (speaker/scene response)

## Decision
Use weighted linear fusion: `fusion_score = α * audio + β * visual`
- Default weights: α=0.6, β=0.4 (60% audio-driven)
- Decision threshold: 0.55

## Rationale
- Simple and interpretable
- Allows threshold tuning without model retraining
- Weights can be adjusted per-language/region

## Risks
- Weights are untested (chosen arbitrarily)
- No training data → cannot validate optimality
- May not generalize to all audio environments

## Status
⚠️ UNTESTED - Requires validation on ground truth before production use

## Next Steps
1. Collect annotated Hindi/regional-language videos
2. Sweep fusion weights and thresholds
3. Report optimal weights + validation metrics
4. Consider class-specific weights (explosion → higher, traffic → lower)
```

---

### 4.2 Tuning Guide

**File:** [docs/TUNING_GUIDE.md](docs/TUNING_GUIDE.md) (NEW)

```markdown
# Tuning Guide: Optimizing Fusion Weights and Thresholds

## Quick Start
1. Collect 10-20 videos with ground truth annotations
2. Run threshold sweep:
   ```bash
   python -m cc_suggester.tuning \
     --predictions pred.json --ground-truth truth.csv
   ```
3. Review tuning curves in HTML report
4. Update config with recommended thresholds

## Understanding Metrics
- **Precision:** % of generated captions that are correct (avoid false positives)
- **Recall:** % of correct events that were detected (avoid false negatives)
- **F1:** Harmonic mean of precision + recall
- **Over-caption rate:** FP / (TP + FP) - % of captions that are wrong

## Example Tuning Workflow

### Scenario: Too Many False Positives (Over-Captioning)
- Problem: 20% of generated captions are wrong (music beats, car ambient)
- Solution: Increase decision_threshold (0.55 → 0.65)
  - Trade-off: Recall drops 95% → 85% (miss 10% more real events)
  - Result: False positives drop 20% → 5%

### Scenario: Missing Events (Under-Captioning)
- Problem: Only detecting 70% of real events
- Solution: Decrease decision_threshold (0.55 → 0.45)
  - Trade-off: Precision drops 90% → 75% (10% of captions wrong)
  - Result: Recall improves 70% → 92%

## Class-Specific Tuning (Advanced)
```json
{
  "fusion_per_class": {
    "explosion": { "alpha": 0.7, "beta": 0.3, "threshold": 0.5 },
    "car_horn": { "alpha": 0.5, "beta": 0.5, "threshold": 0.6 },
    "laughter": { "alpha": 0.4, "beta": 0.6, "threshold": 0.55 }
  }
}
```
- Explosions: mostly audio-driven (rare visual false positives)
- Laughter: visual context more important (overlaps with speech)
```

---

## Summary Table: Implementation Roadmap

| Task | Priority | Effort | Impact | Owner |
|------|----------|--------|--------|-------|
| Extract magic numbers to constants | 1 | 2h | Clarity | Dev |
| Add over-captioning metric | 1 | 4h | Required for validation | Dev |
| Temporal alignment validation | 1 | 6h | Reduces false positives | ML |
| Logging infrastructure | 1 | 4h | Observability | Dev |
| Model download script | 2 | 2h | Ease of setup | DevOps |
| Ground truth annotation guide | 2 | 4h | Enables tuning | ML |
| Threshold tuning tools | 2 | 8h | Optimization | ML |
| Validation report enhancement | 2 | 6h | Demo-ready | Dev |
| Multi-language labels | 3 | 4h | Regional support | Dev |
| ADR documentation | 4 | 2h | Knowledge transfer | Tech Lead |
| Tuning guide | 4 | 3h | Operator guide | ML |

---

## Implementation Order (for Proposal Demo)

1. **Week 1:**
   - Extract constants + add logging (Priority 1, 8h)
   - Create ground truth annotation guide (Priority 2, 4h)
   - Test on demo data → generate tuning report

2. **Week 2:**
   - Collect 10 sample Hindi/regional videos with ground truth (16h)
   - Run full validation → report F1, over-caption rates
   - Update proposal with real metrics

3. **Week 3:**
   - Integrate YAMNet (if possible, else note as stretch goal)
   - Create demo video showing end-to-end pipeline
   - Document tuning process + recommendations

4. **Week 4:**
   - Threshold tuning on collected data
   - Finalize proposal with optimized config
   - Submit with confidence metrics
