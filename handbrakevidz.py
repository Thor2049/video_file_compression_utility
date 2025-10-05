#!/usr/bin/env python3
import os
import time
import subprocess
import logging
import re
import argparse
import json
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)
# State files for web interface
STATE_DIR = Path(__file__).parent / 'state'
STATE_DIR.mkdir(exist_ok=True)

QUEUE_FILE = STATE_DIR / 'queue.json'
CURRENT_FILE = STATE_DIR / 'current.json'
COMPLETED_FILE = STATE_DIR / 'completed.json'
ERRORS_FILE = STATE_DIR / 'errors.json'


class StateManager:
    """Manages state files for web interface communication"""
    
    @staticmethod
    def load_json(file_path):
        """Load JSON file, return empty list if not exists"""
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
        return []
    
    @staticmethod
    def save_json(file_path, data):
        """Save data to JSON file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving {file_path}: {e}")
    
    @staticmethod
    def add_to_queue(file_path):
        """Add file to processing queue"""
        queue = StateManager.load_json(QUEUE_FILE)
        queue.append({
            'path': str(file_path),
            'added': datetime.now().isoformat()
        })
        StateManager.save_json(QUEUE_FILE, queue)
    
    @staticmethod
    def remove_from_queue(file_path):
        """Remove file from queue"""
        queue = StateManager.load_json(QUEUE_FILE)
        queue = [item for item in queue if item['path'] != str(file_path)]
        StateManager.save_json(QUEUE_FILE, queue)
    
    @staticmethod
    def set_current(file_path, progress=0, eta='Unknown'):
        """Update current processing file"""
        current = {
            'path': str(file_path),
            'progress': progress,
            'eta': eta,
            'started': datetime.now().isoformat()
        }
        StateManager.save_json(CURRENT_FILE, current)
    
    @staticmethod
    def clear_current():
        """Clear current processing file"""
        StateManager.save_json(CURRENT_FILE, {})
    
    @staticmethod
    def add_completed(file_path, output_path, original_size, compressed_size):
        """Add to completed list"""
        completed = StateManager.load_json(COMPLETED_FILE)
        completed.append({
            'input': str(file_path),
            'output': str(output_path),
            'original_size_mb': round(original_size / (1024*1024), 2),
            'compressed_size_mb': round(compressed_size / (1024*1024), 2),
            'completed': datetime.now().isoformat()
        })
        StateManager.save_json(COMPLETED_FILE, completed)
    
    @staticmethod
    def add_error(file_path, reason):
        """Add to errors list"""
        errors = StateManager.load_json(ERRORS_FILE)
        errors.append({
            'path': str(file_path),
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        })
        StateManager.save_json(ERRORS_FILE, errors)


class VideoFolderHandler(FileSystemEventHandler):
    def __init__(self, watch_dir, handbrake_path, processed_folders=None):
        self.watch_dir = Path(watch_dir)
        self.handbrake_path = handbrake_path
        self.processed_folders = processed_folders or set()
        
        # Process any existing folders that might not have been processed yet
        self.scan_existing_folders()
    
    def scan_existing_folders(self):
        """Scan for existing folders that might need processing"""
        logger.info(f"Scanning for existing folders in {self.watch_dir}")
        for item in os.listdir(self.watch_dir):
            item_path = self.watch_dir / item
            if item_path.is_dir() and item not in self.processed_folders:
                self.process_folder(item_path)
    
    def on_created(self, event):
        """Handle folder creation events"""
        if not event.is_directory:
            return
        
        folder_path = Path(event.src_path)
        if folder_path.parent == self.watch_dir:
            logger.info(f"New folder detected: {folder_path}")
            # Wait a bit to make sure all files are transferred
            time.sleep(5)
            self.process_folder(folder_path)
    
    def process_folder(self, folder_path):
        """Process a newly created folder for video files"""
        folder_name = folder_path.name
        
        # Skip if already processed
        if folder_name in self.processed_folders:
            logger.info(f"Folder {folder_name} already processed, skipping")
            return
        
        logger.info(f"Processing folder: {folder_name}")
        video_files = self.find_video_files(folder_path)
        
        if not video_files:
            logger.info(f"No file found matching the required suffix in {folder_path}. Skipping.")
            StateManager.add_error(str(folder_path), "No files with required suffix found")
            return
        
        # Add all files to queue
        for video_file in video_files:
            StateManager.add_to_queue(video_file)
        
        # Process each video file
        for video_file in video_files:
            self.compress_video(video_file)
    
    def is_valid_suffix(self, filename):
        """
        Check if filename has valid suffix pattern.
        Pattern: 1-2 spaces followed by 'xx' or 'XX' before extension
        Supports: .mp4, .mkv, .avi, .wmv
        Examples: "file xx.mp4", "file  XX.mkv", "video  xx.avi"
        """
        pattern = r'[\s]{1,2}[xX]{2}\.(mp4|mkv|avi|wmv)$'
        return bool(re.search(pattern, filename))
    
    def find_video_files(self, folder_path):
        """Find video files with required suffix in the folder"""
        video_files = []
        
        for root, _, files in os.walk(folder_path):
            for file in files:
                # Check if file has valid suffix
                if self.is_valid_suffix(file):
                    video_files.append(Path(root) / file)
                elif file.lower().endswith(('.mp4', '.mkv', '.avi', '.wmv')):
                    # Log files that have video extensions but wrong suffix
                    logger.warning(f"Skipping '{file}' - missing required suffix pattern")
        
        return video_files
    
    def get_video_resolution(self, video_path):
        """
        Use ffprobe to get the vertical resolution of the video.
        Returns height in pixels (e.g., 480, 720, 1080)
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=height',
                '-of', 'csv=p=0',
                str(video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            height = int(result.stdout.strip())
            logger.info(f"Detected resolution: {height}p for {video_path.name}")
            return height
        except subprocess.CalledProcessError as e:
            logger.error(f"ffprobe error: {e}")
            logger.error(f"Error output: {e.stderr}")
            return None
        except ValueError as e:
            logger.error(f"Could not parse resolution: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error detecting resolution: {e}")
            return None
    
    def compress_video(self, video_path):
        """Compress a video file using HandbrakeCLI with NVEnc H.265"""
        # Remove from queue
        StateManager.remove_from_queue(video_path)
        
        # Set as current
        StateManager.set_current(video_path, progress=0)
        
        file_name = video_path.name
        
        # Extract new filename by removing the suffix pattern
        # Match 1-2 spaces followed by xx/XX before extension
        new_file_name = re.sub(r'[\s]{1,2}[xX]{2}\.', '.', file_name)
        
        # Use .mp4 as output extension regardless of input
        output_file_name = Path(new_file_name).stem + '.mp4'
        output_path = video_path.parent / output_file_name
        
        # Check if output already exists to prevent overwrite
        if output_path.exists():
            logger.warning(f"Output file already exists: {output_path}. Skipping to prevent overwrite.")
            StateManager.add_error(str(video_path), "Output file already exists")
            StateManager.clear_current()
            return False
        
        # Get original file size
        original_size = video_path.stat().st_size
        
        # Log the full paths for debugging
        logger.info(f"Input file path: {video_path}")
        logger.info(f"Output file path: {output_path}")
        logger.info(f"Compressing: {file_name} -> {output_file_name}")
        
        # Detect source resolution
        source_height = self.get_video_resolution(video_path)
        
        # Determine if we should downscale
        # If resolution is 540p or lower, keep original resolution
        should_downscale = True
        if source_height is not None and source_height <= 540:
            should_downscale = False
            logger.info(f"Source resolution ({source_height}p) is ≤540p, keeping original resolution")
        else:
            logger.info(f"Source resolution is >540p or unknown, downscaling to 480p")
        
        # Build HandbrakeCLI command
        cmd = [
            self.handbrake_path,
            '-i', str(video_path),
            '-o', str(output_path),
            '--preset-import-file', 'none',  # Prevent loading user presets
            '-e', 'nvenc_h265',  # Use NVEnc H.265 encoder
            '-q', '22',  # Quality setting
        ]
        
        # Add resolution settings
        if should_downscale:
            cmd.extend(['--height', '480'])  # Downscale to 480p
        
        # Add common settings
        cmd.extend([
            '--keep-display-aspect',  # Maintain aspect ratio
            '-O',  # Optimize for web
            '--all-audio',  # Keep all audio tracks
            '--all-subtitles',  # Keep all subtitle tracks
            '--copy-timestamps',  # Preserve timestamps
            '--native-language', 'eng',  # Set native language
            '--non-anamorphic',  # Disable anamorphic
        ])
        
        try:
            logger.info(f"Running command: {' '.join(str(c) for c in cmd)}")
            
            # Update progress
            StateManager.set_current(video_path, progress=10, eta='Calculating...')
            
            # Use shell=True on Windows to help with permissions
            if os.name == 'nt':  # Windows
                # Join the command as a string for Windows
                handbrake_exe = f'"{self.handbrake_path}"'
                input_file = f'"{video_path}"' 
                output_file = f'"{output_path}"'
                
                # Build command string
                command_parts = [
                    handbrake_exe,
                    '-i', input_file,
                    '-o', output_file,
                    '-e nvenc_h265',
                    '-q 22'
                ]
                
                if should_downscale:
                    command_parts.append('--height 480')
                
                command_parts.extend([
                    '--keep-display-aspect',
                    '-O',
                    '--all-audio',
                    '--all-subtitles',
                    '--native-language eng',
                    '--non-anamorphic'
                ])
                
                command_str = ' '.join(command_parts)
                logger.info(f"Windows command: {command_str}")
                
                # Run with more explicit output handling
                process = subprocess.Popen(
                    command_str, 
                    shell=True, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    text=True
                )
                
                # Print output in real-time and update progress
                logger.info("HandbrakeCLI is running. This may take a while...")
                
                # Simulate progress updates (HandbrakeCLI doesn't provide easy progress)
                for progress in range(20, 90, 10):
                    if process.poll() is not None:
                        break
                    time.sleep(5)
                    StateManager.set_current(video_path, progress=progress, eta='Processing...')
                
                stdout, stderr = process.communicate()
                
                if stdout:
                    logger.info(f"Command output: {stdout}")
                if stderr:
                    logger.error(f"Command error output: {stderr}")
                    
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, command_str)
            else:
                # Unix/Linux
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                if result.stdout:
                    logger.info(f"Command output: {result.stdout}")
            
            # Update to completion
            StateManager.set_current(video_path, progress=95, eta='Finalizing...')
            
            # Verify the output file exists
            if output_path.exists():
                compressed_size = output_path.stat().st_size
                logger.info(f"Successfully created output file: {output_path}")
                logger.info(f"Original size: {original_size / (1024*1024):.2f} MB")
                logger.info(f"Compressed size: {compressed_size / (1024*1024):.2f} MB")
                
                # Add to completed
                StateManager.add_completed(video_path, output_path, original_size, compressed_size)
                StateManager.clear_current()
            else:
                logger.error(f"Output file was not created at: {output_path}")
                StateManager.add_error(str(video_path), "Output file not created")
                StateManager.clear_current()
                return False
                
            logger.info(f"Compression completed for {file_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"HandbrakeCLI error: {e}")
            if hasattr(e, 'stderr') and e.stderr:
                logger.error(f"Error output: {e.stderr}")
            StateManager.add_error(str(video_path), f"HandbrakeCLI error: {str(e)}")
            StateManager.clear_current()
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            StateManager.add_error(str(video_path), f"Unexpected error: {str(e)}")
            StateManager.clear_current()
            return False

def main():
    parser = argparse.ArgumentParser(
        description='Monitor a folder for new folders with video files and compress them using HandbrakeCLI with NVEnc H.265'
    )
    parser.add_argument('--watch', required=True, help='Directory to watch for new folders')
    parser.add_argument('--handbrake', default='HandBrakeCLI', 
                       help='Path to HandbrakeCLI executable (default assumes it is in PATH)')
    args = parser.parse_args()
    
    # Full path to HandbrakeCLI executable
    handbrake_path = args.handbrake
    
    # Verify HandbrakeCLI is accessible
    try:
        test_cmd = [handbrake_path, '--version']
        result = subprocess.run(test_cmd, capture_output=True, text=True)
        logger.info(f"HandbrakeCLI version: {result.stdout.strip()}")
    except Exception as e:
        logger.error(f"Error accessing HandbrakeCLI: {str(e)}")
        logger.error("Please make sure the path is correct and you have permission to execute it.")
        logger.error("Try running this script as administrator or with elevated privileges.")
        return 1
    
    # Verify ffprobe is accessible (for resolution detection)
    try:
        test_cmd = ['ffprobe', '-version']
        result = subprocess.run(test_cmd, capture_output=True, text=True)
        logger.info(f"ffprobe is available: {result.stdout.split()[0]}")
    except Exception as e:
        logger.error(f"Error accessing ffprobe: {str(e)}")
        logger.error("ffprobe is required for resolution detection. Please install ffmpeg.")
        return 1
    
    watch_dir = Path(args.watch).resolve()
    
    if not watch_dir.exists() or not watch_dir.is_dir():
        logger.error(f"Watch directory does not exist: {watch_dir}")
        return 1
    
    logger.info(f"Starting to monitor: {watch_dir}")
    logger.info(f"Output will be saved to the same directories as source files")
    logger.info(f"State files for web interface: {STATE_DIR}")
    
    # Create event handler and observer
    event_handler = VideoFolderHandler(watch_dir, handbrake_path)
    observer = Observer()
    observer.schedule(event_handler, str(watch_dir), recursive=False)
    observer.start()
    
    try:
        logger.info("Monitoring started. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user.")
        observer.stop()
    
    observer.join()
    logger.info("Script terminated gracefully.")
    return 0


if __name__ == "__main__":
    exit(main())