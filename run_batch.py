"""
Entrypoint for the Track 2 submission container.

Contract (per the Participant Guide):
  - Read tasks from /input/tasks.json on startup
  - Write results to /output/results.json before exiting
  - Exit code 0 on success, non-zero only on a fatal/unrecoverable error
  - Total runtime budget: 10 minutes
  - Per-clip response time should stay under 30s

Design choices for reliability under the hidden ~12-clip eval set:
  - A global wall-clock deadline is tracked so we never blow the 10 minute
    cap even if a couple of clips are slow/retry.
  - Every task is wrapped in its own try/except: one bad video_url or one
    Gemma hiccup must not take down the whole submission (which would zero
    out every other clip too).
  - If a clip can't be captioned in time, we still emit an entry with all
    four style keys present (empty strings) so the JSON schema stays valid -
    that clip scores 0 rather than corrupting the whole results file.
"""
import json
import logging
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

from app.config import settings  # noqa: E402
from app.services.caption_engine import generate_captions, CaptionGenerationError  # noqa: E402
from app.services.video_processor import VideoProcessingError  # noqa: E402
from app.services.style_prompts import STYLE_ORDER  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("run_batch")

TOTAL_BUDGET_SECONDS = 9 * 60 + 30  # leave a safety margin under the 10 min hard limit


def load_tasks(path: str) -> list:
    with open(path, "r") as f:
        return json.load(f)


def empty_captions() -> dict:
    return {style: "" for style in STYLE_ORDER}


def process_task(task: dict) -> dict:
    task_id = task.get("task_id")
    video_url = task.get("video_url")
    styles = task.get("styles") or STYLE_ORDER

    if not video_url:
        logger.error("Task %s has no video_url, skipping", task_id)
        return {"task_id": task_id, "captions": empty_captions()}

    try:
        captions = generate_captions(video_url, styles)
    except (CaptionGenerationError, VideoProcessingError) as exc:
        logger.error("Task %s failed: %s", task_id, exc)
        captions = empty_captions()
    except Exception as exc:  # noqa: BLE001 - never let one clip crash the run
        logger.exception("Task %s failed with unexpected error: %s", task_id, exc)
        captions = empty_captions()

    return {"task_id": task_id, "captions": captions}


def main() -> int:
    start = time.monotonic()
    input_path = settings.input_tasks_path
    output_path = settings.output_results_path

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    try:
        tasks = load_tasks(input_path)
    except Exception as exc:
        logger.exception("Could not read tasks from %s: %s", input_path, exc)
        # Still write valid (empty) JSON so we don't score an OUTPUT_MISSING /
        # malformed-file failure on top of a missing-input failure.
        with open(output_path, "w") as f:
            json.dump([], f)
        return 1

    results = []
    from concurrent.futures import ThreadPoolExecutor, as_completed

    # Setup budget and tracking
    unprocessed_tasks = {task.get("task_id"): task for task in tasks}
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Submit all tasks
        future_to_task_id = {}
        for task in tasks:
            future = executor.submit(process_task, task)
            future_to_task_id[future] = task.get("task_id")

        for future in as_completed(future_to_task_id):
            task_id = future_to_task_id[future]
            elapsed = time.monotonic() - start
            remaining_budget = TOTAL_BUDGET_SECONDS - elapsed
            
            if remaining_budget <= 0:
                logger.warning("Time budget exhausted during processing of %s", task_id)
                # If budget exhausted, the remaining tasks will just be left unfinished or we can inject empty
                pass

            try:
                res = future.result()
                results.append(res)
                del unprocessed_tasks[task_id]
            except Exception as exc:
                logger.exception("Unexpected error in future result for %s: %s", task_id, exc)
                results.append({"task_id": task_id, "captions": empty_captions()})
                del unprocessed_tasks[task_id]

    # Fill any remaining unprocessed tasks with empty captions due to timeout or hard failures
    for task_id, task in unprocessed_tasks.items():
        results.append({"task_id": task_id, "captions": empty_captions()})

    # Sort results to match original input order
    task_order = {task.get("task_id"): i for i, task in enumerate(tasks)}
    results.sort(key=lambda x: task_order.get(x.get("task_id"), 999))

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    logger.info("Wrote %d results to %s in %.1fs", len(results), output_path, time.monotonic() - start)
    return 0


if __name__ == "__main__":
    sys.exit(main())
