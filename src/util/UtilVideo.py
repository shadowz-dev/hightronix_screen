import struct
import subprocess
import json
import logging
import os
from typing import Optional
from moviepy.editor import VideoFileClip

"""
def mp4_duration_with_ffprobe(filename):
    import subprocess, json

    result = subprocess.check_output(
            f'ffprobe -v quiet -show_streams -select_streams v:0 -of json "{filename}"',
            shell=True).decode()
    fields = json.loads(result)['streams'][0]

    if 'tags' in fields and 'DURATION' in fields['tags']:
        return round(float(fields['tags']['DURATION']), 2)

    if 'duration' in fields:
        return round(float(fields['duration']), 2)

    return 0
"""
def get_video_duration_with_moviepy(file_path: str) -> Optional[float]:

    # Ensure the file path is absolute
    file_path = os.path.abspath(file_path)
    
    # Check if the file exists
    if not os.path.isfile(file_path):
        logging.error(f"File not found: {file_path}")
        return None

    try:
        # Load the video file using moviepy
        clip = VideoFileClip(file_path)
        duration = clip.duration
        logging.debug(f"Duration for {file_path}: {duration} seconds")
        return duration
    except Exception as e:
        logging.error(f"Error getting duration with moviepy for file {file_path}: {e}")
    return None