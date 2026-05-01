# Ground Truth Annotation Template for CC Suggestion Tool

This CSV template is used for evaluating and validating the CC suggestion tool against human-annotated ground truth data.

## CSV Format

```csv
start,end,label
0.5,1.2,honking
2.3,2.8,glass_breaking
5.1,6.5,laughter
8.0,9.2,siren
```

## Column Definitions

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `start` | float | Event start time in seconds | 0.5 |
| `end` | float | Event end time in seconds | 1.2 |
| `label` | string | Audio event class or description | "honking", "laughter", "door_slam" |

## Annotation Protocol

1. **Watch the video** and listen for all non-speech audio events
2. **Record precise timings:**
   - Start time: when sound begins
   - End time: when sound ends
   - Precision: ±0.1 seconds acceptable
3. **Classify the event** using consistent labels:
   - Use standardized classes: honking, explosion, laughter, applause, glass_breaking, siren, alarm, music, crowd_noise, etc.
   - Or use heuristic classes if standardized names unavailable: sharp_impact, sustained_sound, loud_sound
4. **Include all meaningful non-speech events:**
   - Include events that affect the narrative or speakers
   - Include events that speakers react to
   - Exclude: background hum, environmental noise that nobody reacts to

## Example Annotations

### Well-Annotated Video

```csv
start,end,label
0.2,0.8,door_slam
1.5,2.2,car_horn
3.1,3.4,glass_breaking
4.0,5.5,laughter
7.2,7.8,phone_ringing
```

### Quality Checks

✅ **Good**
- Timestamps are precise (within 0.1s)
- Labels are consistent and specific
- All visible events are captured
- Events are only counted if meaningful

❌ **Bad**
- Timestamps are vague ("around 2 seconds")
- Labels are inconsistent (honking vs car_horn)
- Only obvious events included; miss subtle sounds
- Include every background noise

## Using Annotations for Evaluation

The tool evaluates predictions against ground truth using:
- **IoU matching**: Time overlap threshold = 0.3 (30% overlap)
- **Metrics computed:**
  - Precision: % of predicted events that match ground truth
  - Recall: % of ground truth events that were detected
  - F1: Harmonic mean of precision + recall
  - **Overcaption rate**: FP / (TP + FP) - fraction of predictions that are wrong
  - **Undercaption rate**: FN / (TP + FN) - fraction of events that were missed

## Acceptance Criteria

After evaluation, compliance is assessed:

| Criterion | Target | Metric |
|-----------|--------|--------|
| "Avoid over-captioning" | ≤ 10% false positives | overcaption_rate |
| "Detect non-speech events" | ≥ 80% recall | recall |

## Workflow

1. **Annotate video(s)** with start, end, label
2. **Run pipeline** on same video(s)
3. **Evaluate** predictions vs. ground truth:
   ```bash
   python -m cc_suggester.eval \
     --predictions output/events.json \
     --ground-truth annotations/ground_truth.csv \
     --output output/metrics.json
   ```
4. **Review metrics** in output JSON:
   - Check overcaption_rate and recall
   - Verify compliance status
   - Adjust thresholds if needed

## Tips for High-Quality Annotations

1. **Annotate in pairs:** Two annotators per video, resolve disagreements
2. **Use precise timing tools:** Frame-by-frame playback to locate boundaries
3. **Be exhaustive:** Don't skip small or subtle sounds
4. **Standardize labels:** Create/maintain a label list for consistency
5. **Document reasoning:** Add notes for borderline cases
6. **Test inter-annotator agreement:** Ensure annotators agree 80%+ of the time

## Sample Annotation Instructions for Annotators

> **Task:** Annotate all non-speech audio events in the video
> 
> **Rules:**
> - Include events that speakers react to (head turn, pause, gesture)
> - Include events that affect understanding (honking, alarm, glass breaking)
> - Exclude: background hum, HVAC noise, video compression artifacts
> - Timing: Start at first audible sound; end when sound stops
> - Labels: Use provided taxonomy (honking, laughter, etc.)
> 
> **Quality Check:**
> - Does each annotation make sense?
> - Are timestamps consistent (±0.1s)?
> - Are all meaningful events covered?
> - Are labels specific and consistent?

## Tracking Annotation Progress

Document your annotation work:
```
Video: interview_hindi_1.mp4
Duration: 5:30
Annotator: Alice
Date: 2026-05-01
Events annotated: 7
Quality notes: Laughter duration 0.3-0.5s, hard to pin exactly
Inter-annotator agreement with Bob: 85% (6/7 matched)
```
