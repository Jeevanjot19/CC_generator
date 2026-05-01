# NEXT CRITICAL STEPS: Ground Truth Validation & Tuning

**Current Status:** Priority 1 complete, code ready for validation  
**Timeline:** 4-6 weeks to proposal submission with real metrics

---

## STEP 1: Collect Ground Truth Data (Weeks 1-2)

### What You Need
- **Quantity:** 10-20 Hindi/regional-language videos (5-15 min each)
- **Quality:** Clear audio, visible speakers, ≥5 non-speech events per video
- **Events:** Include explosions, honking, laughter, applause, alarms, glass breaking, etc.
- **Reactions:** Capture moments where speakers react (nod, pause, startle)

### Sources
- **Option A (Best):** Record your own videos with actors or real scenarios
- **Option B:** Find Hindi/Tamil/Bengali YouTube videos with good audio
- **Option C:** Use existing video database (if available)

### What to Annotate
Use the template from `ANNOTATION_GUIDE.md`:
```csv
start,end,label
0.5,1.2,honking
2.3,2.8,glass_breaking
5.1,6.5,laughter
```

### Tools
- **Video player:** VLC with frame-by-frame controls
- **Spreadsheet:** Excel/Google Sheets with CSV export
- **Timer:** Audacity (for precise timing in waveform view)

### Quality Process
1. Annotator A labels video independently
2. Annotator B labels same video independently
3. Compare: aim for ≥85% agreement (timestamps within ±0.1s)
4. Resolve disagreements together
5. Average 5-10 minutes per video for annotation

---

## STEP 2: Validate Pipeline on Ground Truth (Week 3)

### Run Evaluation
```bash
# For each annotated video:
python -m cc_suggester.cli \
  --input video.mp4 \
  --output output/video.srt \
  --events-json output/video_events.json \
  --ground-truth annotations/video_ground_truth.csv

# Evaluate predictions
python -m cc_suggester.eval \
  --predictions output/video_events.json \
  --ground-truth annotations/video_ground_truth.csv \
  --output output/video_metrics.json
```

### Aggregate Metrics
Create a summary:
```json
{
  "dataset": "Hindi videos (10 videos, 50 total events)",
  "total_predictions": 48,
  "total_ground_truth": 50,
  "precision": 0.92,           // 44/48 predictions correct
  "recall": 0.88,              // 44/50 ground truth detected
  "f1": 0.90,
  "overcaption_rate": 0.08,    // 8% of captions wrong (PASS: <= 10%)
  "undercaption_rate": 0.12,   // 12% of events missed (needs improvement)
  "compliance": {
    "avoid_overcaption": "PASS",
    "detect_events": "WARN"     // 88% recall < 80% target
  }
}
```

### Success Criteria
- ✅ **overcaption_rate <= 10%** (MANDATORY - avoids over-captioning)
- ✅ **recall >= 80%** (MANDATORY - detects events)
- ✅ **F1 >= 0.85** (NICE-TO-HAVE - overall quality)

---

## STEP 3: Tune Fusion Weights (If Needed) (Week 3-4)

### If Over-Captioning (false positives too high)
**Problem:** 15% of predictions are wrong

**Solution:** Increase decision_threshold
```json
// Before
"fusion": {
  "decision_threshold": 0.55
}

// After (more conservative)
"fusion": {
  "decision_threshold": 0.65
}
```

**Trade-off:** Recall may drop from 90% → 80%, but false positives drop 15% → 8%

### If Under-Detecting (missing too many events)
**Problem:** 70% recall (missing 30% of events)

**Solution:** Decrease decision_threshold
```json
// Before
"fusion": {
  "decision_threshold": 0.55
}

// After (more aggressive)
"fusion": {
  "decision_threshold": 0.45
}
```

**Trade-off:** False positives may rise from 8% → 12%, but recall improves 70% → 85%

### Sweep and Find Optimal
```python
# Try thresholds 0.3 to 0.8 in steps of 0.05
# Plot: precision vs. threshold, recall vs. threshold
# Find sweet spot where both criteria met
```

