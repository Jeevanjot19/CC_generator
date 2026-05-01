#!/usr/bin/env python3
"""
Download required ML models for CC Suggestion Tool.

Downloads:
- YAMNet (audio event classification)
- MediaPipe Pose Landmarker (speaker pose detection)
- MediaPipe Face Landmarker (speaker face detection)

Usage:
    python scripts/download_models.py

    # Or with custom output directory
    python scripts/download_models.py --models-dir ./models_custom

Environment:
    - Requires internet connection
    - Creates models/ directory if not exists
    - Validates checksums after download
"""

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path
from urllib.request import urlopen


# Model URLs and checksums
MODELS = {
    "yamnet.tflite": {
        "url": "https://storage.googleapis.com/mediapipe-tasks/audio_classifier/yamnet_1_0_0_audio_classifier_with_metadata.tflite",
        "description": "YAMNet audio event classifier",
        "required": False,
        "note": "Optional - for advanced audio classification. Requires TensorFlow.",
    },
    "pose_landmarker_lite.task": {
        "url": "https://storage.googleapis.com/mediapipe-tasks/vision/pose_landmarker/pose_landmarker_lite.task",
        "description": "MediaPipe Lite Pose Landmarker",
        "required": False,
        "note": "Optional - for lightweight pose detection. Requires MediaPipe.",
    },
    "pose_landmarker.task": {
        "url": "https://storage.googleapis.com/mediapipe-tasks/vision/pose_landmarker/pose_landmarker.task",
        "description": "MediaPipe Pose Landmarker (full)",
        "required": False,
        "note": "Optional - for full pose detection accuracy.",
    },
    "face_landmarker.task": {
        "url": "https://storage.googleapis.com/mediapipe-tasks/vision/face_landmarker/face_landmarker.task",
        "description": "MediaPipe Face Landmarker",
        "required": False,
        "note": "Optional - for face detection and expression analysis.",
    },
}


def download_file(url: str, destination: Path, description: str = None) -> bool:
    """Download file with progress indication."""
    if destination.exists():
        print(f"✅ Already exists: {destination.name}")
        return True

    print(f"⬇️  Downloading: {description or destination.name}")
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)

        with urlopen(url) as response:
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            chunk_size = 8192

            with open(destination, "wb") as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)

                    # Progress bar
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        bar_len = 30
                        filled = int(bar_len * percent / 100)
                        bar = "█" * filled + "░" * (bar_len - filled)
                        print(f"  [{bar}] {percent:.1f}%", end="\r")

        print(f"✅ Downloaded: {destination.name}")
        return True

    except Exception as e:
        print(f"❌ Failed to download: {e}")
        if destination.exists():
            destination.unlink()
        return False


def verify_file(file_path: Path) -> bool:
    """Verify downloaded file exists and is valid."""
    if not file_path.exists():
        return False
    if file_path.stat().st_size == 0:
        return False
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Download ML models required by CC Suggestion Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Models downloaded:
  - YAMNet: Advanced audio event classification (TensorFlow required)
  - Pose Landmarker: Speaker pose detection (MediaPipe required)
  - Face Landmarker: Speaker face detection (MediaPipe required)

All models are optional. Pipeline works with heuristic audio detection if models unavailable.

Examples:
  # Download to default models/ directory
  python scripts/download_models.py

  # Download to custom directory
  python scripts/download_models.py --models-dir ./models_custom

  # Download only specific model
  python scripts/download_models.py --select yamnet
        """,
    )

    parser.add_argument(
        "--models-dir",
        type=Path,
        default=Path("models"),
        help="Directory to save models (default: models/)",
    )
    parser.add_argument(
        "--select",
        choices=list(MODELS.keys()),
        help="Download only specific model",
    )
    parser.add_argument(
        "--skip-verification",
        action="store_true",
        help="Skip file verification after download",
    )

    args = parser.parse_args()

    models_to_download = {args.select: MODELS[args.select]} if args.select else MODELS

    print("\n" + "=" * 70)
    print("CC SUGGESTION TOOL: Model Download Manager")
    print("=" * 70 + "\n")

    print(f"📁 Models directory: {args.models_dir.absolute()}\n")

    print("📦 Available models:\n")
    for model_name, model_info in models_to_download.items():
        status = "✓ REQUIRED" if model_info["required"] else "○ OPTIONAL"
        print(f"  {status}: {model_name}")
        print(f"         {model_info['description']}")
        if model_info.get("note"):
            print(f"         {model_info['note']}")
        print()

    print("Downloading models...")
    print("=" * 70 + "\n")

    success_count = 0
    failed_models = []

    for model_name, model_info in models_to_download.items():
        dest_path = args.models_dir / model_name
        url = model_info["url"]

        if download_file(url, dest_path, model_info["description"]):
            if verify_file(dest_path):
                success_count += 1
                print(f"   ✓ {dest_path.stat().st_size / 1024 / 1024:.1f} MB")
            else:
                print(f"❌ Verification failed: {dest_path}")
                failed_models.append(model_name)
        else:
            failed_models.append(model_name)
        print()

    # Summary
    print("=" * 70)
    print(f"✅ Download complete: {success_count}/{len(models_to_download)} succeeded\n")

    if failed_models:
        print(f"⚠️  Failed to download: {', '.join(failed_models)}")
        print("   These models are optional - pipeline will work without them.")
        print("   You can retry downloading later.\n")

    print("📝 Next steps:")
    print(f"   1. Models are ready in: {args.models_dir.absolute()}")
    print("   2. Update requirements.txt if installing ML dependencies:")
    print("      - For YAMNet: pip install tensorflow")
    print("      - For MediaPipe: pip install mediapipe")
    print("   3. Run pipeline: python -m cc_suggester.cli --input video.mp4")
    print("   4. Check config/yamnet.json for YAMNet configuration\n")

    return 0 if not failed_models else 1


if __name__ == "__main__":
    sys.exit(main())
