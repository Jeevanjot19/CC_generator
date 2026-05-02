# 4 Critical Fixes Required Before PR Submission

## Status: All Issues Verified on Real YouTube Video

---

## 🔴 ISSUE 1: YAMNet Timestamp Bug (CRITICAL)

**Location:** `cc_suggester/audio.py` line 254-258

**Current Code:**
```python
for chunk_idx, result in enumerate(results):
    # Manually compute timestamp using chunk index and hop size
    # This is more reliable than result.timestamp_ms for AUDIO_CLIPS mode
    timestamp = max(0.0, chunk_idx * config.hop_seconds)
```

**Problem:**
- `enumerate(results)` only iterates detected results (20 items for JUMPER video)
- `chunk_idx` goes 0→19, capping timestamp at ~22 seconds
- Actual video is 180 seconds, but events only detected in first 22 seconds
- Audio data after 22s is never processed

**Root Cause:**
- MediaPipe AUDIO_CLIPS mode returns sparse results (only detected events)
- enumerate() treats result array index as chunk index (wrong!)

**Fix:**
```python
for result in results:
    # Use MediaPipe's timestamp_ms (in milliseconds)
    timestamp = max(0.0, result.timestamp_ms / 1000.0)
```

**Impact on Results:**
- Heuristic: Unaffected (uses different approach)
- YAMNet: Will detect events across full video instead of just first 22s
- Estimated: 20 → 40-60 candidates (if audio events distributed throughout)

---

## 🔴 ISSUE 2: Reaction Score Saturation at 1.0 (HIGH)

**Location:** `cc_suggester/visual.py` line 74

**Current Code:**
```python
diffs = _frame_diffs(frames)
peak = max(diffs, default=0.0)
score = min(1.0, peak / config.reaction_threshold)  # ← CEILING
event.reaction_score = round(score, 3)
```

**Problem:**
- If `peak >= reaction_threshold (0.35)`, then `score = 1.0` (capped)
- Any frame difference ≥35% results in score=1.0
- Hard scene cuts (common in thriller films) instantly hit ceiling
- YAMNet results show 2 consecutive events with exactly 1.0 reaction
- This is actually accepting false positives (scene cuts, not actual reactions)

**Example from JUMPER video:**
- Event 0:05.75 - Arrow: reaction_score = 1.0 (scene cut, not real motion)
- Event 0:07.75 - Vehicle: reaction_score = 1.0 (scene cut, not real motion)

**Fix:**
Use sigmoid normalization instead of ceiling:
```python
import math
raw_score = peak / config.reaction_threshold
# Sigmoid: smooth saturation instead of hard ceiling
score = 2 / (1 + math.exp(-raw_score)) - 1  # Range [0, 1]
event.reaction_score = round(score, 3)
```

Or simpler: divide by 2× threshold instead of 1×:
```python
score = min(1.0, peak / (config.reaction_threshold * 2))
```

**Alternative - Add Scene Cut Detector:**
```python
# Detect hard cuts (very high frame difference in one frame)
# vs gradual motion (high average difference)
avg_diff = sum(diffs) / len(diffs)
max_diff = max(diffs)
if max_diff > avg_diff * 3:  # Likely a hard cut
    event.reaction_type = "scene_cut"
    event.reaction_score = 0.1  # Suppress
```

---

## 🔴 ISSUE 3: Long Captions Not Auto-Split (MEDIUM)

**Location:** `cc_suggester/pipeline.py` or new `post_process.py`

**Problem:**
- Last heuristic caption: 174.2-180.9s (6.6 seconds)
- Professional subtitle editors limit captions to 2-3 seconds max
- Viewers can't read 6+ second captions effectively
- JUMPER case: 95% audio confidence + audio override forces 6.6s caption

**Current Result:**
```
4
00:02:54,250 --> 00:03:00,875
[Sustained sound]
```

**Fix - Add Caption Duration Limiter:**
```python
MAX_CAPTION_DURATION = 3.0

def split_long_events(events: list[Event]) -> list[Event]:
    """Split events longer than max_caption_duration."""
    result = []
    for event in events:
        duration = event.t_end - event.t_start
        if duration <= MAX_CAPTION_DURATION:
            result.append(event)
        else:
            # Split into multiple captions
            num_parts = math.ceil(duration / MAX_CAPTION_DURATION)
            part_duration = duration / num_parts
            for i in range(num_parts):
                t_start = event.t_start + i * part_duration
                t_end = min(event.t_end, t_start + part_duration)
                part = copy(event)
                part.t_start = t_start
                part.t_end = t_end
                result.append(part)
    return result
```

**Call in Pipeline:**
```python
# In pipeline.py, after fusion logic:
events = split_long_events(events)  # Split captions >3s
```

**Result After Fix:**
```
4a
00:02:54,250 --> 00:02:57,250
[Sustained sound]

4b
00:02:57,250 --> 00:03:00,875
[Sustained sound]
```

