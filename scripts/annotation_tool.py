#!/usr/bin/env python3
"""
Interactive Ground Truth Annotation Tool
Helps users annotate video timestamps for CC events.
"""

import csv
import json
from pathlib import Path
from datetime import timedelta


def format_timestamp(seconds: float) -> str:
    """Format seconds to HH:MM:SS.mmm format."""
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(int(td.total_seconds()), 3600)
    minutes, seconds_int = divmod(remainder, 60)
    milliseconds = int((td.total_seconds() - int(td.total_seconds())) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds_int:02d}.{milliseconds:03d}"


def parse_timestamp(ts_str: str) -> float:
    """Parse HH:MM:SS.mmm format to seconds."""
    try:
        parts = ts_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds_parts = parts[2].split('.')
        seconds = int(seconds_parts[0])
        milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
        
        return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
    except (ValueError, IndexError):
        return None


def create_annotation_template(video_file: str | Path) -> Path:
    """Create a blank annotation CSV for a video."""
    video_path = Path(video_file)
    annotation_file = Path("ground_truth") / f"{video_path.stem}_annotations.csv"
    
    annotation_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(annotation_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['start_sec', 'end_sec', 'label', 'notes'])
        writer.writeheader()
        writer.writerow({
            'start_sec': '0.0',
            'end_sec': '1.0',
            'label': 'example_event',
            'notes': 'Delete this row and add your annotations'
        })
    
    print(f"✅ Created annotation template: {annotation_file}")
    return annotation_file


def interactive_annotation(video_file: str | Path) -> Path:
    """Interactive annotation mode (command-line)."""
    video_path = Path(video_file)
    annotation_file = Path("ground_truth") / f"{video_path.stem}_ground_truth.csv"
    
    annotation_file.parent.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "=" * 70)
    print("📝 INTERACTIVE ANNOTATION TOOL")
    print("=" * 70)
    print(f"\nVideo: {video_path.name}")
    print("\nInstructions:")
    print("  1. Open the video in your media player (VLC, Windows Media Player, etc.)")
    print("  2. For each sound event, note the timestamp when it starts/ends")
    print("  3. Enter timestamps in format: MM:SS.mmm or HH:MM:SS.mmm")
    print("  4. Press Enter twice to finish")
    print("\nEvent types: honking, explosion, laughter, applause, glass_breaking, etc.")
    print("Or use: 'skip' to skip this video, 'cancel' to abort\n")
    
    events = []
    
    while True:
        print(f"\n📍 Event #{len(events) + 1}")
        
        # Get start time
        start_input = input("  Start time (MM:SS or HH:MM:SS): ").strip()
        
        if start_input.lower() == 'done':
            break
        elif start_input.lower() == 'skip':
            print("⏭️  Skipped")
            return None
        elif start_input.lower() == 'cancel':
            print("❌ Cancelled")
            return None
        
        start_sec = parse_timestamp(start_input)
        if start_sec is None:
            print("❌ Invalid timestamp format")
            continue
        
        # Get end time
        end_input = input("  End time (MM:SS or HH:MM:SS): ").strip()
        end_sec = parse_timestamp(end_input)
        if end_sec is None:
            print("❌ Invalid timestamp format")
            continue
        
        if end_sec <= start_sec:
            print("❌ End time must be after start time")
            continue
        
        # Get label
        label = input("  Event label (honking/explosion/laughter/applause): ").strip().lower()
        if not label:
            label = "sound_event"
        
        # Get notes (optional)
        notes = input("  Notes (optional): ").strip()
        
        events.append({
            'start': start_sec,
            'end': end_sec,
            'label': label,
            'notes': notes
        })
        
        print(f"✅ Added: {format_timestamp(start_sec)} → {format_timestamp(end_sec)} [{label}]")
    
    # Save to CSV
    if events:
        with open(annotation_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['start', 'end', 'label', 'notes'])
            writer.writeheader()
            writer.writerows(events)
        
        print(f"\n✅ Saved {len(events)} annotations to: {annotation_file}")
        return annotation_file
    else:
        print("\n⚠️  No events annotated")
        return None


def convert_to_eval_format(annotation_file: str | Path) -> Path:
    """Convert annotation CSV to evaluation format (start,end,label)."""
    annotation_file = Path(annotation_file)
    
    if not annotation_file.exists():
        print(f"❌ File not found: {annotation_file}")
        return None
    
    # Try different field names
    field_names = None
    with open(annotation_file, 'r') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames:
            field_names = reader.fieldnames
    
    if not field_names:
        print(f"❌ Could not read CSV headers")
        return None
    
    # Map fields
    start_field = next((f for f in field_names if 'start' in f.lower()), 'start')
    end_field = next((f for f in field_names if 'end' in f.lower()), 'end')
    label_field = next((f for f in field_names if 'label' in f.lower()), 'label')
    
    output_file = annotation_file.parent / f"{annotation_file.stem}_eval.csv"
    
    with open(annotation_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=['start', 'end', 'label'])
        writer.writeheader()
        
        for row in reader:
            if row.get(start_field) and row.get(end_field):
                writer.writerow({
                    'start': row[start_field],
                    'end': row[end_field],
                    'label': row.get(label_field, 'sound_event')
                })
    
    print(f"✅ Converted to evaluation format: {output_file}")
    return output_file


def merge_annotations(*annotation_files: str | Path) -> Path:
    """Merge multiple annotation files."""
    output_file = Path("ground_truth") / "merged_annotations.csv"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    all_rows = []
    
    for annotation_file in annotation_files:
        annotation_file = Path(annotation_file)
        if not annotation_file.exists():
            print(f"⚠️  Skipped (not found): {annotation_file}")
            continue
        
        with open(annotation_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('start') and row.get('end'):
                    all_rows.append(row)
    
    with open(output_file, 'w', newline='') as f:
        if all_rows:
            writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
            writer.writeheader()
            writer.writerows(all_rows)
    
    print(f"✅ Merged {len(all_rows)} annotations to: {output_file}")
    return output_file


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python annotation_tool.py <video_file> [--interactive]")
        print("       python annotation_tool.py <annotation.csv> --convert")
        sys.exit(1)
    
    file_arg = sys.argv[1]
    
    if "--interactive" in sys.argv:
        interactive_annotation(file_arg)
    elif "--convert" in sys.argv:
        convert_to_eval_format(file_arg)
    elif "--template" in sys.argv:
        create_annotation_template(file_arg)
    else:
        # Default: create template
        create_annotation_template(file_arg)
