import os
from engine.core.pipeline import run_pipeline

INPUT_PATH = "/input/tasks.json" if os.path.exists("/input/tasks.json") else "input/tasks.json"
OUTPUT_PATH = "/output/results.json" if os.path.exists("/input/tasks.json") else "output/results.json"

if __name__ == "__main__":
    run_pipeline(INPUT_PATH, OUTPUT_PATH)
