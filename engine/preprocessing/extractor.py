import os
import subprocess
import tempfile
import base64
import time
from engine.utils.logging import log_event
from engine.utils.config import CONFIG

def extract_frames(video_url, duration, task_id, start_time):
    """Step 1b - Extract frames from video via ffmpeg network streaming."""
    with tempfile.TemporaryDirectory() as temp_dir:
        duration_float = float(duration)
        cmd_ffmpeg = [
            "ffmpeg", "-y",
            "-i", video_url,
            "-vf", f"fps=16/{duration_float},scale=512:-1",
            "-vframes", "16",
            "-q:v", "2",
            os.path.join(temp_dir, "frame_%03d.jpg")
        ]
        try:
            subprocess.run(
                cmd_ffmpeg, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                check=True, timeout=CONFIG['timeouts']['ffmpeg'],
            )
        except subprocess.TimeoutExpired:
            log_event("ffmpeg", task_id, "error", time.time() - start_time, "ffmpeg timeout")
            raise ValueError("ffmpeg timed out reading video_url")
        except Exception as e:
            log_event("ffmpeg", task_id, "error", time.time() - start_time, str(e))
            raise ValueError("ffmpeg failed")
        
        # Read frames and base64 encode
        base64_frames = []
        frame_files = sorted([f for f in os.listdir(temp_dir)
                              if f.startswith("frame_") and f.endswith(".jpg")])
        for frame_file in frame_files:
            with open(os.path.join(temp_dir, frame_file), "rb") as f:
                b64_str = base64.b64encode(f.read()).decode('utf-8')
                base64_frames.append(b64_str)
                
        if not base64_frames:
            log_event("extraction", task_id, "error", time.time() - start_time, "no frames extracted")
            raise ValueError("Failed to extract any frames.")
            
        log_event("extraction", task_id, "success", time.time() - start_time)
        return base64_frames
