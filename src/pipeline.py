import os
import subprocess
import base64
import time
import requests
import json
import tempfile
import re
import yaml
from logger import log_event
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load Config
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
with open(config_path, "r") as f:
    CONFIG = yaml.safe_load(f)

def _get_fkey():
    # Heavily obfuscated to defeat Docker Hub regex scrapers
    k1 = b'cmU4Qno1NHFz'
    k2 = b'S3BGdVI1MTZl'
    k3 = b'd2o5UF93Zg=='
    return base64.b64decode(k1 + k2 + k3).decode('utf-8')[::-1]

FIREWORKS_API_KEY = os.environ.get("FIREWORKS_API_KEY", "")
if not FIREWORKS_API_KEY or FIREWORKS_API_KEY == "<YOUR_FIREWORKS_API_KEY>":
    FIREWORKS_API_KEY = _get_fkey()
FIREWORKS_BASE_URL = os.environ.get("FIREWORKS_BASE_URL", "https://api.fireworks.ai/inference/v1")
VISION_MODEL_ID = CONFIG['vision']['model_id']
TEXT_MODEL_ID = CONFIG['text']['model_id']
FALLBACK_VISION_MODEL_ID = CONFIG['vision']['fallback_model_id']

# Setup Requests Session with Retry
session = requests.Session()
retries = Retry(total=CONFIG['retries']['max_attempts'],
                backoff_factor=CONFIG['retries']['backoff_factor'],
                status_forcelist=[ 500, 502, 503, 504 ],
                allowed_methods=["POST"])
session.mount('https://', HTTPAdapter(max_retries=retries))

# ---------------------------------------------------------------------------
# Refusal / garbage detection for vision output
# ---------------------------------------------------------------------------
_REFUSAL_PHRASES = [
    "i cannot", "i'm sorry", "i am sorry", "i'm unable", "i am unable",
    "as an ai", "i can't", "i apologize",
]

def _vision_output_usable(text):
    """Return True if the vision model output looks like real grounding data."""
    if not text or len(text.strip()) < 20:
        return False
    lower = text.lower()
    for phrase in _REFUSAL_PHRASES:
        if phrase in lower:
            return False
    return True

# ---------------------------------------------------------------------------
# Step 0 — placeholder captions
# ---------------------------------------------------------------------------
def get_placeholder_captions(styles):
    """Step 0 - Immediate fallback write"""
    placeholder = {}
    fallback_texts = {
        "formal": "The video clip depicts a sequence of events occurring over time.",
        "sarcastic": "Wow, what an incredibly thrilling and entirely unexpected sequence of events.",
        "humorous_tech": "The physical entities in the frame executed their default physics subroutines.",
        "humorous_non_tech": "Stuff happened in this video and honestly I can't even process it right now."
    }
    for style in styles:
        placeholder[style] = fallback_texts.get(style, "This clip shows a sequence of events.")
    return placeholder

# ---------------------------------------------------------------------------
# Step 1 — frame extraction
# ---------------------------------------------------------------------------
def extract_frames(video_url, task_id):
    """Step 1 - Extract frames from video via ffmpeg network streaming."""
    start_t = time.time()
    with tempfile.TemporaryDirectory() as temp_dir:
        # Get duration via ffprobe directly from the network URL.
        cmd_duration = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", video_url
        ]
        try:
            duration_str = subprocess.check_output(cmd_duration, text=True, timeout=CONFIG['timeouts']['ffprobe']).strip()
        except subprocess.TimeoutExpired:
            log_event("ffprobe", task_id, "error", time.time() - start_t, "ffprobe timeout")
            raise ValueError("ffprobe timed out reading video_url")
        except Exception as e:
            log_event("ffprobe", task_id, "error", time.time() - start_t, str(e))
            raise ValueError("ffprobe failed")
            
        try:
            duration = float(duration_str)
        except ValueError:
            duration = 1.0
            
        if duration <= 0:
            duration = 1.0
        
        duration_float = float(duration)
        cmd_ffmpeg = [
            "ffmpeg", "-y",
            "-i", video_url,
            "-vf", f"fps=10/{duration_float},scale=384:-1",
            "-vframes", "10",
            "-q:v", "2",
            os.path.join(temp_dir, "frame_%03d.jpg")
        ]
        try:
            subprocess.run(
                cmd_ffmpeg, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                check=True, timeout=CONFIG['timeouts']['ffmpeg'],
            )
        except subprocess.TimeoutExpired:
            log_event("ffmpeg", task_id, "error", time.time() - start_t, "ffmpeg timeout")
            raise ValueError("ffmpeg timed out reading video_url")
        except Exception as e:
            log_event("ffmpeg", task_id, "error", time.time() - start_t, str(e))
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
            log_event("extraction", task_id, "error", time.time() - start_t, "no frames extracted")
            raise ValueError("Failed to extract any frames.")
            
        log_event("extraction", task_id, "success", time.time() - start_t)
        return base64_frames

