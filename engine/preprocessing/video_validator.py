import subprocess
import time
from engine.utils.logging import log_event
from engine.utils.config import CONFIG

def get_video_duration(video_url, task_id, start_time):
    """Step 1a - Check video duration using ffprobe."""
    cmd_duration = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", video_url
    ]
    try:
        duration_str = subprocess.check_output(cmd_duration, text=True, timeout=CONFIG['timeouts']['ffprobe']).strip()
    except subprocess.TimeoutExpired:
        log_event("ffprobe", task_id, "error", time.time() - start_time, "ffprobe timeout")
        raise ValueError("ffprobe timed out reading video_url")
    except Exception as e:
        log_event("ffprobe", task_id, "error", time.time() - start_time, str(e))
        raise ValueError("ffprobe failed")
        
    try:
        duration = float(duration_str)
    except ValueError:
        duration = 1.0
        
    if duration <= 0:
        duration = 1.0
        
    return duration
