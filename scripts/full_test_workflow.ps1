# ============================================================================
# Full Testing Workflow: Download, Process, Annotate, Evaluate
# ============================================================================
# This script automates the complete validation pipeline

param(
    [switch]$SkipDownload,
    [switch]$SkipPipeline,
    [switch]$SkipEval,
    [switch]$Dashboard
)

$ErrorActionPreference = "Stop"

# Configuration
$videosDir = "videos"
$resultsDir = "results"
$groundTruthDir = "ground_truth"

# Create directories
Write-Host "📁 Creating directories..." -ForegroundColor Cyan
mkdir -Force $videosDir | Out-Null
mkdir -Force $resultsDir | Out-Null
mkdir -Force $groundTruthDir | Out-Null

# ============================================================================
# STEP 1: Download Videos
# ============================================================================
if (-not $SkipDownload) {
    Write-Host "`n📥 STEP 1: Downloading test videos..." -ForegroundColor Green
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
    
    # Check if yt-dlp is installed
    try {
        yt-dlp --version | Out-Null
    } catch {
        Write-Host "❌ yt-dlp not found. Installing..." -ForegroundColor Yellow
        pip install yt-dlp
    }
    
    # Download sample videos (English + Hindi)
    # These are intentionally generic URLs - replace with real ones
    $videoUrls = @(
        # English action clip (small file for testing)
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        # Hindi movie scene (small file for testing)
        "https://www.youtube.com/watch?v=J6eI5t2ZBUU"
    )
    
    foreach ($url in $videoUrls) {
        Write-Host "⏳ Downloading: $url" -ForegroundColor Yellow
        try {
            # Download short clip (max 5 minutes) in MP4
            yt-dlp `
                --format "best[ext=mp4]" `
                --output "$videosDir/%(title)s.%(ext)s" `
                --max-downloads 1 `
                --socket-timeout 30 `
                "$url" 2>&1 | Select-Object -First 5
            Write-Host "✅ Downloaded" -ForegroundColor Green
        } catch {
            Write-Host "⚠️  Could not download $url (network may be restricted)" -ForegroundColor Yellow
            Write-Host "   Continuing with local demo video instead..." -ForegroundColor Gray
        }
    }
}

# Check if we have any videos
$videoFiles = @(Get-ChildItem "$videosDir/*.mp4" -ErrorAction SilentlyContinue)
if ($videoFiles.Count -eq 0) {
    Write-Host "⚠️  No videos found. Using demo video from samples/" -ForegroundColor Yellow
    if (Test-Path "samples/demo_video.mp4") {
        Copy-Item "samples/demo_video.mp4" "$videosDir/demo_video.mp4"
        $videoFiles = @(Get-ChildItem "$videosDir/demo_video.mp4")
    }
}

# ============================================================================
# STEP 2: Run Pipeline on Videos
# ============================================================================
if (-not $SkipPipeline) {
    Write-Host "`n🎬 STEP 2: Running pipeline on videos..." -ForegroundColor Green
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
    
    foreach ($videoFile in $videoFiles) {
        $baseName = $videoFile.BaseName
        Write-Host "`n⏳ Processing: $baseName" -ForegroundColor Yellow
        
        try {
            python -m cc_suggester.cli `
                --input $videoFile.FullName `
                --output "$resultsDir/$baseName.srt" `
                --events-json "$resultsDir/${baseName}_events.json" `
                --report-html "$resultsDir/${baseName}_report.html"
            
            Write-Host "✅ Generated:" -ForegroundColor Green
            Write-Host "   ✓ $resultsDir/$baseName.srt" -ForegroundColor Cyan
            Write-Host "   ✓ $resultsDir/${baseName}_events.json" -ForegroundColor Cyan
            Write-Host "   ✓ $resultsDir/${baseName}_report.html" -ForegroundColor Cyan
        } catch {
            Write-Host "❌ Error processing $baseName" -ForegroundColor Red
            Write-Host $_.Exception.Message -ForegroundColor Red
        }
    }
}
}

# ============================================================================
# STEP 3: Create Ground Truth Annotations
# ============================================================================
Write-Host "`n📝 STEP 3: Creating ground truth annotations..." -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green

# Create realistic sample ground truth for demo videos
# In production, you would manually annotate by watching the video

$sampleGroundTruths = @{}
$sampleGroundTruths["demo_video"] = "start,end,label`n1.5,2.8,honking`n5.2,6.9,explosion`n12.1,13.5,laughter`n18.3,19.7,applause"
$sampleGroundTruths["demo_test"] = "start,end,label`n0.8,2.3,car_horn`n3.1,4.5,glass_breaking`n7.2,8.9,laughter"

foreach ($videoFile in $videoFiles) {
    $baseName = $videoFile.BaseName
    $truthFile = "$groundTruthDir/${baseName}_ground_truth.csv"
    
    # Use sample data if available, otherwise create basic template
    if ($sampleGroundTruths.ContainsKey($baseName)) {
        $content = $sampleGroundTruths[$baseName]
    } else {
        # Create a template for manual annotation
        $content = "start,end,label`n# Edit by watching the video - format: start_sec,end_sec,event_label"
    }
    
    Set-Content -Path $truthFile -Value $content -Encoding UTF8
    Write-Host "✅ Created: $truthFile" -ForegroundColor Green
}

# ============================================================================
# STEP 4: Run Evaluation
# ============================================================================
if (-not $SkipEval) {
    Write-Host "`n📊 STEP 4: Running evaluation..." -ForegroundColor Green
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
    
    foreach ($videoFile in $videoFiles) {
        $baseName = $videoFile.BaseName
        $eventsFile = "$resultsDir/${baseName}_events.json"
        $truthFile = "$groundTruthDir/${baseName}_ground_truth.csv"
        $metricsFile = "$resultsDir/${baseName}_metrics.json"
        
        if ((Test-Path $eventsFile) -and (Test-Path $truthFile)) {
            Write-Host "`n⏳ Evaluating: $baseName" -ForegroundColor Yellow
            
            try {
                python -m cc_suggester.eval `
                    --predictions $eventsFile `
                    --ground-truth $truthFile `
                    --output $metricsFile
                
                Write-Host "✅ Metrics saved to: $metricsFile" -ForegroundColor Green
                
                # Display metrics
                if (Test-Path $metricsFile) {
                    $metrics = Get-Content $metricsFile | ConvertFrom-Json
                    Write-Host "  Precision:  $($metrics.precision.ToString('P2'))" -ForegroundColor Cyan
                    Write-Host "  Recall:     $($metrics.recall.ToString('P2'))" -ForegroundColor Cyan
                    Write-Host "  F1 Score:   $($metrics.f1_score.ToString('F3'))" -ForegroundColor Cyan
                    Write-Host "  Overcaption: $($metrics.overcaption_rate.ToString('P2'))" -ForegroundColor Cyan
                    Write-Host "  Compliance: $($metrics.compliance.pass) ✅" -ForegroundColor Cyan
                }
            } catch {
                Write-Host "⚠️  Could not evaluate $baseName (check ground truth format)" -ForegroundColor Yellow
            }
        } else {
            Write-Host "⚠️  Skipping evaluation for $baseName (missing files)" -ForegroundColor Yellow
        }
    }
}

# ============================================================================
# STEP 5: Summary & Dashboard
# ============================================================================
Write-Host "`n📋 STEP 5: Summary" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green

Write-Host "`n✅ Workflow Complete!" -ForegroundColor Green
Write-Host "`nGenerated Files:" -ForegroundColor Cyan
Write-Host "  📁 Videos:       $videosDir/" -ForegroundColor Gray
Write-Host "  📁 Results:      $resultsDir/" -ForegroundColor Gray
Write-Host "  📁 Ground Truth: $groundTruthDir/" -ForegroundColor Gray

Write-Host "`nNext Steps:" -ForegroundColor Cyan
Write-Host "  1. Review SRT captions:" -ForegroundColor Gray
Write-Host "     Get-Content results/*.srt" -ForegroundColor Yellow
Write-Host "`n  2. View detailed reports:" -ForegroundColor Gray
Write-Host "     Open results/*_report.html in browser" -ForegroundColor Yellow
Write-Host "`n  3. View event data:" -ForegroundColor Gray
Write-Host "     streamlit run streamlit_app.py" -ForegroundColor Yellow
Write-Host "     Then enter: results/demo_video_events.json" -ForegroundColor Yellow
Write-Host "`n  4. Improve annotations:" -ForegroundColor Gray
Write-Host "     Edit ground_truth/*_ground_truth.csv" -ForegroundColor Yellow
Write-Host "     Then re-run evaluation" -ForegroundColor Yellow

if ($Dashboard) {
    Write-Host "`n🚀 Starting dashboard..." -ForegroundColor Green
    streamlit run streamlit_app.py
}