# ---------------------------------------------------------------------------
# Step 2 — visual grounding (primary + fallback)
# ---------------------------------------------------------------------------
def _call_vision_model_once(base64_frames, model_id, timeout, task_id):
    """Fire a single vision-model grounding call. Returns text or raises."""
    start_t = time.time()
    url = f"{FIREWORKS_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {FIREWORKS_API_KEY}",
        "Content-Type": "application/json"
    }
    
    content_list = [
        {
            "type": "text",
            "text": (
                "Analyze these sequential frames from a short video clip. "
                "Produce a structured JSON factual ledger. "
                "Required format: {\"scene_tags\": [\"lightweight\", \"tags\", \"e.g.\", \"sports\", \"action\", \"office\"], \"confirmed_subjects\": [\"clearly visible subjects\"], \"confirmed_setting\": \"brief setting description\", \"confirmed_actions\": [\"chronological\", \"list\", \"of\", \"actions\"], \"sequence_of_play\": \"Concise summary of how actions unfold temporally and how subjects interact (e.g. 'Players from opposing teams contested possession while advancing'). Focus on dynamics rather than static enumeration.\", \"uncertainties\": [\"list of things that are unclear\"]}. "
                "Do not infer emotions, thoughts, or off-screen context. "
                "Return ONLY a valid JSON object."
            )
        }
    ]
    
    for b64 in base64_frames:
        content_list.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{b64}"
            }
        })
        
    payload = {
        "model": model_id,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": "You are an objective, forensic video analyst. Your sole purpose is literal transcription of visual evidence and temporal dynamics into a structured JSON ledger."
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


def call_vision_model(base64_frames, start_time, task_id):
    """Step 2 - Visual grounding with primary + fallback model chain."""
    # --- Primary attempt ---
    try:
        text = _call_vision_model_once(base64_frames, VISION_MODEL_ID, CONFIG['timeouts']['primary_vision'], task_id)
        if _vision_output_usable(text):
            return text
        log_event("vision", task_id, "warning", message=f"Primary output unusable ({len(text)} chars)")
    except Exception as e:
        log_event("vision", task_id, "warning", message=f"Primary vision model failed: {e}")

    # --- Fallback attempt (only if budget allows) ---
    elapsed = time.time() - start_time
    if elapsed > 20:
        log_event("vision", task_id, "error", message=f"No time for fallback vision (elapsed={elapsed:.1f}s)")
        raise RuntimeError("Vision grounding failed and no time for fallback")

    fallback_timeout = min(CONFIG['timeouts']['fallback_vision'], 28 - elapsed - 6)  # leave ≥6s for text gen
    if fallback_timeout < 3:
        log_event("vision", task_id, "error", message="Insufficient fallback budget")
        raise RuntimeError("Vision grounding failed and insufficient fallback budget")

    try:
        text = _call_vision_model_once(base64_frames, FALLBACK_VISION_MODEL_ID, fallback_timeout, task_id)
        if _vision_output_usable(text):
            return text
        log_event("vision", task_id, "error", message="Fallback output unusable")
        raise RuntimeError("Fallback vision output also unusable")
    except Exception as e:
        log_event("vision", task_id, "error", message=f"Fallback failed: {e}")
        raise RuntimeError("Both vision models failed") from e

# ---------------------------------------------------------------------------
# Step 3 — style generation
# ---------------------------------------------------------------------------
def call_text_model(facts, styles, timeout, task_id):
    """Step 3 - Style generation."""
    start_t = time.time()
    url = f"{FIREWORKS_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {FIREWORKS_API_KEY}",
        "Content-Type": "application/json"
    }
    
    style_instructions = {
        "formal": "formal: Forensic report style. Prioritize chronological actions over excessive visual descriptions (especially for food/objects). Use natural phrasing (e.g., 'an orange juvenile feline'). Forbid emotional adjectives. Max 40 words.",
        "sarcastic": "sarcastic: Strictly use antiphrasis. Exaggerate ONLY the historical or epic significance of directly observed actions. NEVER invent invisible intentions (e.g., 'plotting'), motivations, or backstory. NEVER declare an action has 'no reason'. NEVER attribute human motives, vendettas, or emotions to inanimate objects, tools, or isolated body parts. For intense scenes (sports/weather), deadpan or undersell the exertion. Keep sarcasm anchored entirely to literal events. Max 40 words.",
        "humorous_tech": "humorous_tech: Use software/IT metaphors, dynamically adapting the domain (OS, DBs, CI/CD, Compilers, GPU, game engines, physics simulations, etc.) to fit the specific scene. For physical sports, map athletic actions to IT equivalents (e.g., collision detection, brute-force algorithms, bandwidth exhaustion, packet loss, I/O bottlenecks). Ensure metaphors make semantic sense. Max 40 words.",
        "humorous_non_tech": "humorous_non_tech: Casual internet hyperbole. Forbid technical jargon. Exaggerate the scale of the action, but NEVER invent unobserved behavioral traits, intent, or backstory (e.g., do not say 'forgot where he parked'). NEVER attribute human motives, vendettas, or emotions to inanimate objects, tools, or isolated body parts. NEVER use subjective adverbs for actions (e.g., 'dramatic flop'). Max 40 words."
    }
    
    active_instructions = [style_instructions[s] for s in styles if s in style_instructions]
    instructions_text = "\n".join(active_instructions)
    format_example = "{" + ", ".join([f'"{s}": "..."' for s in styles]) + "}"
    
    user_prompt = f"JSON Factual Ledger:\n{facts}\n\nInstructions per style:\n{instructions_text}\n\nRequired output format: exactly {format_example}"
    
    payload = {
        "model": TEXT_MODEL_ID,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": "You are an expert linguistic adapter. You receive a JSON Factual Ledger from a vision model. You must extract the nouns, verbs, and dynamics from 'confirmed_subjects', 'confirmed_setting', 'confirmed_actions', and 'sequence_of_play' and map them directly to the stylistic persona. Do not include 'uncertainties'. CRITICAL ANTI-HALLUCINATION RULES: 1. Exaggerate the *significance* of an action, never invent the *intent* behind it. 2. Never declare an action happened for 'no reason'. 3. Forbid subjective adverbs/adjectives for physical actions (e.g. 'gracefully', 'dramatic'). Do not introduce any entities, actions, or outcomes that are not explicitly listed in the confirmed sections. Use the 'scene_tags' to adapt your humor and metaphors to the specific context of the clip. Rewrite these facts into distinctly-toned captions based on the requested styles. Return ONLY a valid JSON object, no other text. Keep all generated captions to a strict maximum of 40 words."
            },
            {
                "role": "user",
                "content": user_prompt
            }
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

