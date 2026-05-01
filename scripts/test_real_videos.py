#!/usr/bin/env python3
"""
Real Video Testing Workflow
Complete pipeline for testing with actual videos:
1. Validate videos
2. Extract audio
3. Run pipeline
4. Create annotation templates
5. Run evaluation
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def run_cmd(cmd, description="", show_output=False):
    """Run a command and return success status."""
    if description:
        print(f"⏳ {description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=not show_output,
            text=True,
            timeout=600
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_dependencies():
    """Verify all required dependencies are installed."""
    print("\n" + "=" * 70)
    print("🔧 CHECKING DEPENDENCIES")
    print("=" * 70)
    
    required = {
        "ffmpeg": "FFmpeg",
        "ffprobe": "FFprobe",
        "python": "Python",
    }
    
    missing = []
    
    for cmd, name in required.items():
        try:
            result = subprocess.run(
                [cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"✅ {name} found")
            else:
                missing.append(name)
        except FileNotFoundError:
            missing.append(name)
    
    if missing:
        print(f"\n⚠️  Missing: {', '.join(missing)}")
        if "FFmpeg" in missing:
            print("   Install with:")
            print("   • Windows: choco install ffmpeg")
            print("   • Mac: brew install ffmpeg")
            print("   • Linux: apt-get install ffmpeg")
        return False
    
    print("✅ All dependencies found")
    return True


def validate_videos(video_dir: str | Path):
    """Validate all videos in directory."""
    video_dir = Path(video_dir)
    video_files = list(video_dir.glob("**/*.mp4")) + list(video_dir.glob("**/*.mov")) + list(video_dir.glob("**/*.avi"))
    
    if not video_files:
        print(f"⚠️  No videos found in {video_dir}")
        return []
    
    print(f"\n✅ Found {len(video_files)} video(s)")
    valid_videos = []
    
    for video_file in video_files:
        if run_cmd(
            f'python scripts/video_utils.py "{video_file}"',
            f"Validating: {video_file.name}"
        ):
            valid_videos.append(video_file)
    
    return valid_videos


def extract_audio_from_videos(video_files: list[Path]) -> dict[str, Path]:
    """Extract audio from all videos."""
    print(f"\n{'=' * 70}")
    print("🎵 EXTRACTING AUDIO FROM VIDEOS")
    print("=" * 70)
    
    audio_dir = Path("audio")
    audio_dir.mkdir(exist_ok=True)
    
    extracted = {}
    
    for video_file in video_files:
        audio_file = audio_dir / f"{video_file.stem}.wav"
        
        if audio_file.exists():
            print(f"⏭️  Already extracted: {audio_file.name}")
            extracted[video_file.stem] = audio_file
            continue
        
        if run_cmd(
            f'python scripts/video_utils.py "{video_file}" --extract-audio "{audio_file}"',
            f"Extracting: {video_file.name}"
        ):
            extracted[video_file.stem] = audio_file
    
    return extracted


def process_audio_through_pipeline(audio_files: dict[str, Path]) -> dict[str, dict]:
    """Run pipeline on extracted audio."""
    print(f"\n{'=' * 70}")
    print("🎬 RUNNING PIPELINE ON AUDIO")
    print("=" * 70)
    
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    results = {}
    
    for name, audio_file in audio_files.items():
        srt_file = results_dir / f"{name}.srt"
        events_file = results_dir / f"{name}_events.json"
        report_file = results_dir / f"{name}_report.html"
        
        if events_file.exists():
            print(f"⏭️  Already processed: {name}")
            results[name] = {
                'srt': srt_file,
                'events': events_file,
                'report': report_file
            }
            continue
        
        cmd = (
            f'python -m cc_suggester.cli '
            f'--input "{audio_file}" '
            f'--output "{srt_file}" '
            f'--events-json "{events_file}" '
            f'--report-html "{report_file}"'
        )
        
        if run_cmd(cmd, f"Processing: {name}"):
            results[name] = {
                'srt': srt_file,
                'events': events_file,
                'report': report_file
            }
            print(f"✅ Results:")
            print(f"   • SRT: {srt_file.name}")
            print(f"   • Events: {events_file.name}")
            print(f"   • Report: {report_file.name}")
    
    return results


def create_annotation_templates(video_files: list[Path]):
    """Create annotation templates for all videos."""
    print(f"\n{'=' * 70}")
    print("📝 CREATING ANNOTATION TEMPLATES")
    print("=" * 70)
    
    for video_file in video_files:
        run_cmd(
            f'python scripts/annotation_tool.py "{video_file}" --template',
            f"Template: {video_file.name}"
        )


def print_next_steps(results: dict):
    """Print helpful next steps for user."""
    print(f"\n{'=' * 70}")
    print("✅ WORKFLOW COMPLETE!")
    print("=" * 70)
    
    print("\n📊 Generated Outputs:")
    for name, files in results.items():
        print(f"\n  {name}:")
        print(f"    • SRT: {files['srt'].relative_to(Path.cwd())}")
        print(f"    • Events: {files['events'].relative_to(Path.cwd())}")
        print(f"    • Report: {files['report'].relative_to(Path.cwd())}")
    
    print(f"\n📝 Next Steps:")
    print("   1. ANNOTATE GROUND TRUTH:")
    print("      • Watch each video")
    print("      • Edit: ground_truth/*_annotations.csv")
    print("      • Format: start_sec,end_sec,label")
    print("      OR use interactive tool:")
    print("      python scripts/annotation_tool.py video.mp4 --interactive")
    print("")
    print("   2. EVALUATE RESULTS:")
    for name in results.keys():
        print(f"      python -m cc_suggester.eval \\")
        print(f"        --predictions results/{name}_events.json \\")
        print(f"        --ground-truth ground_truth/{name}_ground_truth.csv \\")
        print(f"        --output results/{name}_metrics.json")
    print("")
    print("   3. REVIEW IN DASHBOARD:")
    print("      streamlit run streamlit_app.py")
    print("      Then enter: results/VIDEO_NAME_events.json")
    print("")
    print("   4. VIEW HTML REPORTS:")
    for name, files in results.items():
        print(f"      • Open in browser: {files['report']}")
    
    print(f"\n💡 Tips:")
    print("   • Ground truth should be as accurate as possible (watch video carefully)")
    print("   • Use VLC Media Player for precise timestamps (View → Advanced Controls)")
    print("   • Start with 3-5 short videos (2-5 min each)")
    print("   • Save annotations CSV frequently")


def main():
    print("\n" + "=" * 70)
    print("🎬 REAL VIDEO TESTING WORKFLOW")
    print("=" * 70)
    
    # Check dependencies
    if not check_dependencies():
        print("\n⚠️  Please install missing dependencies and try again")
        return False
    
    # Create necessary directories
    for d in ["videos", "audio", "results", "ground_truth"]:
        Path(d).mkdir(exist_ok=True)
    
    # Check for videos
    video_dir = Path("videos")
    if not list(video_dir.glob("*.*")):
        print(f"\n⚠️  No videos found in {video_dir}/")
        print("   Download videos first:")
        print("   python scripts/download_youtube_videos.py --urls URL1 URL2 --output-dir videos/")
        return False
    
    # Validate videos
    valid_videos = validate_videos(video_dir)
    if not valid_videos:
        print("❌ No valid videos found")
        return False
    
    # Extract audio
    audio_files = extract_audio_from_videos(valid_videos)
    if not audio_files:
        print("❌ No audio extracted")
        return False
    
    # Process through pipeline
    results = process_audio_through_pipeline(audio_files)
    if not results:
        print("❌ No results from pipeline")
        return False
    
    # Create annotation templates
    create_annotation_templates(valid_videos)
    
    # Print next steps
    print_next_steps(results)
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
