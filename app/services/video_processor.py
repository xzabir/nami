"""
Video Processing Module

Streams a video from any source (YouTube, Facebook, local device, direct url)
WITHOUT downloading it entirely to disk. It applies duration checks first, and if valid,
extracts frames on the fly at a specific rate (e.g. 1 frame per second).
"""
import base64
import logging
import os
import re
from typing import List, Optional, Tuple

import cv2

from app.config import settings

logger = logging.getLogger("video_processor")


class VideoProcessingError(Exception):
    pass


# ---------------------------------------------------------------------------
# URL and Stream Checkers
# ---------------------------------------------------------------------------
def _is_social_media(url: str) -> bool:
    """Check if URL is from a known social media site supported by yt-dlp."""
    pattern = re.compile(
        r"(youtube\.com|youtu\.be|facebook\.com|fb\.watch|instagram\.com|tiktok\.com|twitter\.com|x\.com|vimeo\.com)",
        re.IGNORECASE,
    )
    return bool(pattern.search(url))


def _get_social_media_stream_url(url: str) -> Tuple[str, Optional[float]]:
    """Uses yt-dlp to extract the direct stream URL and duration WITHOUT downloading."""
    try:
        import yt_dlp
    except ImportError as exc:
        raise VideoProcessingError("yt-dlp is not installed. Run: pip install yt-dlp") from exc

    ydl_opts = {
        "format": "best[height<=720][ext=mp4]/best[height<=720]/best[ext=mp4]/best",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            stream_url = info.get("url")
            if not stream_url:
                raise VideoProcessingError(f"Could not extract a direct stream URL from {url}")
            
            # yt-dlp usually knows the duration without needing to open the file
            duration = info.get("duration") 
            return stream_url, float(duration) if duration else None
            
    except Exception as exc:
        raise VideoProcessingError(f"yt-dlp failed to extract info from '{url}': {exc}") from exc


def _check_duration_bounds(duration: float, source: str):
    """Raises an error if duration is outside the accepted window."""
    min_sec = settings.min_video_seconds
    max_sec = settings.max_video_seconds
    if duration < min_sec:
        raise VideoProcessingError(f"Video is too short ({duration:.1f}s < {min_sec}s minimum). Source: {source}")
    if duration > max_sec:
        raise VideoProcessingError(f"Video is too long ({duration:.1f}s > {max_sec}s maximum). Source: {source}")


# ---------------------------------------------------------------------------
# Direct Stream Extraction (No Downloading)
# ---------------------------------------------------------------------------
def _extract_frames_from_stream(stream_url: str, source_name: str, known_duration: Optional[float] = None) -> List[str]:
    """
    Opens a video stream, checks duration (if not already known), and reads exactly 
    1 frame per second sequentially. This prevents having to download the file to disk.
    """
    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        raise VideoProcessingError(f"OpenCV could not open video stream: {source_name}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # 1. Apply duration check FIRST (if yt-dlp didn't already give it to us)
    if not known_duration:
        if total_frames <= 0 or fps <= 0:
            cap.release()
            raise VideoProcessingError(f"Cannot determine duration for: {source_name}")
        
        known_duration = total_frames / fps
        _check_duration_bounds(known_duration, source_name)
    else:
        # We already validated it before opening the stream, but we still need total_frames
        if total_frames <= 0 and fps > 0:
            total_frames = int(known_duration * fps)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    logger.info(
        "Stream opened: %s | duration=%.1fs fps=%.1f resolution=%dx%d",
        source_name, known_duration, fps, width, height,
    )

    if width == 0 or height == 0:
        cap.release()
        raise VideoProcessingError(f"Video has zero-dimension frames: {source_name}")

    # 2. Extract frames sequentially at exactly `frames_per_second` (e.g. 1 FPS)
    frames_per_second = settings.frames_per_second
    n_frames_to_extract = int(known_duration * frames_per_second)
    if n_frames_to_extract == 0:
        n_frames_to_extract = 1

    frames_b64: List[str] = []
    skipped_green = 0

    # Calculate how many frames to skip in the stream to hit 1 FPS
    # For a 30 FPS video, we want to grab 1 frame, skip 29, grab 1, skip 29.
    frames_to_skip = int(fps / frames_per_second)
    if frames_to_skip <= 0:
        frames_to_skip = 1

    current_frame_idx = 0
    extracted_count = 0

    while extracted_count < n_frames_to_extract:
        # Instead of using CAP_PROP_POS_FRAMES (which is broken on many network streams),
        # we sequentially grab frames, decoding only the ones we need.
        ret = cap.grab()
        if not ret:
            break
            
        if current_frame_idx % frames_to_skip == 0:
            ret, frame = cap.retrieve()
            if ret and frame is not None:
                # Green-frame sanity check
                mean_b, mean_g, mean_r = frame.mean(axis=(0, 1))
                if mean_g > 200 and mean_r < 30 and mean_b < 30:
                    logger.warning("Frame %d is pure green — skipping", current_frame_idx)
                    skipped_green += 1
                else:
                    # Resize to <=512 px wide for token efficiency
                    h, w = frame.shape[:2]
                    if w > 512:
                        scale = 512.0 / w
                        frame = cv2.resize(frame, (512, int(h * scale)), interpolation=cv2.INTER_AREA)

                    ret2, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, settings.frame_jpeg_quality])
                    if ret2:
                        frames_b64.append(base64.b64encode(buf.tobytes()).decode("utf-8"))
                        extracted_count += 1
                        
        current_frame_idx += 1

    cap.release()

    if skipped_green:
        logger.warning("%d frames were pure green — check stream integrity.", skipped_green)
    
    if not frames_b64:
        raise VideoProcessingError(f"No usable frames extracted from stream: {source_name}")

    logger.info("Extracted %d usable frames from stream %s", len(frames_b64), source_name)
    return frames_b64


# ---------------------------------------------------------------------------
# Public Entry Point
# ---------------------------------------------------------------------------
def extract_frames_b64(video_source: str) -> List[str]:
    """
    Main router for video processing.
    1. Check duration FIRST (without downloading).
    2. Stream the video directly from the URL.
    3. Extract exactly 1 FPS.
    """
    # Clean up the input: strip spaces from the URL, or extract the URL if the user pasted a sentence
    video_source = re.sub(r'\s+', '', video_source)
    if "http" in video_source and not video_source.startswith("http"):
        # If they pasted "Error: https://..." extract the URL part
        match = re.search(r'(https?://[^\s]+)', video_source)
        if match:
            video_source = match.group(1)

    if os.path.exists(video_source):
        # Local file
        logger.info("Processing local video: %s", video_source)
        return _extract_frames_from_stream(video_source, video_source, known_duration=None)
        
    elif _is_social_media(video_source):
        # Social media: fetch metadata first to check duration without downloading
        logger.info("Fetching metadata for social media URL: %s", video_source)
        stream_url, duration = _get_social_media_stream_url(video_source)
        
        if duration:
            # Apply duration check BEFORE we even attempt to stream the video frames
            _check_duration_bounds(duration, video_source)
            logger.info("Duration check passed (%.1fs). Streaming frames...", duration)
        
        return _extract_frames_from_stream(stream_url, video_source, known_duration=duration)
        
    elif video_source.startswith("http"):
        # Direct URL (e.g. AWS S3, personal storage).
        # We pass it directly to OpenCV, which reads the network header to get duration first.
        logger.info("Processing direct URL stream: %s", video_source)
        return _extract_frames_from_stream(video_source, video_source, known_duration=None)
        
    else:
        raise VideoProcessingError(f"Cannot process source: {video_source}")
