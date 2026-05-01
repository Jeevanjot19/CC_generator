#!/usr/bin/env python3
"""
Video Preprocessing & Validation Utility
Handles video format conversion, validation, and preparation for pipeline.
"""

import subprocess
import json
import os
from pathlib import Path
from typing import Optional, NamedTuple


class VideoInfo(NamedTuple):
    """Video metadata."""
    width: int
    height: int
    duration: float
    fps: float
    codec: str
    file_size_mb: float
    valid: bool = True


def setup_ffmpeg_path():
    """Add FFmpeg to PATH if it's in a standard location."""
    ffmpeg_paths = [
        Path(os.path.expandvars(r"%LOCALAPPDATA%\Programs\FFmpeg\bin")),
        Path(r"C:\Program Files\FFmpeg\bin"),
        Path(r"C:\FFmpeg\bin"),
    ]
    
    for ffmpeg_path in ffmpeg_paths:
        if ffmpeg_path.exists():
            os.environ['PATH'] = str(ffmpeg_path) + os.pathsep + os.environ['PATH']
            return True
    return False


def check_ffmpeg() -> bool:
    """Check if FFmpeg is installed."""
    setup_ffmpeg_path()
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_video_info(video_path: str | Path) -> Optional[VideoInfo]:
    """Extract video metadata using ffmpeg/ffprobe."""
    setup_ffmpeg_path()
    video_path = Path(video_path)
    
    if not video_path.exists():
        print(f"❌ File not found: {video_path}")
        return None
    
    try:
        # Get detailed info using ffmpeg
        result = subprocess.run(
            ["ffmpeg", "-i", str(video_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        output_text = result.stderr
        
        # Extract duration: Duration: 00:00:30.00
        duration = 0.0
        for line in output_text.split("\n"):
            if "Duration:" in line:
                time_part = line.split("Duration:")[1].split(",")[0].strip()
                parts = time_part.split(":")
                if len(parts) == 3:
                    h, m, s = parts
                    duration = int(h) * 3600 + int(m) * 60 + float(s)
                break
        
        # Get video stream info
        width, height, fps, codec = 0, 0, 30.0, "unknown"
        
        if "Video:" in output_text:
            for line in output_text.split("\n"):
                if "Video:" in line:
                    import re
                    # Parse resolution: 640x480 (not 0x1 which is hex)
                    # Look for numbers that are at least 2 digits
                    res_match = re.search(r"(\d{2,})x(\d{2,})", line)
                    if res_match:
                        width = int(res_match.group(1))
                        height = int(res_match.group(2))
                    
                    # Parse codec: mpeg4, h264, etc
                    codec_match = re.search(r"Video:\s+(\w+)", line)
                    if codec_match:
                        codec = codec_match.group(1)
                    
                    # Parse FPS: "24 fps", "30000/1001 fps"
                    fps_match = re.search(r"(\d+\.?\d*)\s*fps", line)
                    if fps_match:
                        fps = float(fps_match.group(1))
                    else:
                        # Try fractional format
                        fps_frac = re.search(r"(\d+)/(\d+)\s*fps", line)
                        if fps_frac:
                            fps = float(fps_frac.group(1)) / float(fps_frac.group(2))
                    break
        
        file_size_mb = video_path.stat().st_size / (1024 * 1024)
        
        return VideoInfo(
            width=width,
            height=height,
            duration=duration,
            fps=fps,
            codec=codec,
            file_size_mb=file_size_mb
        )
    except Exception as e:
        print(f"❌ Error getting video info: {e}")
        return None


def extract_audio(video_path: str | Path, output_path: str | Path) -> bool:
    """Extract audio from video file."""
    setup_ffmpeg_path()
    video_path = Path(video_path)
    output_path = Path(output_path)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-q:a", "9",
            "-n",  # Don't overwrite
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"❌ FFmpeg error: {result.stderr[:500]}")
            return False
        
        print(f"✅ Extracted audio: {output_path}")
        return output_path.exists()
    
    except subprocess.TimeoutExpired:
        print(f"❌ Audio extraction timed out")
        return False
    except Exception as e:
        print(f"❌ Error extracting audio: {e}")
        return False


def convert_video(
    video_path: str | Path,
    output_path: str | Path,
    format: str = "mp4",
    quality: str = "medium"
) -> bool:
    """Convert video to standard format."""
    setup_ffmpeg_path()
    video_path = Path(video_path)
    output_path = Path(output_path)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    quality_map = {
        "low": ("h264", "18"),
        "medium": ("h264", "23"),
        "high": ("h264", "20"),
    }
    
    codec, crf = quality_map.get(quality, quality_map["medium"])
    
    try:
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-c:v", codec,
            "-crf", crf,
            "-c:a", "aac",
            "-b:a", "128k",
            "-n",  # Don't overwrite
            str(output_path)
        ]
        
        print(f"⏳ Converting: {video_path.name}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode != 0:
            print(f"❌ Conversion failed: {result.stderr[:500]}")
            return False
        
        print(f"✅ Converted: {output_path}")
        return True
    
    except subprocess.TimeoutExpired:
        print(f"❌ Conversion timed out")
        return False
    except Exception as e:
        print(f"❌ Error converting video: {e}")
        return False


def validate_video(video_path: str | Path) -> bool:
    """Validate video file integrity."""
    video_path = Path(video_path)
    
    if not video_path.exists():
        print(f"❌ File not found: {video_path}")
        return False
    
    info = get_video_info(video_path)
    
    if not info:
        print(f"❌ Invalid video file")
        return False
    
    print(f"✅ Video validation:")
    print(f"   Resolution: {info.width}x{info.height}")
    print(f"   Duration: {info.duration:.1f}s")
    print(f"   FPS: {info.fps:.1f}")
    print(f"   Codec: {info.codec}")
    print(f"   Size: {info.file_size_mb:.1f} MB")
    
    # Validation checks
    if info.duration < 1:
        print(f"⚠️  Warning: Video too short ({info.duration}s)")
        return False
    
    if info.width < 320 or info.height < 240:
        print(f"⚠️  Warning: Video resolution too low ({info.width}x{info.height})")
    
    return True


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python video_utils.py <video_file> [--extract-audio <output>]")
        sys.exit(1)
    
    video_file = sys.argv[1]
    
    # Check FFmpeg
    if not check_ffmpeg():
        print("⚠️  FFmpeg not found. Install with: choco install ffmpeg (Windows) or brew install ffmpeg (Mac)")
    
    # Validate video
    if validate_video(video_file):
        if "--extract-audio" in sys.argv:
            output_idx = sys.argv.index("--extract-audio") + 1
            if output_idx < len(sys.argv):
                extract_audio(video_file, sys.argv[output_idx])
