# ✅ FFmpeg Installation Guide

## Easiest Option: Download & Extract

### Step 1: Download FFmpeg (Pre-built)
Visit: https://ffmpeg.org/download.html

**For Windows:**
- Click "Windows builds by BtbN" (most reliable)
- Download the latest "static" build (e.g., `ffmpeg-N-124278-gcc3ca17127-win64-lgpl.zip`)
- Or go directly to: https://github.com/BtbN/FFmpeg-Builds/releases

### Step 2: Extract to a Folder
```
C:\FFmpeg\  (or any folder)
  ├── bin\
  │   ├── ffmpeg.exe
  │   ├── ffprobe.exe
  │   └── ffplay.exe
  └── ...
```

### Step 3: Add to System PATH
**Windows 10/11:**
1. Press `Win + X` → "System"
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Under "System variables", click "Path"
5. Click "Edit"
6. Click "New"
7. Enter: `C:\FFmpeg\bin` (or wherever you extracted it)
8. Click OK, OK, OK

**Restart your terminal** after adding to PATH.

---

## Verification

After adding to PATH, test:
```powershell
ffmpeg -version
ffprobe -version
```

Both should show version info.

---

## Alternative: Chocolatey (Advanced)

If you have Chocolatey installed:
```powershell
choco install ffmpeg
```

---

## Alternative: Direct URL
Fastest download (full static build):
https://www.gyan.dev/ffmpeg/builds/

Download `ffmpeg-release-essentials.zip`, extract to `C:\FFmpeg\`, and add `C:\FFmpeg\bin` to PATH.

---

## After Installation: Test the Workflow

```powershell
# Verify FFmpeg works
ffmpeg -version

# Run the test workflow
cd d:\subtitle
python scripts/test_real_videos.py

# Should now show: ✅ FFmpeg found
```

---

## If Still Not Working

1. Close ALL PowerShell windows
2. Open a NEW PowerShell window
3. Run: `python scripts/test_real_videos.py`

The PATH changes only take effect in newly opened terminals.
