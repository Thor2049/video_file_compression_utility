#!/usr/bin/env python3
import os
import time
import subprocess
import logging
import re
import argparse
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
            logger.info(f"No video files found in {folder_name}")
            return
        
        # Process each video file
        for video_file in video_files:
            self.compress_video(video_file)
    
    def find_video_files(self, folder_path):
        """Find video files in the folder with .mp4 or .mkv extensions"""
        video_files = []
        
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(('.mp4', '.mkv')):
                    video_files.append(Path(root) / file)
        
        return video_files
    
    def compress_video(self, video_path):
        """Compress a video file using Handbrake"""
        # Extract the file name and handle different suffix patterns
        file_name = video_path.name
        
        # Check for both " xx." and "  xx." patterns
        if " xx." in file_name:
            new_file_name = file_name.replace(" xx.", ".")
        elif "  xx." in file_name:
            new_file_name = file_name.replace("  xx.", ".")
        else:
            # If no match, just use the original name but ensure mp4 extension
            new_file_name = file_name
            
        # Use .mp4 as output extension regardless of input
        output_file_name = Path(new_file_name).stem + '.mp4'
        output_path = video_path.parent / output_file_name
        
        # Log the full paths for debugging
        logger.info(f"Input file path: {video_path}")
        logger.info(f"Output file path: {output_path}")
        
        logger.info(f"Compressing: {file_name} -> {output_file_name}")
        
        # Build HandbrakeCLI command
        cmd = [
            self.handbrake_path,
            '-i', str(video_path),
            '-o', str(output_path),
            '--preset-import-file', 'none',  # Prevent loading user presets
            '-e', 'nvenc_h265',  # Use NVEnc H.265 encoder
            '-q', '22',  # Quality setting
            '--height', '480',  # Set maximum height to 480p
            '--keep-display-aspect',  # Maintain aspect ratio
            '-O',  # Optimize for web
            '--all-audio',  # Keep all audio tracks
            '--all-subtitles',  # Keep all subtitle tracks
            '--copy-timestamps',  # Preserve timestamps
            '--native-language', 'eng',  # Set native language
            '--non-anamorphic',  # Disable anamorphic
        ]
        
        try:
            logger.info(f"Running command: {' '.join(str(c) for c in cmd)}")
            
            # Use shell=True on Windows to help with permissions
            if os.name == 'nt':  # Windows
                # Join the command as a string for Windows
                handbrake_exe = f'"{self.handbrake_path}"'
                input_file = f'"{video_path}"' 
                output_file = f'"{output_path}"'
                
                # Execute the command with proper quoting and NVEnc encoder
                command_str = f'{handbrake_exe} -i {input_file} -o {output_file} -e nvenc_h265 -q 22 --height 480 --keep-display-aspect -O --all-audio --all-subtitles --native-language eng --non-anamorphic'
                logger.info(f"Windows command: {command_str}")
                
                # Run with more explicit output handling
                process = subprocess.Popen(command_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                # Print output in real-time
                logger.info("HandbrakeCLI is running. This may take a while...")
                stdout, stderr = process.communicate()
                
                if stdout:
                    logger.info(f"Command output: {stdout}")
                if stderr:
                    logger.error(f"Command error output: {stderr}")
                    
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, command_str)
            else:
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                if result.stdout:
                    logger.info(f"Command output: {result.stdout}")
            
            # Verify the output file exists
            if output_path.exists():
                logger.info(f"Successfully created output file: {output_path}")
                file_size = output_path.stat().st_size
                logger.info(f"Output file size: {file_size / (1024*1024):.2f} MB")
            else:
                logger.error(f"Output file was not created at: {output_path}")
                
            logger.info(f"Compression completed for {file_name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"HandbrakeCLI error: {e}")
            logger.error(f"Error output: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Monitor a folder for new folders with video files and compress them using HandbrakeCLI')
    parser.add_argument('--watch', required=True, help='Directory to watch for new folders')
    parser.add_argument('--handbrake', default='HandBrakeCLI', help='Path to HandbrakeCLI executable (default assumes it is in PATH)')
    args = parser.parse_args()
    
    # Full path to HandbrakeCLI executable
    handbrake_path = args.handbrake
    
    # Verify HandbrakeCLI is accessible
    try:
        # Basic test command to check if HandbrakeCLI is accessible
        test_cmd = [handbrake_path, '--version']
        result = subprocess.run(test_cmd, capture_output=True, text=True)
        logger.info(f"HandbrakeCLI version: {result.stdout.strip()}")
    except Exception as e:
        logger.error(f"Error accessing HandbrakeCLI: {str(e)}")
        logger.error("Please make sure the path is correct and you have permission to execute it.")
        logger.error("Try running this script as administrator or with elevated privileges.")
        return 1
    
    watch_dir = Path(args.watch).resolve()
    
    if not watch_dir.exists() or not watch_dir.is_dir():
        logger.error(f"Watch directory does not exist: {watch_dir}")
        return 1
    
    logger.info(f"Starting to monitor: {watch_dir}")
    logger.info("Output will be saved to the same directories as source files")
    
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
    return 0

if __name__ == "__main__":
    exit(main())