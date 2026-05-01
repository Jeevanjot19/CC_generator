# Video Collection Strategy: Finding 3-5 Hindi/Tamil YouTube Videos

**Goal:** Collect 3-5 high-quality Hindi/Tamil videos with clear non-speech events  
**Timeline:** 1-2 hours to find and download  
**Effort Level:** Low - mostly searching and downloading

---

## QUICK STRATEGY

### 1. YouTube Search Terms (Find videos with clear events)

**High-likelihood searches:**
- "Indian interview" + "car horn" / "traffic"
- "Hindi podcast" OR "Tamil interview" 
- "Indian drama scene" (scripted reactions, sound effects)
- "Hindi comedy sketch" (laughter, surprise sounds)
- "Indian news interview" (multiple speakers, background noise)
- "Hindi movie scene" (with subtitles for context)

**Examples that work well:**
```
Search: "Hindi interview" "car horn" site:youtube.com
Search: "Tamil podcast" "traffic noise" site:youtube.com
Search: "Hindi podcast" OR "Tamil podcast" 5+ minutes
Search: "Indian drama scene" "glass breaking" OR "door slam"
```

### 2. Video Selection Criteria

✅ **Good Videos Have:**
- [ ] 5-15 minutes duration (not too short/long)
- [ ] Clear audio (can hear dialogue and sounds)
- [ ] 3-10 non-speech events (honking, laughter, doors, etc.)
- [ ] Visible speakers (for reaction validation)
- [ ] Hindi or Tamil language
- [ ] Subtitles helpful (understand context, know when sounds happen)

❌ **Avoid:**
- Background-only ambient noise (no clear events)
- Music-heavy videos (hard to distinguish from dialogue)
- Very compressed audio (artifacts cause false positives)
- Silent/text-only videos (no audio to caption)

### 3. Where to Find Videos

| Source | Pros | Cons | Links |
|--------|------|------|-------|
| **YouTube** | Huge variety, subtitles often available | Copyright concerns, need caution | https://youtube.com |
| **NewsX, NDTV (YouTube)** | Real interviews, clear audio | News-specific content | YouTube channels |
| **Podcast channels** | Structured, long form | Fewer sound effects | Spotify/YouTube |
| **Indian drama clips** | Lots of action/sounds | Scripted (less realistic) | YouTube clips |

### 4. Recommended Search Examples

**Search 1: Hindi News Interviews**
```
"Hindi news interview" site:youtube.com 10-20 minutes
→ Try channels: NewsX, NDTV, India Today
→ Look for studio interviews with background noise
```

**Search 2: Hindi Podcasts**
```
"Hindi podcast" OR "Hindustani podcast" 15+ minutes
→ Try: BeerBiceps, FitTR, Indian internet channels
→ Look for casual conversation with ambient sounds
```

**Search 3: Indian Drama/Comedy**
```
"Hindi comedy scene" OR "Indian drama scene" 5-15 minutes
→ Sound effects: honking, glass breaking, doors
→ Actors react to sounds (good for validation)
```

**Search 4: Tamil Content**
```
"Tamil interview" OR "Tamil podcast" OR "Tamil news"
→ Try: News channels (Sun News, Thanthi TV)
→ Try: Podcast channels (Tamil talk shows)
```

### 5. How to Download Videos

**Option A: youtube-dl (Most reliable)**
```bash
# Install
pip install youtube-dl

# Download video + audio
youtube-dl -f best "https://youtube.com/watch?v=VIDEO_ID" -o "videos/%(title)s.%(ext)s"

# Download audio only (WAV)
youtube-dl -f bestaudio "https://youtube.com/watch?v=VIDEO_ID" -x --audio-format wav -o "videos/%(title)s.%(ext)s"
```

**Option B: yt-dlp (Newer, faster)**
```bash
# Install
pip install yt-dlp

# Download
yt-dlp -f best "https://youtube.com/watch?v=VIDEO_ID" -o "videos/%(title)s.%(ext)s"
```

**Option C: Manual Download**
- Use site: https://y2mate.com or https://savefrom.net
- Download video, save to `videos/` folder
- Convert to WAV if needed

### 6. Video Naming Convention

```
videos/
├── hindi_interview_01_newsX.mp4
├── hindi_interview_01_newsX.wav
├── tamil_podcast_01_beerbiceps.mp4
├── tamil_podcast_01_beerbiceps.wav
├── hindi_drama_01_comedysketch.mp4
└── hindi_drama_01_comedysketch.wav
```

---

## ANNOTATION WORKFLOW (For each video)

### Step 1: Watch video with frame-by-frame control
- Use VLC Media Player (free)
- Enable subtitles if available (helps understand context)
- Note approximate times of sound events

### Step 2: Annotate using spreadsheet
Template:
```csv
video,start,end,label,speaker_reacted,notes
hindi_interview_01.wav,0.5,1.2,honking,yes,"Car outside, speaker paused"
hindi_interview_01.wav,2.3,2.8,laughter,yes,"Audience laughing"
hindi_interview_01.wav,5.1,6.5,door_slam,yes,"Someone entered, speaker turned"
```

### Step 3: Validate timing (±0.1s precision)
- Use Audacity for frame-by-frame audio waveform
- Ensure start/end times are consistent
- Run pipeline and compare predictions to ground truth

---

## QUICK CHECKLIST (3-5 Videos)

### Video 1: Hindi News Interview
- [ ] Search: "Hindi news interview" on YouTube (10+ min)
- [ ] Select one with clear background sounds
- [ ] Download MP4 + audio
- [ ] Extract to WAV if needed
- [ ] Watch and annotate (3-5 events expected)

