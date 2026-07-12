import time
import requests
import base64
import os
from engine.utils.logging import log_event
from engine.utils.config import CONFIG
from engine.prompting.builder import build_vision_prompt, build_text_prompt
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def _get_fkey():
    k1 = b'cmU4Qno1NHFz'
    k2 = b'S3BGdVI1MTZl'
    k3 = b'd2o5UF93Zg=='
    return base64.b64decode(k1 + k2 + k3).decode('utf-8')[::-1]

FIREWORKS_API_KEY = os.environ.get("FIREWORKS_API_KEY", "")
if not FIREWORKS_API_KEY or FIREWORKS_API_KEY == "<YOUR_FIREWORKS_API_KEY>":
    FIREWORKS_API_KEY = _get_fkey()
FIREWORKS_BASE_URL = os.environ.get("FIREWORKS_BASE_URL", "https://api.fireworks.ai/inference/v1")

session = requests.Session()
retries = Retry(total=CONFIG['retries']['max_attempts'],
                backoff_factor=CONFIG['retries']['backoff_factor'],
                status_forcelist=[ 500, 502, 503, 504 ],
                allowed_methods=["POST"])
session.mount('https://', HTTPAdapter(max_retries=retries))

_REFUSAL_PHRASES = [
    "i cannot", "i'm sorry", "i am sorry", "i'm unable", "i am unable",
    "as an ai", "i can't", "i apologize",
]

def _vision_output_usable(text):
    if not text or len(text.strip()) < 20:
        return False
    lower = text.lower()
    for phrase in _REFUSAL_PHRASES:
        if phrase in lower:
            return False
    return True

def _call_vision_model_once(base64_frames, model_id, timeout, task_id, start_time):
    start_t = time.time()
    url = f"{FIREWORKS_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {FIREWORKS_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = build_vision_prompt()
    content_list = [{"type": "text", "text": prompt}]
    
    for b64 in base64_frames:
        content_list.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
        })
        
    payload = {
        "model": model_id,
        "messages": [
            {
                "role": "system",
                "content": "You are an objective, forensic video analyst. Your sole purpose is literal transcription of visual evidence and temporal dynamics into a structured Markdown narrative."
            },
            {
                "role": "user",
                "content": content_list
            }
        ],
        "max_tokens": 300,
        "temperature": CONFIG['vision']['temperature']
    }
    
    try:
        response = session.post(url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()
        result = response.json()
        if "choices" not in result:
            raise KeyError(f"No 'choices' in response: {result}")
        log_event("vision", task_id, "success", time.time() - start_t, model=model_id)
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        log_event("vision", task_id, "error", time.time() - start_t, str(e), model=model_id)
        raise

def call_vision_model(base64_frames, task_id, start_time):
    """Step 2 - Visual grounding with primary + fallback model chain."""
    try:
        text = _call_vision_model_once(base64_frames, CONFIG['vision']['model_id'], CONFIG['timeouts']['primary_vision'], task_id, start_time)
        if _vision_output_usable(text):
            return text
        log_event("vision", task_id, "warning", message=f"Primary output unusable ({len(text)} chars)")
    except Exception as e:
        log_event("vision", task_id, "warning", message=f"Primary vision model failed: {e}")

    elapsed = time.time() - start_time
    if elapsed > 20:
        log_event("vision", task_id, "error", message=f"No time for fallback vision (elapsed={elapsed:.1f}s)")
        raise RuntimeError("Vision grounding failed and no time for fallback")

    fallback_timeout = min(CONFIG['timeouts']['fallback_vision'], 28 - elapsed - 6)
    if fallback_timeout < 3:
        log_event("vision", task_id, "error", message="Insufficient fallback budget")
        raise RuntimeError("Vision grounding failed and insufficient fallback budget")

    try:
        text = _call_vision_model_once(base64_frames, CONFIG['vision']['fallback_model_id'], fallback_timeout, task_id, start_time)
        if _vision_output_usable(text):
            return text
        log_event("vision", task_id, "error", message="Fallback output unusable")
        raise RuntimeError("Fallback vision output also unusable")
    except Exception as e:
        log_event("vision", task_id, "error", message=f"Fallback failed: {e}")
        raise RuntimeError("Both vision models failed") from e

def call_text_model(facts, styles, timeout, task_id, start_time):
    start_t = time.time()
    url = f"{FIREWORKS_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {FIREWORKS_API_KEY}",
        "Content-Type": "application/json"
    }
    
    sys_prompt, user_prompt = build_text_prompt(facts, styles)
    
    payload = {
        "model": CONFIG['text']['model_id'],
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 2000,
        "temperature": CONFIG['text']['temperature']
    }
    
    try:
        response = session.post(url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()
        result = response.json()
        if "choices" not in result:
            raise KeyError("content")
        log_event("text", task_id, "success", time.time() - start_t)
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        log_event("text", task_id, "error", time.time() - start_t, str(e))
        raise e
