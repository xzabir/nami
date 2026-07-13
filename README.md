# Nami: Video Captioning Agent

An AI agent designed to watch video clips and generate highly stylized captions based on the provided tone. It operates autonomously, supporting multimodal analysis by extracting frames at 1 Frame Per Second (1 FPS) and passing them into a vision-capable LLM to understand context, setting, and subjects.

This project was built for the **Track 2: Video Captioning Agent** hackathon challenge.

## Features

- **Agent-Based Architecture**: Automatically ingests URLs (direct video links or cloud storage).
- **1 Frame Per Second Extraction**: Dynamically calculates the duration of a clip and strictly pulls 1 FPS for contextually dense vision-grounding, avoiding arbitrary frame caps.
- **Strict Budget Tracking**: A global wall-clock monitor ensures the batch processor never exceeds the 10-minute maximum runtime, guaranteeing successful exit codes.
- **Single-Pass Stylization**: To respect tight latency budgets (under 30s per request), the agent prompts the LLM to generate all four required caption styles (`formal`, `sarcastic`, `humorous_tech`, `humorous_non_tech`) simultaneously in a single structured JSON response.

## Architecture

The project consists of two distinct layers:
1. **The Submission Pipeline (Docker)**: A streamlined backend pipeline designed exclusively to meet the strict hackathon constraints. It operates as an offline batch runner that pulls tasks from `/input/tasks.json` and outputs results to `/output/results.json`.
2. **The Web Application (Full-Stack)**: A FastAPI backend and a modern React SPA frontend designed to showcase the agent's capabilities in a user-friendly dashboard with database persistence.

## Environment Setup

The container comes fully configured for the hackathon evaluation environment. If you are running the project locally for development, you can use a `.env` file to configure the parameters:

```env
# Fireworks AI Credentials
FIREWORKS_API_KEY=your_fireworks_key_here
FIREWORKS_BASE_URL=https://api.fireworks.ai/inference/v1

# AI Model Selection
GEMMA_MODEL_ID=accounts/fireworks/models/minimax-m3

# Video Processing Constraints
MIN_VIDEO_SECONDS=2
MAX_VIDEO_SECONDS=300
FRAMES_PER_SECOND=1.0
FRAME_JPEG_QUALITY=70
```

## Running the Submission Container

This project is packaged as a standard Docker image that automatically processes `/input/tasks.json` upon startup and writes to `/output/results.json` as per the Track 2 specifications.

1. **Build the image**:
   *(Apple Silicon users must include `--platform linux/amd64`)*
   ```bash
   docker buildx build --platform linux/amd64 -f Dockerfile.submission -t nami-agent .
   ```

2. **Run locally**:
   ```bash
   docker run --rm \
     -v $(pwd)/test_input.json:/input/tasks.json \
     -v $(pwd)/test_output.json:/output/results.json \
     nami-agent
   ```

## Running the Web Application (React + FastAPI)

In addition to the headless batch submission, you can run the full-stack web application to interact with the agent via a modern UI.

1. **Start the FastAPI Backend**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```

2. **Start the React Frontend**:
   ```bash
   cd react-frontend
   npm install
   npm run dev
   ```
   The frontend will be available at `http://localhost:5173`.

## Core Components

*   `app/services/video_processor.py`: Responsible for checking video durations and extracting exactly 1 frame per second without downloading the video to disk.
*   `app/services/caption_engine.py`: The vision model integration. It builds the few-shot context prompts and parses the JSON output.
*   `app/services/style_prompts.py`: The system prompt engineering core, heavily tuned with few-shot examples to differentiate between factual formal tones and dry sarcastic humor.
*   `run_batch.py`: The bootstrap script invoked by the Docker container to process the tasks, handle exceptions gracefully, and write the results to disk within the time budget.

## Dependencies

*   `opencv-python-headless`: For fast, non-GUI video frame extraction.
*   `httpx`: For asynchronous, robust API calls to the LLM endpoints.
*   `pydantic-settings`: For strict environment variable management.
