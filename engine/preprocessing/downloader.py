import os
import requests
import tempfile
import time
from engine.utils.logging import log_event
from engine.utils.config import CONFIG

def download_video(video_url, task_id, start_time):
    """Download video locally to prevent ffmpeg network stalls."""
    start_t = time.time()
    try:
        # Create a temp file that persists until we delete it
        fd, temp_path = tempfile.mkstemp(suffix=".mp4")
        os.close(fd)
        
        # We use a 10 second timeout for the download
        response = requests.get(video_url, stream=True, timeout=10)
        response.raise_for_status()
        
        with open(temp_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        log_event("download", task_id, "success", time.time() - start_t)
        return temp_path
    except Exception as e:
        log_event("download", task_id, "error", time.time() - start_t, str(e))
        raise ValueError(f"Failed to download video: {e}")
