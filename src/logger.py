import json
import time
import sys

def log_event(stage, task_id, status="success", latency_sec=None, message=None, **kwargs):
    """
    Emit a structured JSON log.
    """
    log_record = {
        "timestamp": time.time(),
        "task_id": task_id,
        "stage": stage,
        "status": status,
    }
    
    if latency_sec is not None:
        log_record["latency_sec"] = round(latency_sec, 3)
    if message is not None:
        log_record["message"] = message
        
    log_record.update(kwargs)
    
    # Print to stdout so Docker captures it cleanly
    print(json.dumps(log_record))
    sys.stdout.flush()
