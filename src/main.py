import json
import os
import sys
import time
import concurrent.futures
import yaml
from pipeline import process_clip, get_placeholder_captions
from logger import log_event

# Load Config
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
with open(config_path, "r") as f:
    CONFIG = yaml.safe_load(f)

INPUT_PATH = "/input/tasks.json" if os.path.exists("/input/tasks.json") else "input/tasks.json"
OUTPUT_PATH = "/output/results.json" if os.path.exists("/input/tasks.json") else "output/results.json"
TOTAL_BUDGET_SECONDS = CONFIG['total_budget_seconds']

def write_results(results_list):
    # Atomic write to ensure file is always valid JSON
    temp_path = OUTPUT_PATH + ".tmp"
    with open(temp_path, "w") as f:
        json.dump(results_list, f, indent=2)
    os.replace(temp_path, OUTPUT_PATH)

def main():
    start_time = time.time()
    
    # Read tasks
    if not os.path.exists(INPUT_PATH):
        log_event("init", "system", "error", message=f"Input file not found at {INPUT_PATH}")
        sys.exit(1)
        
    with open(INPUT_PATH, "r") as f:
        tasks = json.load(f)
        
    # Initialize results with placeholders (Step 0)
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
        
    # Write initial fallback state immediately
    write_results(results)
    log_event("init", "system", "success", message=f"Loaded {len(tasks)} tasks and wrote placeholders")
    
    # Process clips with genuine parallelism
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONFIG['max_workers']) as executor:
        futures = {}
        for task in tasks:
            # Skip submitting new clips if < 35s remains in total budget
            elapsed = time.time() - start_time
            if elapsed > TOTAL_BUDGET_SECONDS - 35:
                log_event("scheduler", task["task_id"], "warning", message=f"Total budget nearly exhausted ({elapsed:.1f}s). Skipping.")
                break
            
            task_id = task["task_id"]
            video_url = task["video_url"]
            styles = task.get("styles", [])
            
            future = executor.submit(process_clip, video_url, styles, task_id)
            futures[future] = task_id
        
        # Collect results as they complete (not in submission order)
        for future in concurrent.futures.as_completed(futures, timeout=TOTAL_BUDGET_SECONDS - (time.time() - start_time)):
            task_id = futures[future]
            try:
                final_captions = future.result(timeout=CONFIG['clip_budget_seconds'] + 5)
                
                if final_captions:
                    results_map[task_id]["captions"] = final_captions
                    write_results(results)
                    log_event("result_collector", task_id, "success", message="Successfully wrote output to file")
                else:
                    log_event("result_collector", task_id, "warning", message="Returned None, keeping placeholder.")
                    
            except concurrent.futures.TimeoutError:
                log_event("result_collector", task_id, "error", message="Timeout processing task, keeping placeholder.")
            except Exception as e:
                log_event("result_collector", task_id, "error", message=f"Error processing task: {e}")

    log_event("shutdown", "system", "success", time.time() - start_time, "Pipeline shutdown complete")

if __name__ == "__main__":
    main()
