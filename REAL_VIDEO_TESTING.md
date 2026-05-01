# 🎬 Real Video Testing Guide

## Quick Start (5 minutes)

### Step 1: Check Dependencies
```powershell
python scripts/test_real_videos.py
```
This will verify FFmpeg is installed and set up directories.

### Step 2: Download Videos
Get 3-5 test videos (2-5 minutes each, with sound effects):
```powershell
python scripts/download_youtube_videos.py `
  --urls "https://www.youtube.com/watch?v=..." `
           "https://www.youtube.com/watch?v=..." `
  --format mp4 `
  --output-dir videos/
```

**Good test videos:**
- Action scenes (explosions, gunshots)
- Comedy clips (laughter, applause)
- News segments (alerts, tone changes)
- Interviews (natural reactions)

### Step 3: Run Full Workflow
```powershell
python scripts/test_real_videos.py
```

This automatically:
1. ✅ Validates all videos
2. ✅ Extracts audio
3. ✅ Runs CC detection pipeline
4. ✅ Creates annotation templates
5. ✅ Generates reports

---

## Manual Testing (If Preferred)

### 1. Validate Video
```powershell
python scripts/video_utils.py videos/my_video.mp4
```

Output shows:
- ✅ Resolution, duration, FPS, codec
- ✅ File size
- ✅ Validity check

### 2. Extract Audio
```powershell
python scripts/video_utils.py videos/my_video.mp4 --extract-audio audio/my_video.wav
```

Creates: `audio/my_video.wav`

### 3. Run Pipeline
```powershell
python -m cc_suggester.cli `
  --input audio/my_video.wav `
  --output results/my_video.srt `
  --events-json results/my_video_events.json `
  --report-html results/my_video_report.html
```

Generates:
- `results/my_video.srt` — Caption file
- `results/my_video_events.json` — Event details
- `results/my_video_report.html` — Visual report

### 4. Annotate Ground Truth

#### Method A: Interactive Mode (Guided)
```powershell
python scripts/annotation_tool.py videos/my_video.mp4 --interactive
```

Follow the prompts:
1. Open video in media player (VLC recommended)
2. For each sound event, enter start/end timestamps
3. Enter event label (honking, laughter, explosion, etc.)
4. Tool saves to `ground_truth/my_video_ground_truth.csv`

#### Method B: Manual CSV Editing
1. Template created automatically: `ground_truth/my_video_annotations.csv`
2. Watch video, note timestamps
3. Edit CSV with:
   ```csv
   start,end,label
   2.5,3.2,honking
   5.1,6.8,laughter
   ```
4. Convert to evaluation format:
   ```powershell
   python scripts/annotation_tool.py ground_truth/my_video_annotations.csv --convert
   ```

### 5. Evaluate Performance
```powershell
python -m cc_suggester.eval `
  --predictions results/my_video_events.json `
  --ground-truth ground_truth/my_video_ground_truth.csv `
  --output results/my_video_metrics.json
```

Shows metrics:
```
Precision:  85.2%   (TP / (TP + FP))
Recall:     90.5%   (TP / (TP + FN))
F1 Score:   0.877   (Harmonic mean)
Overcaption: 5.3%   (FP rate - should be <10%)
Compliance: PASS ✅  (meets targets)
```

### 6. Review in Dashboard
```powershell
streamlit run streamlit_app.py
```

Enter: `results/my_video_events.json`

See:
- 📊 Events table with all scores
- 📈 Confidence distributions
- ✅ Accept/reject decisions
- 👁️ SRT preview

---

## Timestamp Tips

**Using VLC Media Player (Recommended):**
1. Open video
2. Press `V` to show control panel
3. Hover over timeline to see timestamp
4. Use arrow keys for frame-by-frame
5. Check timestamp when sound starts/ends

**Format Options:**
```
MM:SS         → 2:30 (2 min 30 sec)
MM:SS.mmm     → 2:30.500 (2 min 30.5 sec)
HH:MM:SS      → 0:02:30 (2 min 30 sec)
HH:MM:SS.mmm  → 0:02:30.500 (2 min 30.5 sec)
```

**Tips:**
- Note when sound **starts**, not when reaction happens
- Note when sound **ends**, not when silence starts
- Mark pauses after laughter/applause
- Group overlapping sounds as single event

---

## Batch Processing Multiple Videos

Process 5+ videos automatically:

```powershell
# Download all videos first
python scripts/download_youtube_videos.py --urls URL1 URL2 URL3 URL4 URL5 --output-dir videos/

# Run full workflow on all
python scripts/test_real_videos.py