### Video 2: Hindi Podcast
- [ ] Search: "Hindi podcast" (15+ min)
- [ ] Select one with ambient noise/reactions
- [ ] Download
- [ ] Annotate (3-5 events)

### Video 3: Tamil Interview/Podcast
- [ ] Search: "Tamil podcast" or "Tamil interview"
- [ ] Verify language is Tamil
- [ ] Download
- [ ] Annotate (3-5 events)

### Video 4-5: (Optional for robustness)
- [ ] Additional Hindi or Tamil content
- [ ] Different style (drama, comedy, news)

---

## TOTAL EVENTS EXPECTED

```
Video 1 (Hindi news):     4-6 events
Video 2 (Hindi podcast):  3-5 events
Video 3 (Tamil):          3-5 events
Video 4-5 (optional):     6-10 events (if collected)

Total: 10-26 events on 3-5 videos
```

---

## LEGAL NOTES

✅ **Fair Use** (Safe for project use):
- Educational purpose (open-source project)
- Non-profit, open-source development
- Limited portion of copyrighted material
- Not competing with original content
- Cite source in project documentation

❌ **Avoid:**
- Movie clips without permission
- Licensed music/content without rights
- Claiming ownership of downloaded content
- Removing original attribution

**Best Practice:** Document sources in CREDITS.md
```markdown
## Video Sources

1. hindi_interview_01.mp4
   - Source: NewsX YouTube channel
   - URL: https://youtube.com/watch?v=...
   - License: Fair use for educational/research purposes
   - Date collected: May 1, 2026

2. tamil_podcast_01.mp4
   - Source: [Channel name]
   - URL: [URL]
   - License: Fair use
   - Date collected: May 1, 2026
```

---

## INSTALLATION: Download Tools

### youtube-dl (Simple, Most Reliable)
```bash
pip install youtube-dl

# Test
youtube-dl --version
```

### yt-dlp (Faster, More Features)
```bash
pip install yt-dlp

# Test
yt-dlp --version
```

### FFmpeg (Optional, for format conversion)
```bash
# Windows: Install via chocolatey
choco install ffmpeg

# Or download: https://ffmpeg.org/download.html
# Or use within Python: pip install moviepy
```

---

## EXAMPLE WORKFLOW

### Step 1: Search and Find
```
1. Go to YouTube
2. Search: "Hindi news interview NewsX"
3. Filter: 10-20 minutes, has clear audio
4. Watch preview (first 2 min)
5. If good: Copy video ID from URL
```

### Step 2: Download
```bash
# Get the YouTube URL
URL="https://youtube.com/watch?v=dQw4w9WgXcQ"

# Option A: Download video only
yt-dlp -f best "$URL" -o "videos/hindi_interview_01.mp4"

# Option B: Extract audio to WAV
yt-dlp -f bestaudio "$URL" -x --audio-format wav -o "videos/hindi_interview_01.wav"
```

### Step 3: Annotate
```
Open: hindi_interview_01.wav
Watch: Full video with VLC
Document: Start/end times of events
Example:
  - 0.5s-1.2s: honking (traffic outside)
  - 2.3s-2.8s: laughter (audience)
  - 5.1s-6.5s: door slam (new guest)
```

### Step 4: Run Pipeline
```bash
# Run detection
python -m cc_suggester.cli \
  --input videos/hindi_interview_01.wav \
  --output output/hindi_01.srt \
  --events-json output/hindi_01_events.json

# Evaluate against ground truth
python -m cc_suggester.eval \
  --predictions output/hindi_01_events.json \
  --ground-truth annotations/hindi_01_ground_truth.csv \
  --output output/hindi_01_metrics.json
```

### Step 5: Check Results
```
Expected metrics:
- Precision: 0.80-0.95
- Recall: 0.75-0.95
- Overcaption rate: < 10%
- Detection rate: > 80%
```

---

## AUTOMATION: Download Script

I'll create a Python script to automate steps 1-2. See `scripts/download_youtube_videos.py`

Usage:
```bash
python scripts/download_youtube_videos.py \
  --urls "URL1" "URL2" "URL3" \
  --output-dir videos/ \
  --format wav
```

---

## SUCCESS CRITERIA

✅ When you're ready to annotate:
- [ ] 3-5 videos downloaded
- [ ] Total ~15-25 events across all videos
- [ ] Clear audio quality
- [ ] Hindi or Tamil language
- [ ] Visible speaker reactions (for visual validation)

✅ After annotation:
- [ ] Ground truth CSVs created for each video
- [ ] Timing ±0.1s precision
- [ ] All events labeled consistently
- [ ] Ready for pipeline evaluation

✅ After validation:
- [ ] Run pipeline on all videos
- [ ] Compute metrics (precision, recall, F1)
- [ ] Check compliance: overcaption <= 10%? recall >= 80%?
- [ ] Report results in proposal

---

## NEXT: Priority 2 Implementation

Once you have videos downloaded (even if not annotated yet), we'll implement:

1. **Model Download Script** - Auto-download YAMNet, MediaPipe models
2. **YAMNet Integration Testing** - Benchmark heuristic vs. YAMNet
3. **Validation Report Enhancement** - Show metrics in HTML output

This will strengthen your proposal with:
- ✅ Easy setup (no manual model download)
- ✅ Proven multi-backend support (heuristic + YAMNet)
- ✅ Visible metrics (report shows F1, precision, recall)