### Document Results
```
Threshold Tuning Results
========================
threshold=0.45: precision=0.85, recall=0.92, over_caption=15% ❌ (too many FP)
threshold=0.55: precision=0.92, recall=0.88, over_caption=8% ✅ (default optimal)
threshold=0.65: precision=0.95, recall=0.80, over_caption=5% ✅ (more conservative)

RECOMMENDATION: Keep threshold=0.55 (achieves best balance)
```

---

## STEP 4: Validate YAMNet Integration (Week 4)

### Install Dependencies
```bash
pip install tensorflow
```

### Test YAMNet Backend
```bash
python -m cc_suggester.cli \
  --input video.mp4 \
  --output output/yamnet_demo.srt \
  --config config/yamnet.json
```

### Compare Heuristic vs. YAMNet
Run same videos with both backends:
```bash
# Heuristic
python -m cc_suggester.cli --input video.mp4 --output out/heuristic.srt --config config/default.json --events-json out/heuristic_events.json

# YAMNet
python -m cc_suggester.cli --input video.mp4 --output out/yamnet.srt --config config/yamnet.json --events-json out/yamnet_events.json

# Evaluate both
python -m cc_suggester.eval --predictions out/heuristic_events.json --ground-truth truth.csv --output out/heuristic_metrics.json
python -m cc_suggester.eval --predictions out/yamnet_events.json --ground-truth truth.csv --output out/yamnet_metrics.json
```

### Report Comparison
```
Heuristic vs. YAMNet Comparison
===============================
                Heuristic   YAMNet
Precision       0.92        0.94
Recall          0.88        0.91
F1              0.90        0.93
Over-caption    8%          6%
Speed (10min)   0.5s        45s

YAMNet is more accurate (+3% F1) but much slower (90x)
Decision: Keep both, use heuristic for fast analysis, YAMNet for production
```

---

## STEP 5: Final Proposal Update (Week 4-5)

### Update README.md
```markdown
## Validation Results

The tool has been validated on 15 Hindi and Tamil videos:
- **Precision:** 92% (92% of generated captions are correct)
- **Recall:** 88% (detect 88% of non-speech events)
- **F1 Score:** 0.90
- **False Positive Rate:** 8% (well below 10% target)

Acceptance Criteria:
- ✅ Avoids over-captioning (8% false positives < 10% target)
- ✅ Detects non-speech events (88% recall > 80% target)
```

### Update CHECKLIST.md
```markdown
## COMPLETED

- [x] Ground truth collection (15 videos, 75+ events)
- [x] Evaluation on validation set (precision 92%, recall 88%)
- [x] Fusion threshold tuning (optimal threshold: 0.55)
- [x] YAMNet integration and comparison
- [x] Final metrics and compliance assessment
```

### Create VALIDATION_REPORT.md
```markdown
# Validation Report

## Dataset
- 15 Hindi and Tamil videos
- 2-10 minutes each
- 75 unique non-speech events
- 2 annotators per video (85% inter-annotator agreement)

## Results
| Metric | Result | Target | Status |
|--------|--------|--------|--------|
| Precision | 92% | N/A | ✅ |
| Recall | 88% | ≥80% | ✅ |
| F1 Score | 0.90 | N/A | ✅ |
| False Positive Rate | 8% | ≤10% | ✅ |
| False Negative Rate | 12% | N/A | ✅ |

## Per-Class Performance
| Audio Class | Events | Detected | Precision |
|-------------|--------|----------|-----------|
| Honking | 8 | 7 | 88% |
| Laughter | 12 | 11 | 92% |
| Explosion | 6 | 5 | 83% |
| Glass breaking | 5 | 5 | 100% |
| Siren | 7 | 6 | 86% |
| ... | ... | ... | ... |

## Conclusion
The tool successfully meets both acceptance criteria and is ready for deployment.
```

### Final Commit Message
```
feat: Validation on 15 regional-language videos

Results:
- Precision: 92% (meets requirement)
- Recall: 88% (meets requirement)
- False positive rate: 8% (below 10% target)
- Tested on Hindi and Tamil videos
- All acceptance criteria met

Closes #2 (CC Suggestion Tool proposal)
```

---

## WEEKLY CHECKLIST

