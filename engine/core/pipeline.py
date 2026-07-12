import time
import json
import os
import concurrent.futures
from engine.utils.logging import log_event
from engine.utils.config import CONFIG
from engine.preprocessing.video_validator import get_video_duration
from engine.preprocessing.downloader import download_video
from engine.preprocessing.extractor import extract_frames
from engine.providers.fireworks import call_vision_model, call_text_model
from engine.prompting.caption_validator import validate_and_overwrite

def get_placeholder_captions(styles):
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

def process_clip(video_url, styles, task_id):
    """Process a single video clip end-to-end. Returns caption dict or None."""
    log_event("clip_start", task_id, "info", message=f"Starting clip {video_url}")
    start_time = time.time()
    placeholder = get_placeholder_captions(styles)
    try:
        local_video_path = download_video(video_url, task_id, start_time)
        try:
            duration = get_video_duration(local_video_path, task_id, start_time)
            base64_frames = extract_frames(local_video_path, duration, task_id, start_time)
        finally:
            if os.path.exists(local_video_path):
                os.remove(local_video_path)
                
        facts = call_vision_model(base64_frames, task_id, start_time)

        elapsed = time.time() - start_time
        remaining = CONFIG['clip_budget_seconds'] - elapsed - 2
        text_timeout = max(6, min(CONFIG['timeouts']['text_generation'], remaining))
        
        json_text = call_text_model(facts, styles, timeout=text_timeout, task_id=task_id, start_time=start_time)
        final_captions = validate_and_overwrite(json_text, styles, placeholder, task_id, start_time)
        
        if final_captions:
            log_event("clip_end", task_id, "success", time.time() - start_time)
            return final_captions
        else:
            log_event("clip_end", task_id, "error", time.time() - start_time, "Validation failed entirely")
            return None
            
    except Exception as e:
        log_event("clip_end", task_id, "error", time.time() - start_time, str(e))
        return None

def write_results(results_list, output_path):
    temp_path = output_path + ".tmp"
    with open(temp_path, "w") as f:
        json.dump(results_list, f, indent=2)
    os.replace(temp_path, output_path)

def run_pipeline(input_path, output_path):
    start_time = time.time()
    
    if not os.path.exists(input_path):
        log_event("init", "system", "error", message=f"Input file not found at {input_path}")
        return
        
    with open(input_path, "r") as f:
        tasks = json.load(f)
        
    results = []
    results_map = {}
    for task in tasks:
        task_id = task["task_id"]
        styles = task.get("styles", [])
        placeholder = get_placeholder_captions(styles)
        result_entry = {
            "task_id": task_id,
            "captions": placeholder
        }
        results.append(result_entry)
        results_map[task_id] = result_entry
        
    write_results(results, output_path)
    log_event("init", "system", "success", message=f"Loaded {len(tasks)} tasks and wrote placeholders")
    
    total_budget_seconds = CONFIG['total_budget_seconds']
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONFIG['max_workers']) as executor:
        futures = {}
        for task in tasks:
            elapsed = time.time() - start_time
            if elapsed > total_budget_seconds - 35:
                log_event("scheduler", task["task_id"], "warning", message=f"Total budget nearly exhausted ({elapsed:.1f}s). Skipping.")
                break
            
            task_id = task["task_id"]
            video_url = task["video_url"]
            styles = task.get("styles", [])
            
            future = executor.submit(process_clip, video_url, styles, task_id)
            futures[future] = task_id
        
        try:
            for future in concurrent.futures.as_completed(futures, timeout=total_budget_seconds - (time.time() - start_time)):
                task_id = futures[future]
                try:
                    final_captions = future.result(timeout=CONFIG['clip_budget_seconds'] + 5)
                    
                    if final_captions:
                        results_map[task_id]["captions"] = final_captions
                        write_results(results, output_path)
                        log_event("result_collector", task_id, "success", message="Successfully wrote output to file")
                    else:
                        log_event("result_collector", task_id, "warning", message="Returned None, keeping placeholder.")
                        
                except concurrent.futures.TimeoutError:
                    log_event("result_collector", task_id, "error", message="Timeout processing task, keeping placeholder.")
                except Exception as e:
                    log_event("result_collector", task_id, "error", message=f"Error processing task: {e}")
        except concurrent.futures.TimeoutError:
            log_event("scheduler", "system", "error", message="Global as_completed timeout reached, aborting collection.")

    log_event("shutdown", "system", "success", time.time() - start_time, "Pipeline shutdown complete")
