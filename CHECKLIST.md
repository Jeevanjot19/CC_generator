# Intelligent CC Suggestion Tool Checklist

## Done

- [x] Created a runnable Python package for the proposal demo.
- [x] Added CLI entry point for `.wav` and video inputs.
- [x] Added synthetic demo audio generator.
- [x] Added audio candidate detection stage.
- [x] Added visual reaction scoring hook for video inputs.
- [x] Added fusion decision logic.
- [x] Added SRT, SLS, and JSON output.
- [x] Added basic tests for the pipeline and failure paths.
- [x] Improved missing-input and missing-FFmpeg error messages.

## Completed In This Pass

- [x] Add external config support.
- [x] Add an HTML demo report.
- [x] Wire report generation into the CLI.
- [x] Expand tests around config/report behavior.
- [x] Install FFmpeg.
- [x] Generate a small `.mp4` fixture.
- [x] Run the full video pipeline end to end.

## Next High-Impact Steps

- [x] Add selectable audio backends.
- [x] Add optional YAMNet backend with dependency guidance.
- [x] Download and run MediaPipe YAMNet TFLite model in project-local `.venv`.
- [x] Upgrade runnable visual scoring to OpenCV.
- [x] Add optional MediaPipe backend with dependency guidance.
- [x] Download and run MediaPipe pose/face task models in project-local `.venv`.
- [x] Add evaluation metrics and benchmark command.
- [x] Add a Streamlit reviewer dashboard.
- [ ] Add real Hindi/regional-language sample videos.
- [ ] Record a short demo video for the proposal.
- [ ] Push the code to GitHub and link it in the proposal/comment.

## Optional Later Steps

- [ ] Add Docker packaging.
- [ ] Add GitHub Actions CI.
- [ ] Add editor feedback CSV export/import.

## Environment Findings

- [x] Python 3.14.2 detected.
- [x] FFmpeg installed and video path tested.
- [x] OpenCV available for visual scoring.
- [x] Streamlit available for reviewer UI.
- [ ] TensorFlow / TensorFlow Hub unavailable for YAMNet in this environment.
- [ ] MediaPipe unavailable in this environment.
