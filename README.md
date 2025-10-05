# Video Compression Utility (NVEnc H.265)

Automated video compression tool using HandbrakeCLI with NVIDIA's NVEnc H.265 encoder. Features intelligent resolution handling, real-time web monitoring, and strict file suffix validation to prevent data corruption.

## Features

- **Automated Folder Monitoring**: Watches specified directory for new folders containing video files
- **NVEnc H.265 Encoding**: Hardware-accelerated video compression using NVIDIA GPU
- **Intelligent Resolution Handling**: 
  - Automatically detects source video resolution
  - Preserves original resolution for videos ≤540p
  - Downscales to 480p for videos >540p
- **Strict Suffix Validation**: Only processes files with specific naming patterns to prevent accidental overwrites
- **Multi-Format Support**: Handles .mp4, .mkv, .avi, .wmv, and .mpg files
- **Real-Time Web Interface**: Streamlit dashboard showing queue, progress, completed files, and errors
- **Graceful Shutdown**: Handles Ctrl+C for clean termination

## Supported File Patterns

The script **only** processes video files with the following suffix patterns:

- `filename xx.mp4` (single space + xx)
- `filename  xx.mkv` (double space + xx)
- `filename XX.avi` (uppercase XX)
- `filename  XX.wmv` (any combination of 1-2 spaces + xx/XX case-insensitive)
- `filename xx.mpg` (MPG format support)

**Important**: Files without this suffix pattern will be **skipped** to prevent accidental corruption.

## Prerequisites

### Required Software

1. **HandbrakeCLI**: Command-line interface for video compression
   - Download from: https://handbrake.fr/downloads2.php
   - Ensure it's in your system PATH or note the installation path
   - NVEnc encoder requires NVIDIA GPU with hardware encoding support

2. **FFmpeg (with ffprobe)**: For video resolution detection
   - Download from: https://ffmpeg.org/download.html
   - Ensure `ffprobe` is accessible from command line

3. **Python 3.10+**: Required for running the scripts

4. **NVIDIA GPU Drivers**: Required for NVEnc hardware acceleration
   - Install latest drivers from NVIDIA website
   - Verify GPU supports H.265 encoding

## Installation

### Option 1: Using pip (Virtual Environment)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Option 2: Using Conda

```bash
# Create environment from file
conda env create -f environment.yml

# Activate environment
conda activate video-compression
```

## Usage

### Running the Compression Script

**Basic usage** (HandbrakeCLI in PATH):
```bash
python handbrakevidz.py --watch /path/to/watch/directory
```

**Specifying HandbrakeCLI path**:
```bash
python handbrakevidz.py --watch /path/to/watch/directory --handbrake "/path/to/HandBrakeCLI"
```

**Windows example**:
```bash
python handbrakevidz.py --watch "C:\Videos\ToCompress" --handbrake "C:\Program Files\HandBrake\HandBrakeCLI.exe"
```

**Linux/Mac example**:
```bash
python handbrakevidz.py --watch "/home/user/videos/to_compress" --handbrake "/usr/bin/HandBrakeCLI"
```

### Running the Web Monitor

In a **separate terminal**, run:

```bash
streamlit run web_monitor.py
```

This will open a web browser with the monitoring dashboard at `http://localhost:8501`

The dashboard shows:
- **Current Processing**: File being encoded with progress percentage
- **Queue**: Files waiting to be processed
- **Completed**: Successfully compressed files with size reduction stats
- **Errors/Skipped**: Files that were skipped or failed with reasons

### Stopping the Script

Press `Ctrl+C` in the terminal running `handbrakevidz.py` for graceful shutdown.

## How It Works

1. **Monitoring**: Script watches the specified directory for new folders or existing folders with unprocessed files
2. **File Discovery**: Scans folders for video files matching the required suffix pattern
3. **Resolution Detection**: Uses ffprobe to detect source video resolution
4. **Conditional Processing**:
   - If resolution ≤540p: Keeps original resolution, applies H.265 encoding
   - If resolution >540p: Downscales to 480p, applies H.265 encoding
5. **Output**: Saves compressed video in same folder, removes suffix from filename
   - Example: `my_video xx.mp4` → `my_video.mp4`
