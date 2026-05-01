#!/usr/bin/env python3
"""
Complete Testing Workflow: Download, Process, Annotate, Evaluate
Automates the entire validation pipeline in one command.
"""

import json
import subprocess
import sys
from pathlib import Path
import shutil


def run_cmd(cmd, description=""):
    """Run a command and handle errors."""
    if description:
        print(f"\n⏳ {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    print("\n" + "=" * 70)
    print("🚀 FULL TESTING WORKFLOW: Download → Process → Annotate → Evaluate")
    print("=" * 70)
    
    # Setup directories
    videos_dir = Path("videos")
    results_dir = Path("results")
    truth_dir = Path("ground_truth")
    
    for d in [videos_dir, results_dir, truth_dir]:
        d.mkdir(exist_ok=True)
    
    print(f"\n📁 Created directories: {videos_dir}/, {results_dir}/, {truth_dir}/")
    
    # Check for demo audio/video files
    demo_files = [
        Path("samples/demo_test.wav"),
        Path("samples/demo_video.mp4"),
    ]
    
    test_videos = [f for f in demo_files if f.exists()]
    if not test_videos:
        print(f"⚠️  No test files found (checked: {[str(f) for f in demo_files]})")
        return
    
    print(f"\n✅ Found {len(test_videos)} test file(s): {[f.name for f in test_videos]}")
    
    # ========================================================================
    # STEP 1: Run Pipeline
    # ========================================================================
    print(f"\n{'━' * 70}")
    print("STEP 1: Running pipeline on videos")
    print("━" * 70)
    
    for video_file in test_videos:
        base_name = video_file.stem
        print(f"\n📹 Processing: {base_name}")
        
        srt_file = results_dir / f"{base_name}.srt"
        events_file = results_dir / f"{base_name}_events.json"
        report_file = results_dir / f"{base_name}_report.html"
        
        cmd = (
            f'python -m cc_suggester.cli '
            f'--input "{video_file}" '
            f'--output "{srt_file}" '
            f'--events-json "{events_file}" '
            f'--report-html "{report_file}"'
        )
        
        if run_cmd(cmd):
            print(f"✅ Generated:")
            print(f"   ✓ {srt_file}")
            print(f"   ✓ {events_file}")
            print(f"   ✓ {report_file}")
        else:
            print(f"⚠️  Pipeline execution had issues")
    
    # ========================================================================
    # STEP 2: Create Ground Truth
    # ========================================================================
    print(f"\n{'━' * 70}")
    print("STEP 2: Creating ground truth annotations")
    print("━" * 70)
    
    # Sample ground truth for test files
    ground_truths = {
        "demo_test": [
            {"start": 0.5, "end": 1.2, "label": "honking"},
            {"start": 2.1, "end": 3.0, "label": "explosion"},
        ],
        "demo_video": [
            {"start": 1.5, "end": 2.8, "label": "honking"},
            {"start": 5.2, "end": 6.9, "label": "explosion"},
            {"start": 12.1, "end": 13.5, "label": "laughter"},
            {"start": 18.3, "end": 19.7, "label": "applause"},
        ],
    }
    
    for video_file in test_videos:
        base_name = video_file.stem
        truth_file = truth_dir / f"{base_name}_ground_truth.csv"
        
        # Create CSV header
        csv_lines = ["start,end,label"]
        
        if base_name in ground_truths:
            for event in ground_truths[base_name]:
                csv_lines.append(f"{event['start']},{event['end']},{event['label']}")
        else:
            csv_lines.append("# Please annotate by watching the video (start_sec,end_sec,event_label)")
        
        truth_file.write_text("\n".join(csv_lines) + "\n")
        print(f"✅ Created: {truth_file}")
    
    # ========================================================================
    # STEP 3: Run Evaluation
    # ========================================================================
    print(f"\n{'━' * 70}")
    print("STEP 3: Running evaluation")
    print("━" * 70)
    
    metrics_summary = {}
    
    for video_file in test_videos:
        base_name = video_file.stem
        events_file = results_dir / f"{base_name}_events.json"
        truth_file = truth_dir / f"{base_name}_ground_truth.csv"
        metrics_file = results_dir / f"{base_name}_metrics.json"
        
        if events_file.exists() and truth_file.exists():
            print(f"\n📊 Evaluating: {base_name}")
            
            cmd = (
                f'python -m cc_suggester.eval '
                f'--predictions "{events_file}" '
                f'--ground-truth "{truth_file}" '
                f'--output "{metrics_file}"'
            )
            
            if run_cmd(cmd):
                # Display metrics
                if metrics_file.exists():
                    metrics = json.loads(metrics_file.read_text())
                    metrics_summary[base_name] = metrics
                    
                    print(f"  ✅ Metrics saved to: {metrics_file}")
                    print(f"     Precision:    {metrics.get('precision', 0):.1%}")
                    print(f"     Recall:       {metrics.get('recall', 0):.1%}")
                    print(f"     F1 Score:     {metrics.get('f1_score', 0):.3f}")
                    print(f"     Overcaption:  {metrics.get('overcaption_rate', 0):.1%}")
                    
                    compliance = metrics.get('compliance', {})
                    status = "✅ PASS" if compliance.get('pass') else "⚠️ CHECK"
                    print(f"     Compliance:   {status}")
    
    # ========================================================================
    # STEP 4: Summary
    # ========================================================================
    print(f"\n{'━' * 70}")
    print("✅ WORKFLOW COMPLETE!")
    print("━" * 70)
    
    print(f"\n📁 Generated Files:")
    print(f"   Videos:       {videos_dir}/")
    print(f"   Results:      {results_dir}/")
    print(f"   Ground Truth: {truth_dir}/")
    
    print(f"\n📊 Summary of Results:")
    if metrics_summary:
        for name, metrics in metrics_summary.items():
            print(f"\n   {name}:")
            print(f"     • Precision: {metrics.get('precision', 0):.1%}")
            print(f"     • Recall:    {metrics.get('recall', 0):.1%}")
            print(f"     • F1:        {metrics.get('f1_score', 0):.3f}")
    else:
        print("   (No metrics available yet)")
    
    print(f"\n🎯 Next Steps:")
    print(f"   1. Review SRT captions:")
    print(f"      cat results/*.srt")
    print(f"   2. View HTML reports (in browser):")
    print(f"      results/*_report.html")
    print(f"   3. Launch interactive dashboard:")
    print(f"      streamlit run streamlit_app.py")
    print(f"      Then enter: results/demo_video_events.json")
    print(f"   4. Improve ground truth:")
    print(f"      Edit ground_truth/*_ground_truth.csv")
    print(f"   5. Re-run evaluation:")
    print(f"      python -m cc_suggester.eval --predictions results/demo_video_events.json --ground-truth ground_truth/demo_video_ground_truth.csv --output results/demo_video_metrics.json")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