---

## 🔴 ISSUE 4: YAMNet Label Taxonomy Incomplete (MEDIUM)

**Location:** `cc_suggester/config.py` lines 99-125

**Problem:**
- 14 YAMNet classes detected but missing from `label_taxonomy`
- Missing: Arrow, Animal, Horse, Door, Engine, Fireworks, Pigeon, Rail transport, Scary music, Sliding door, Train, Typing, Vehicle, Ambient music
- All fall through to generic `[Sound effect]` fallback
- Users get no rich information from ML model

**Current Taxonomy (partial):**
```python
"Honking": "[honking]",
"Gunshot": "[gunshot]",
"Explosion": "[explosion]",
# ... but no Arrow, Vehicle, Animal, etc.
```

**Fix - Expand Label Taxonomy:**
```python
label_taxonomy: dict[str, str] = field(
    default_factory=lambda: {
        # ... existing labels ...
        
        # Add missing YAMNet classes
        "Arrow": "[arrow sound]",
        "Animal": "[animal sound]",
        "Horse": "[horse]",
        "Door": "[door]",
        "Engine": "[engine]",
        "Fireworks": "[fireworks]",
        "Pigeon, dove": "[bird]",
        "Rail transport": "[train]",
        "Scary music": "[scary music]",
        "Sliding door": "[sliding door]",
        "Train": "[train]",
        "Typing": "[typing]",
        "Vehicle": "[vehicle]",
        "Ambient music": "[ambient music]",
    }
)
```

**Result After Fix:**
```json
// Before:
"audio_class": "Arrow",
"cc_label": "[Sound effect]"

// After:
"audio_class": "Arrow",
"cc_label": "[arrow sound]"
```

---

## Priority & Implementation Order

### 🚨 CRITICAL (Blocks PR)
**Issue 1: YAMNet Timestamp Bug**
- Without fix: YAMNet produces incomplete results (events only in first 22s)
- Time to fix: 5 minutes
- Risk: Low (simple code change)
- Validation: Re-run YAMNet on JUMPER video, verify events span full duration

### 🔴 HIGH (Should Fix Before PR)
**Issue 2: Reaction Score Saturation**
- Without fix: YAMNet results have false positives (scene cuts accepted)
- Time to fix: 10 minutes
- Risk: Medium (changes visual scoring behavior)
- Validation: Re-run heuristic + YAMNet on JUMPER video, verify reaction_score < 1.0

### 🟡 MEDIUM (Nice to Have)
**Issue 3: Long Caption Duration**
- Without fix: 6.6-second captions (professional standard is 2-3s)
- Time to fix: 15 minutes
- Risk: Low (post-processing step)
- Validation: Re-run on JUMPER video, check SRT durations ≤ 3s

**Issue 4: Label Taxonomy**
- Without fix: YAMNet outputs generic `[Sound effect]` instead of rich labels
- Time to fix: 5 minutes
- Risk: Very Low (just config data)
- Validation: Re-run YAMNet, check SRT labels contain Arrow, Vehicle, etc.

---

## Validation Plan

After each fix, re-run pipeline:
```bash
# Heuristic (should be unaffected)
python -m cc_suggester.cli \
  --input "videos/JUMPER - Suspense Thriller Short Film.mp4" \
  --output jumper_heuristic_fixed.srt \
  --events-json jumper_heuristic_fixed_events.json \
  --config config/default.json

# YAMNet (should show events across full duration)
python -m cc_suggester.cli \
  --input "videos/JUMPER - Suspense Thriller Short Film.mp4" \
  --output jumper_yamnet_fixed.srt \
  --events-json jumper_yamnet_fixed_events.json \
  --config config/yamnet.json
```

**Success Criteria:**
- [ ] Timestamp Bug: YAMNet events distributed across full 180s video
- [ ] Reaction Score: No reaction_score = 1.0 (max should be ~0.95)
- [ ] Caption Duration: All accepted captions ≤ 3 seconds
- [ ] Labels: YAMNet captions show `[arrow sound]`, `[vehicle]`, etc., not generic `[Sound effect]`

---

## Next Steps

**Immediate (Before PR):**
1. Fix Issue 1 (YAMNet Timestamps) - 5 min
2. Fix Issue 2 (Reaction Saturation) - 10 min
3. Fix Issue 3 (Caption Duration) - 15 min
4. Fix Issue 4 (Label Taxonomy) - 5 min
5. Re-validate on JUMPER video - 5 min
6. Commit + Push - 2 min

**Total Time: ~42 minutes**

**Alternative (Minimal PR):**
- Fix Issue 1 + Issue 4 only (~10 min)
- Note Issues 2 & 3 as "Future Work" in PR description
- Both are non-blocking and don't affect core functionality

**Recommendation:**
Do all 4 fixes before PR. Once you fix Issue 1, you'll see YAMNet detecting 40+ events across the full video, which will immediately demonstrate why Issues 2 & 3 matter.
