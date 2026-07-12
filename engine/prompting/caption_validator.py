import re
import json
import time
from engine.utils.logging import log_event

def validate_and_overwrite(json_text, requested_styles, placeholder, task_id, start_time):
    """Step 4 - Validate and overwrite, with per-style partial credit."""
    if not json_text:
        log_event("validation", task_id, "error", time.time() - start_time, "Empty json_text")
        return None

    match = re.search(r'\{.*\}', json_text, re.DOTALL)
    if match:
        json_text = match.group(0)

    json_text = json_text.strip()
    if json_text.startswith("```json"):
        json_text = json_text[7:]
    elif json_text.startswith("```"):
        json_text = json_text[3:]
    if json_text.endswith("```"):
        json_text = json_text[:-3]
    json_text = json_text.strip()

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError:
        log_event("clip_end", task_id, "error", latency_sec=time.time()-start_time, message="Validation failed entirely")
        print(f"FAILED JSON TEXT: {json_text}")
        return None

    # Case-insensitive key matching
    data_lower = {str(k).lower(): v for k, v in data.items()}
    final_data = {}
    
    seen_values = set()
    
    for style in requested_styles:
        key = style.lower()
        value = data_lower.get(key)
        
        fallback_text = placeholder.get(style, "This clip shows a sequence of events.")
        
        if not value or not str(value).strip():
            final_data[style] = fallback_text
            continue
            
        value_str = str(value).strip()
        
        # Enforce hard length limit (allow small buffer for punctuation split)
        if len(value_str.split()) > 120:
            log_event("validation", task_id, "warning", message=f"Style {style} exceeded word limit")
            final_data[style] = fallback_text
            continue
            
        # Reject markdown code blocks
        if value_str.startswith("```") or value_str.endswith("```"):
            final_data[style] = fallback_text
            continue
            
        # Reject placeholder leakage
        if value_str == fallback_text:
            final_data[style] = fallback_text
            continue
            
        # Reject duplicated style outputs
        if value_str in seen_values:
            final_data[style] = fallback_text
            continue
            
        seen_values.add(value_str)
        final_data[style] = value_str

    return final_data