6. **State Tracking**: Updates JSON state files for web interface monitoring

## Configuration

### Encoding Settings

Default HandbrakeCLI settings (edit in `handbrakevidz.py` if needed):

```python
'-e', 'nvenc_h265',  # Encoder: NVEnc H.265
'-q', '22',          # Quality: 22 (lower = better quality, larger file)
'--height', '480',   # Target height (when downscaling)
'-O',                # Optimize for web
'--all-audio',       # Keep all audio tracks
'--all-subtitles',   # Keep all subtitle tracks
```

### Supported Video Extensions

Currently supports: `.mp4`, `.mkv`, `.avi`, `.wmv`

To add more, edit the regex pattern in `is_valid_suffix()` method.

## Directory Structure

```
/video_file_compression_utility/
├── handbrakevidz.py        # Main compression script
├── web_monitor.py           # Streamlit web interface
├── requirements.txt         # Python dependencies (pip)
├── environment.yml          # Conda environment specification
├── README.md                # This file
├── LICENSE                  # License file
└── state/                   # Created automatically
    ├── queue.json           # Files waiting to process
    ├── current.json         # Currently processing file
    ├── completed.json       # Successfully completed files
    └── errors.json          # Skipped/failed files
```

## State Files (JSON)

The script creates a `state/` directory with JSON files for monitoring:

- **queue.json**: List of files waiting to be processed
- **current.json**: Current file being processed with progress
- **completed.json**: History of successfully compressed files
- **errors.json**: Log of skipped or failed files with reasons

These files enable the web interface to display real-time status.

## Troubleshooting

### Script won't start

**Issue**: `Error accessing HandbrakeCLI`
- **Solution**: Verify HandbrakeCLI is installed and path is correct
- Test: Run `HandBrakeCLI --version` in terminal

**Issue**: `Error accessing ffprobe`
- **Solution**: Install FFmpeg and ensure ffprobe is in PATH
- Test: Run `ffprobe -version` in terminal

### Files not being processed

**Issue**: "No file found matching the required suffix"
- **Solution**: Files must have ` xx` or ` XX` suffix before extension
- Example: Rename `video.mp4` to `video xx.mp4`

**Issue**: "Output file already exists"
- **Solution**: Delete or move existing output file first
- Example: If `video.mp4` exists, `video xx.mp4` will be skipped

### GPU encoding not working

**Issue**: HandbrakeCLI falling back to software encoding
- **Solution**: 
  1. Update NVIDIA drivers
  2. Verify GPU supports H.265 encoding
  3. Check HandbrakeCLI can access NVIDIA encoder

### Web interface not updating

**Issue**: Dashboard shows old data
- **Solution**: 
  1. Ensure `handbrakevidz.py` is running
  2. Check `state/` directory exists and has JSON files
  3. Refresh browser or restart Streamlit

## Performance Notes

- **NVEnc Encoding**: Much faster than software encoding (10-50x speedup depending on GPU)
- **Resolution Detection**: Adds ~1-2 seconds per file for ffprobe analysis
- **Disk I/O**: Ensure watch directory is on fast storage for better performance
- **Multiple Files**: Processed sequentially, not in parallel

## Security & Safety

- **No Overwrites**: Script validates output file doesn't exist before processing
- **Suffix Validation**: Strict pattern matching prevents processing wrong files
- **Graceful Shutdown**: Ctrl+C stops monitoring without corrupting files
- **Error Logging**: All errors logged to console and `errors.json`

## Known Limitations

- **Progress Tracking**: HandbrakeCLI doesn't provide real-time progress, so web UI shows simulated progress
- **Sequential Processing**: Only one file processed at a time
- **GPU Required**: NVEnc requires compatible NVIDIA GPU
- **Resolution Detection**: Requires ffprobe (part of FFmpeg)

## Contributing

Feel free to submit issues or pull requests for improvements.

## License

See LICENSE file for details.

## Support

For issues or questions:
1. Check this README's Troubleshooting section
2. Verify all prerequisites are installed
3. Check console output for error messages
4. Review `state/errors.json` for processing failures
