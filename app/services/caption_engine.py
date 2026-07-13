"""
Video Captioning Engine

Processes video frames and calls the vision model (Gemma) to generate 
multiple caption styles in a single request.
"""
import json
import logging
import re
import time
from typing import Dict, List, Optional

import httpx

from app.config import settings
from app.services.style_prompts import build_system_prompt, build_user_prompt, STYLE_ORDER
from app.services.video_processor import extract_frames_b64, VideoProcessingError

logger = logging.getLogger("caption_engine")


class CaptionGenerationError(Exception):
    pass
# ---------------------------------------------------------------------------
# Message Builder
# ---------------------------------------------------------------------------
def _build_messages(frames_b64: List[str], styles: List[str]) -> list:
    content = [{"type": "text", "text": build_user_prompt(styles)}]
    for b64 in frames_b64:
        url = b64 if b64.startswith("data:") else f"data:image/jpeg;base64,{b64}"
        content.append({
            "type": "image_url",
            "image_url": {"url": url},
        })
    return [
        {"role": "system", "content": build_system_prompt()},
        {"role": "user", "content": content},
    ]


# ---------------------------------------------------------------------------
# Gemma 4 E4B / Fireworks AI Engine
# ---------------------------------------------------------------------------
def _call_gemma(messages: list) -> str:
    """Calls Gemma via Fireworks AI."""
    if not settings.fireworks_api_key:
        raise CaptionGenerationError("No FIREWORKS_API_KEY set.")

    url = f"{settings.fireworks_base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.fireworks_api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": settings.gemma_model_id,
        "messages": messages,
        # kimi is a reasoning model — it thinks before answering, so it needs more tokens
        "max_tokens": 3000,
        "temperature": 0.7,
    }

    with httpx.Client(timeout=60.0) as client:
        resp = client.post(url, headers=headers, json=body)
        if resp.status_code >= 400:
            raise CaptionGenerationError(f"Fireworks API error {resp.status_code}: {resp.text[:300]}")
        data = resp.json()

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise CaptionGenerationError(f"Unexpected Fireworks response shape: {data}") from exc


# ---------------------------------------------------------------------------
# Output Parsing
# ---------------------------------------------------------------------------
def _parse_captions(raw: str) -> Dict[str, str]:
    cleaned = raw.strip()

    # Strip markdown fences if present
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-z]*\n?", "", cleaned)
        cleaned = re.sub(r"```$", "", cleaned).strip()

    # Try to parse directly first
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        # Model may have wrapped JSON in prose — extract the first JSON object we find
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise CaptionGenerationError(f"No JSON object found in model output: {raw[:300]}")
        try:
            parsed = json.loads(match.group())
        except json.JSONDecodeError as exc:
            raise CaptionGenerationError(f"Model did not return valid JSON: {raw[:300]}") from exc

    missing = [s for s in STYLE_ORDER if s not in parsed]
    if missing:
        raise CaptionGenerationError(f"Missing styles in model output: {missing}")

    return {s: str(parsed[s]).strip() for s in STYLE_ORDER}


# ---------------------------------------------------------------------------
# Public Agent Entry
# ---------------------------------------------------------------------------
def generate_captions(video_url: str, styles: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Extracts frames from the video and generates captions for the specified styles.
    Returns a dictionary mapping style names to the generated text.
    """
    styles = styles or STYLE_ORDER
    start = time.monotonic()

    # Get 1 frame per second
    frames = extract_frames_b64(video_url)

    # Call vision model
    try:
        logger.info("Routing vision task to Fireworks...")
        messages = _build_messages(frames, styles)
        raw = _call_gemma(messages)
        captions = _parse_captions(raw)
        
    except CaptionGenerationError as e:
        logger.warning(f"Analysis failed: {e}. Attempting strict retry...")
        # Stricter retry fallback if the model outputs weird JSON
        messages = _build_messages(frames, styles)
        messages[0]["content"] += "\nReturn ONLY the raw JSON object, nothing else."
        raw = _call_gemma(messages)
        captions = _parse_captions(raw)

    elapsed_ms = (time.monotonic() - start) * 1000
    logger.info("Captioned %s in %.0fms", video_url, elapsed_ms)
    return captions
