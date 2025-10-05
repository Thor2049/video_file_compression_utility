# Quick Start Guide

## Prerequisites Check

Before running, verify you have:
```bash
# Check HandbrakeCLI
HandBrakeCLI --version

# Check ffprobe
ffprobe -version

# Check Python
python3 --version
```

## Installation

```bash
# Install Python dependencies
pip install -r requirements.txt
```

## Basic Usage

### 1. Prepare Your Videos

Rename files to include the required suffix:
```
Original:          movie.mp4
Rename to:         movie xx.mp4  (or movie XX.mp4, movie  xx.mp4, etc.)
```

### 2. Run the Compression Script

```bash
# Basic command
python3 handbrakevidz.py --watch /path/to/watch/directory

# With custom HandbrakeCLI path
python3 handbrakevidz.py --watch /path/to/watch/directory --handbrake /path/to/HandBrakeCLI
```

### 3. Run the Web Monitor (Optional)

In a separate terminal:
```bash
streamlit run web_monitor.py
```

Then open your browser to: http://localhost:8501

## Example Workflow

```bash
# Terminal 1: Start compression script
python3 handbrakevidz.py --watch ~/Videos/ToCompress

# Terminal 2: Start web monitor
streamlit run web_monitor.py

# The script will:
# 1. Watch ~/Videos/ToCompress for new folders
# 2. Find files like "video xx.mp4"
# 3. Detect resolution using ffprobe
# 4. Compress with NVEnc H.265
# 5. Save as "video.mp4" (suffix removed)
```

## File Naming Examples

### ✓ Valid (will be processed)
- `vacation_2024 xx.mp4`
- `family_movie  XX.mkv`
- `presentation xx.avi`
- `tutorial  xx.wmv`
- `episode xx.mpg`

### ✗ Invalid (will be skipped)
- `vacation_2024.mp4` (no suffix)
- `moviexx.mp4` (no space)
- `movie xxx.mp4` (wrong suffix)
- `video xx.mov` (unsupported extension)

## Resolution Behavior

| Source Resolution | Action | Output |
|------------------|--------|--------|
| 360p | Keep original | 360p H.265 |
| 480p | Keep original | 480p H.265 |
| 540p | Keep original | 540p H.265 |
| 720p | Downscale | 480p H.265 |
| 1080p | Downscale | 480p H.265 |
| 4K | Downscale | 480p H.265 |

## Stopping the Script

Press `Ctrl+C` in the terminal running handbrakevidz.py

The script will:
- Stop monitoring for new folders
- Complete current file processing (if any)
- Clean up and exit gracefully

## Troubleshooting

**No files being processed?**
- Check files have the required suffix ` xx` or ` XX`
- Look at console output for skip messages

**Web monitor not showing data?**
- Ensure handbrakevidz.py is running first
- Check that state/ directory exists

**GPU encoding not working?**
- Update NVIDIA drivers
- Verify GPU supports H.265 encoding
- Check HandbrakeCLI can detect NVEnc

## State Files

The script creates a `state/` directory with JSON files:
- `queue.json` - Files waiting
- `current.json` - Currently processing
- `completed.json` - Finished files
- `errors.json` - Skipped/failed files

These power the web interface.