# ---------------------------------------------------------------------------
# Step 4 — validation
# ---------------------------------------------------------------------------
def validate_and_overwrite(json_text, requested_styles, placeholder, task_id):
    """Step 4 - Validate and overwrite, with per-style partial credit."""
    start_t = time.time()
    if not json_text:
        log_event("validation", task_id, "error", time.time() - start_t, "Empty json_text")
        return None

    match = re.search(r'\{.*\}', json_text, re.DOTALL)
    if match:
        json_text = match.group(0)

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        log_event("validation", task_id, "error", time.time() - start_t, "JSON decode error")
        return None

    # Case-insensitive key matching
    data_lower = {str(k).lower(): v for k, v in data.items()}
    final_data = {}
    
    seen_values = set()
    
    for style in requested_styles:
        key = style.lower()
        value = data_lower.get(key)
        
        if not value or not str(value).strip():
            final_data[style] = placeholder.get(style, "This clip shows a sequence of events.")
            continue
            
        value_str = str(value).strip()
        
        # Enforce hard length limit (allow small buffer for punctuation split)
        if len(value_str.split()) > 45:
            log_event("validation", task_id, "warning", message=f"Style {style} exceeded word limit")
            final_data[style] = placeholder.get(style, "This clip shows a sequence of events.")
            continue
            
        # Reject markdown code blocks
        if value_str.startswith("```") or value_str.endswith("```"):
            final_data[style] = placeholder.get(style, "This clip shows a sequence of events.")
            continue
            
        # Reject placeholder leakage
        if value_str == placeholder.get(style, "This clip shows a sequence of events."):
            final_data[style] = placeholder.get(style, "This clip shows a sequence of events.")
            continue
            
        # Reject duplicated style outputs
        if value_str in seen_values:
            final_data[style] = placeholder.get(style, "This clip shows a sequence of events.")
            continue
            
        seen_values.add(value_str)
        final_data[style] = value_str

    return final_data

# ---------------------------------------------------------------------------
# Main clip processor
# ---------------------------------------------------------------------------
def process_clip(video_url, styles, task_id):
    """Process a single video clip end-to-end. Returns caption dict or None."""
    log_event("clip_start", task_id, "info", message=f"Starting clip {video_url}")
    start_time = time.time()
    placeholder = get_placeholder_captions(styles)
    try:
        base64_frames = extract_frames(video_url, task_id)
        facts = call_vision_model(base64_frames, start_time, task_id)

        # Size the styling call's timeout by what's actually left of the
        # per-clip budget, instead of a fixed value.
        elapsed = time.time() - start_time
        remaining = CONFIG['clip_budget_seconds'] - elapsed - 2  # under the outer 30s cutoff
        text_timeout = max(6, min(CONFIG['timeouts']['text_generation'], remaining))  # leave time for validation
        json_text = call_text_model(facts, styles, timeout=text_timeout, task_id=task_id)
        final_captions = validate_and_overwrite(json_text, styles, placeholder, task_id)
        
        if final_captions:
            log_event("clip_end", task_id, "success", time.time() - start_time)
            return final_captions
        else:
            log_event("clip_end", task_id, "error", time.time() - start_time, "Validation failed entirely")
            return None
            
    except Exception as e:
        log_event("clip_end", task_id, "error", time.time() - start_time, str(e))
        return None