# Intelligent CC Suggestion Tool - Production Ready Implementation

**Project Status:** Priority 1 & Priority 2 COMPLETE ✅  
**Current Phase:** Ready for ground truth validation  
**Timeline to Proposal:** 2-3 weeks with real metrics

## 🎯 Project Overview

This is an **Intelligent Closed Captions (CC) Suggestion Tool** that automatically detects non-speech audio events and generates captions for them. The tool:

1. **Detects** candidate non-speech audio events (using heuristic or YAMNet)
2. **Inspects** the matching visual window for speaker reactions (optional)
3. **Fuses** both signals to avoid over-captioning
4. **Exports** accepted suggestions as SRT or SLS captions

**Key Metrics:**
- Measurable accuracy: overcaption_rate, recall, F1
- Automatic compliance checking
- Professional HTML reports with metrics
- Production-ready logging and error handling

## 🚀 Quick Start

### Try the Demo:
```powershell
# Generate sample audio
python -m cc_suggester.demo_data --output samples\demo.wav

# Run pipeline with metrics display
python -m cc_suggester.cli \
  --input samples\demo.wav \
  --output out\demo.srt \
  --events-json out\events.json \
  --report-html out\report.html

# Open HTML report in browser to see metrics
start out\report.html
```

### Validate on Ground Truth:
```powershell
# Download videos
python scripts/download_youtube_videos.py \
  --urls "https://youtube.com/watch?v=..." \
  --format wav

# Annotate with ground truth (follow ANNOTATION_GUIDE.md)

# Evaluate predictions
python -m cc_suggester.eval \
  --predictions out\events.json \
  --ground-truth annotations\truth.csv \
  --output out\metrics.json
```

## 📁 Documentation

| Purpose | File |
|---------|------|
| This overview | **README.md** |
| Setup & quick start | **README.md** (below) |
| Project checklist | CHECKLIST.md |
| Create ground truth | ANNOTATION_GUIDE.md |
| Find & download videos | VIDEO_COLLECTION_GUIDE.md |
| Implementation details | PRIORITY_1_COMPLETE.md, PRIORITY_2_COMPLETE.md |
| Roadmap & timeline | NEXT_STEPS.md |

---

# Intelligent CC Suggestion Tool - Demo Pipeline

This repository is a working proof-of-concept for the PlanetRead C4GT DMP 2026 proposal.
It demonstrates the central idea behind the project:

1. detect candidate non-speech audio events,
2. inspect the matching visual window for scene reaction,
3. fuse both scores to avoid over-captioning,
4. export accepted suggestions as SRT or SLS.

The demo intentionally uses lightweight, inspectable heuristics so it can run before
large ML dependencies are installed. The module boundaries are designed so YAMNet,
PANNs, and MediaPipe can replace the heuristic stages later.

## Quick Start

```powershell
python -m cc_suggester.demo_data --output samples\demo.wav
python -m cc_suggester.cli --input samples\demo.wav --output out\demo.srt --events-json out\events.json --report-html out\report.html
```

For video input such as `.mp4`, install FFmpeg and make sure `ffmpeg` is on `PATH`:

```powershell
python -m cc_suggester.cli --input path\to\video.mp4 --output out\captions.srt --format srt
```

If FFmpeg was installed with winget and the current shell has not picked up the
new `PATH` yet, restart PowerShell. In the current development session, the
full video path was tested with:

```powershell
python -m cc_suggester.cli --input samples\demo_video.mp4 --output out\video_demo.srt --format srt --events-json out\video_events.json --report-html out\video_report.html --config config\default.json
```

## What This Proves

- The pipeline is end-to-end and produces editor-reviewable caption files.
- Audio events are first-class structured objects with timestamps and confidence.
- The visual module is constrained to audio-event windows, matching the proposal.
- The decision engine is configurable and conservative by default.
- The current implementation can be demoed without downloading model weights.

## Current Demo Limitations

- Audio detection is energy/transient based, not YAMNet yet.
- Visual reaction scoring uses low-resolution frame difference via FFmpeg, not MediaPipe yet.
- Without FFmpeg, video files cannot be decoded; `.wav` demo input still works.

## Repository Layout

```text
cc_suggester/
  audio.py          # WAV/video audio loading and candidate event detection
  cli.py            # command-line entry point
  config.py         # default thresholds and label taxonomy
  demo_data.py      # creates a tiny synthetic WAV fixture
  event.py          # shared Event dataclass
  output.py         # SRT, SLS, and JSON writers
  pipeline.py       # orchestration
  visual.py         # reaction scoring around candidate event windows
tests/
  test_pipeline.py
```

## Suggested Demo Script

1. Run the demo WAV command above.
2. Show `out/events.json` to prove the tool tracks audio score, reaction score,
   fusion score, and decision.
3. Open `out/report.html` to show a reviewer-friendly event table.
4. Show `out/demo.srt` as the final editor-facing artifact.
5. Explain that the next PR swaps `audio.py` with YAMNet and `visual.py` with MediaPipe
   while preserving the pipeline contract.

## Reviewer Dashboard

The lightweight HTML report is the easiest artifact to share. For a live reviewer UI,
run the Streamlit dashboard:

```powershell
streamlit run streamlit_app.py
```

Use `out/video_events.json` or `out/events.json` as the events file.

## Evaluation

Compare predictions against a simple ground-truth CSV:

```powershell
python -m cc_suggester.eval --predictions out\video_events.json --ground-truth samples\demo_ground_truth.csv --output out\metrics.json
```

## Actual ML Backends

The default config stays lightweight:

```powershell
python -m cc_suggester.cli --input samples\demo_video.mp4 --output out\video_demo.srt --events-json out\video_events.json --report-html out\video_report.html --config config\default.json
```

The project-local `.venv` includes MediaPipe and can run the actual TFLite
backends:

```powershell
.\.venv\Scripts\python.exe -m cc_suggester.cli --input samples\demo.wav --output out\yamnet_demo.srt --events-json out\yamnet_events.json --report-html out\yamnet_report.html --config config\yamnet.json
```

For full YAMNet audio classification plus MediaPipe pose/face landmark scoring:

```powershell
.\.venv\Scripts\python.exe -m cc_suggester.cli --input samples\demo_video.mp4 --output out\full_ml_demo.srt --events-json out\full_ml_events.json --report-html out\full_ml_report.html --config config\full_ml.json
```

The required model assets live in `models/`:

- `yamnet.tflite`
- `pose_landmarker_lite.task`
- `face_landmarker.task`

The generated sample video is a test pattern, so MediaPipe does not find people
or faces in it. On real videos with visible speakers, `reaction_score` is
computed from pose and face landmark movement.
