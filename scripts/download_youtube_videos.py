#!/usr/bin/env python3
"""
Download YouTube videos for ground truth annotation.

Usage:
    python scripts/download_youtube_videos.py \
        --urls "https://youtube.com/watch?v=..." "https://..." \
        --output-dir videos/ \
        --format wav \
        --language hindi

Requirements:
    pip install yt-dlp
"""

import argparse
import subprocess
import sys
from pathlib import Path


def check_dependencies():
    """Check if yt-dlp is installed."""
    try:
        import yt_dlp  # noqa: F401
        return True
    except ImportError:
        print("❌ yt-dlp not found. Install with: pip install yt-dlp")
        return False


def download_video(url: str, output_dir: Path, format: str = "mp4") -> bool:
    """
    Download video from YouTube.

    Args:
        url: YouTube URL
        output_dir: Directory to save video
        format: 'mp4' for video, 'wav' for audio only

    Returns:
        True if successful, False otherwise
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        if format == "wav":
            # Extract audio to WAV
            cmd = [
                "yt-dlp",
                "-f", "bestaudio",
                "-x",
                "--audio-format", "wav",
                "--audio-quality", "192",
                "-o", str(output_dir / "%(title)s.%(ext)s"),
                url,
            ]
        else:
            # Download best video
            cmd = [
                "yt-dlp",
                "-f", "best",
                "-o", str(output_dir / "%(title)s.%(ext)s"),
                url,
            ]

        print(f"⬇️  Downloading: {url}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ Downloaded successfully to {output_dir}/")
        print(result.stdout)
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Download failed: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ yt-dlp command not found. Install with: pip install yt-dlp")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Download YouTube videos for CC suggestion ground truth annotation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download single video as WAV
  python scripts/download_youtube_videos.py \\
    --urls "https://youtube.com/watch?v=dQw4w9WgXcQ" \\
    --format wav \\
    --output-dir videos/

  # Download multiple videos
  python scripts/download_youtube_videos.py \\
    --urls "URL1" "URL2" "URL3" \\
    --format wav \\
    --output-dir videos/

  # Download as MP4
  python scripts/download_youtube_videos.py \\
    --urls "https://youtube.com/watch?v=..." \\
    --format mp4 \\
    --output-dir videos/
        """,
    )

    parser.add_argument(
        "--urls",
        nargs="+",
        required=True,
        help="YouTube URLs to download (space-separated)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("videos"),
        help="Directory to save videos (default: videos/)",
    )
    parser.add_argument(
        "--format",
        choices=["mp4", "wav"],
        default="wav",
        help="Download format: mp4 (video) or wav (audio only). Default: wav",
    )
    parser.add_argument(
        "--language",
        default="hindi",
        help="Language of videos (for naming/documentation)",
    )

    args = parser.parse_args()

    # Check dependencies
    if not check_dependencies():
        return 1

    # Download each video
    print(f"\n📥 Downloading {len(args.urls)} video(s) as {args.format.upper()}...")
    print(f"📁 Output directory: {args.output_dir.absolute()}\n")

    success_count = 0
    for i, url in enumerate(args.urls, 1):
        print(f"\n[{i}/{len(args.urls)}]", end=" ")
        if download_video(url, args.output_dir, args.format):
            success_count += 1
        else:
            print(f"⚠️  Failed to download: {url}")

    # Summary
    print(f"\n{'='*60}")
    print(f"Download complete: {success_count}/{len(args.urls)} succeeded")
    print(f"Videos saved to: {args.output_dir.absolute()}\n")

    if success_count == len(args.urls):
        print("✅ All videos downloaded successfully!")
        print(f"📝 Next steps:")
        print(f"   1. Watch videos and take notes on sound events")
        print(f"   2. Create ground truth CSV files in annotations/")
        print(f"   3. Run: python -m cc_suggester.eval --predictions ... --ground-truth ...")
        return 0
    else:
        print("⚠️  Some downloads failed. Check URLs and try again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
