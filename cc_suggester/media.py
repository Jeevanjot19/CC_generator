from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm"}
WAV_EXTENSIONS = {".wav"}


class MediaDependencyError(RuntimeError):
    pass


def ffmpeg_path() -> str | None:
    return shutil.which("ffmpeg")


def require_ffmpeg() -> str:
    executable = ffmpeg_path()
    if not executable:
        raise MediaDependencyError(
            "FFmpeg is required for video input but was not found on PATH. "
            "Install FFmpeg, or run the demo with a .wav input."
        )
    return executable


def extract_wav(video_path: Path, wav_path: Path, sample_rate: int) -> None:
    ffmpeg = require_ffmpeg()
    command = [
        ffmpeg,
        "-y",
        "-i",
        str(video_path),
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-f",
        "wav",
        str(wav_path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "FFmpeg audio extraction failed.")