# This will:
# 1. Validate each video
# 2. Extract audio from each
# 3. Run pipeline on each
# 4. Create annotation templates
# 5. Generate individual reports
```

Then annotate each one:
```powershell
python scripts/annotation_tool.py videos/video1.mp4 --interactive
python scripts/annotation_tool.py videos/video2.mp4 --interactive
# ... repeat for each video
```

Then evaluate all:
```powershell
foreach ($name in @("video1", "video2", "video3")) {
    python -m cc_suggester.eval `
      --predictions "results/${name}_events.json" `
      --ground-truth "ground_truth/${name}_ground_truth.csv" `
      --output "results/${name}_metrics.json"
}
```

---

## File Structure After Testing

```
d:\subtitle/
├── videos/                          # Downloaded videos
│   ├── my_video.mp4
│   ├── test_video.mp4
│   └── ...
│
├── audio/                           # Extracted audio
│   ├── my_video.wav
│   ├── test_video.wav
│   └── ...
│
├── results/                         # Pipeline outputs
│   ├── my_video.srt
│   ├── my_video_events.json
│   ├── my_video_report.html
│   ├── my_video_metrics.json
│   └── ...
│
├── ground_truth/                    # Annotations
│   ├── my_video_annotations.csv     # Raw annotations
│   ├── my_video_ground_truth.csv    # For evaluation
│   └── ...
│
└── scripts/
    ├── test_real_videos.py          # Main workflow
    ├── video_utils.py               # Video handling
    ├── annotation_tool.py           # Annotation helper
    └── ...
```

---

## Troubleshooting

### "FFmpeg is required but not found"
```powershell
# Windows
choco install ffmpeg

# Mac
brew install ffmpeg

# Linux
apt-get install ffmpeg
```

### Video validation fails
- Check file is not corrupted: `python scripts/video_utils.py video.mp4`
- Try converting: `python scripts/video_utils.py video.mp4 --convert video_converted.mp4`
- Or extract just audio: `python scripts/video_utils.py video.mp4 --extract-audio audio.wav`

### Low precision/recall scores
**Check:**
- ✓ Ground truth timestamps are accurate (watch video carefully)
- ✓ Event labels match detected events
- ✓ No missed events in annotations
- ✓ No extra events in annotations

**Adjust:**
- Edit config/default.json:
  - Lower `fusion_threshold` to be more sensitive (0.55 → 0.45)
  - Increase `audio_confidence_threshold` for stricter audio (0.5 → 0.6)

**Re-evaluate:**
```powershell
python -m cc_suggester.eval --predictions events.json --ground-truth truth.csv --output metrics.json
```

### Too many false positives
- Increase fusion threshold (0.55 → 0.70)
- Increase audio confidence requirement
- Check if background noise is being detected
- Improve ground truth (make sure all events are marked)

### Slow processing
- Long videos: Extract shorter clips first
- Videos >10 min: Process in chunks manually
- Check resource usage: Use Task Manager
- Try: `config/no-visual-config.json` (audio-only, faster)

---

## Quality Targets

After testing 5+ videos, aim for:
- **Precision:** ≥75% (avoid false positives)
- **Recall:** ≥80% (catch most real events)
- **F1 Score:** >0.70 (balanced performance)
- **Overcaption Rate:** <10% (compliance target)

If below targets:
1. Review ground truth accuracy
2. Adjust config thresholds
3. Analyze failure cases
4. Retrain heuristic constants if needed

---

## Example: Complete Workflow

```powershell
# 1. Download test videos
python scripts/download_youtube_videos.py `
  --urls "https://www.youtube.com/watch?v=YlJzkKzrH7E" `
           "https://www.youtube.com/watch?v=kJQDAdC5cS8" `
  --format mp4 `
  --output-dir videos/

# 2. Run full workflow (automatic)
python scripts/test_real_videos.py

# 3. Annotate videos one by one
python scripts/annotation_tool.py videos/video1.mp4 --interactive
python scripts/annotation_tool.py videos/video2.mp4 --interactive

# 4. Evaluate all
python -m cc_suggester.eval --predictions results/video1_events.json --ground-truth ground_truth/video1_ground_truth.csv --output results/video1_metrics.json
python -m cc_suggester.eval --predictions results/video2_events.json --ground-truth ground_truth/video2_ground_truth.csv --output results/video2_metrics.json

# 5. Check results
cat results/video1_metrics.json
cat results/video2_metrics.json

# 6. Review in dashboard
streamlit run streamlit_app.py
# Input: results/video1_events.json (etc.)
```

---

## Next Steps After Testing

✅ **If metrics meet targets (precision ≥75%, recall ≥80%):**
- Expand to 10-20 videos
- Test with regional languages (Hindi, Tamil, Bengali)
- Get inter-rater agreement (2 annotators per video)
- Prepare proposal with real metrics

❌ **If metrics below targets:**
- Review and improve ground truth annotations
- Adjust config thresholds
- Analyze false positives/negatives
- Consider collecting more training data

📝 **For Production Deployment:**
- Set confidence thresholds based on validation results
- Document all config parameters used
- Create deployment package with models
- Test on target video platform/format

---

**Ready to test? Start with:** `python scripts/test_real_videos.py`