### Week 1-2: Data Collection
- [ ] Identify and collect 10-20 videos
- [ ] Train 2 annotators using ANNOTATION_GUIDE.md
- [ ] Annotate all videos (10 min + 5 min review per video)
- [ ] Verify inter-annotator agreement >= 85%

### Week 3: Validation
- [ ] Run pipeline on all annotated videos
- [ ] Compute metrics (precision, recall, F1, over-caption rate)
- [ ] Check compliance: overcaption <= 10%? recall >= 80%?
- [ ] Generate metrics summary report

### Week 4: Tuning (If Needed)
- [ ] If metrics don't meet targets, adjust thresholds
- [ ] Re-run evaluation with new thresholds
- [ ] Document optimal thresholds
- [ ] Test YAMNet integration
- [ ] Compare heuristic vs. YAMNet performance

### Week 5: Finalization
- [ ] Update README with validation results
- [ ] Create VALIDATION_REPORT.md
- [ ] Update CHECKLIST.md with completed items
- [ ] Final review and commit

---

## CRITICAL SUCCESS FACTORS

✅ **MUST HAVE (Non-negotiable)**
1. Overcaption rate <= 10% (proposal says "avoid over-captioning")
2. Recall >= 80% (proposal says "detect non-speech events")
3. Test on actual Hindi/regional-language content (not English)
4. 2 annotators per video with >= 85% agreement
5. Document metrics in proposal

⚠️ **SHOULD HAVE (High Priority)**
1. F1 >= 0.85 (overall quality)
2. YAMNet backend working (not just heuristic)
3. Per-class performance breakdown
4. Ablation studies (heuristic vs. YAMNet vs. MediaPipe)

📝 **NICE-TO-HAVE (Lower Priority)**
1. Speed benchmarks
2. Memory usage profiles
3. Comparison to baseline methods
4. Docker packaging for easy deployment

---

## COMMON PITFALLS TO AVOID

❌ **DON'T:**
- Use English-language videos for validation (Hindi/regional required)
- Skip inter-annotator agreement (aim for >= 85%)
- Annotate only "obvious" events (include subtle ones)
- Ignore over-captioning rate (this is acceptance criterion #1)
- Change thresholds without re-evaluating

✅ **DO:**
- Follow annotation protocol exactly
- Get at least 10 videos minimum
- Document all decisions
- Report metrics transparently
- Validate before claiming accuracy

---

## SAMPLE PROJECT TIMELINE

```
Week 1:   DATA COLLECTION [████░░░░░░] Video collection + annotation setup
Week 2:   DATA ANNOTATION [██████░░░░] Annotate 10-15 videos
Week 3:   VALIDATION      [████░░░░░░] Evaluate pipeline, check metrics
Week 4:   TUNING + YAMNET [██░░░░░░░░] Threshold tuning, YAMNet integration
Week 5:   FINALIZATION    [██░░░░░░░░] Report writing, proposal submission
```

---

## RESOURCES NEEDED

- **Hardware:** Laptop with video editing software (VLC, Audacity)
- **People:** 2+ annotators (can be team members or volunteers)
- **Time:** ~40 hours for annotation (10 videos × 4 hours each)
- **Tools:** 
  - VLC Media Player (free)
  - Audacity (free, for timing)
  - Excel/Google Sheets
  - Python (already installed)

---

## SUCCESS METRIC

**The proposal is READY for submission when:**

```json
{
  "ground_truth_videos": 15,
  "precision": 0.92,              // >= 0.85
  "recall": 0.88,                 // >= 0.80
  "f1": 0.90,                     // >= 0.85
  "overcaption_rate": 0.08,       // <= 0.10 ✅
  "recall_criterion": 0.88,       // >= 0.80 ✅
  "language": "Hindi + Tamil",    // Regional ✅
  "inter_annotator_agreement": 0.85,  // >= 0.85 ✅
  "proposal_ready": true          // All criteria met
}
```

---

## FINAL NOTES

- **Start immediately:** Ground truth collection is the bottleneck
- **Document everything:** Decisions, annotations, metrics, thresholds
- **Be honest:** Report both successes and limitations
- **Be reproducible:** Include code, commands, data in proposal
- **Be confident:** Once you have ground truth validation, you can claim accuracy
