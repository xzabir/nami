<div align="center">
  <h1>🌊 Nami</h1>
  <p><strong>A Minimalist, High-Performance Video Captioning Agent</strong></p>
  <p>
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-black.svg" alt="License" /></a>
    <img src="https://img.shields.io/badge/Track-2_Agent-black.svg" alt="Track 2" />
    <img src="https://img.shields.io/badge/Model-Gemma_3-black.svg" alt="Model" />
  </p>
  <br />
</div>

## 📖 The Vision

**Nami** is an intelligent vision agent built from the ground up for the **AMD Developer Hackathon (Track 2)**. Instead of taking a shotgun approach to video analysis, Nami relies on surgical precision: she watches a video at exactly 1 Frame Per Second, passing a dense visual context array to the Gemma 3 vision model to generate four distinct caption styles in a single, lightning-fast inference pass.

The result? Unmatched consistency across formal, sarcastic, and humorous styles, all while strictly adhering to a 10-minute maximum runtime budget for bulk video processing.

---

## ⚡ What Makes Nami Different?

Unlike standard wrappers around AI endpoints, Nami is engineered for resilience and visual excellence:

- **Surgical Frame Extraction:** Dynamic duration calculation ensures we grab exactly what we need (1 FPS) directly from the stream without hoarding disk space.
- **Concurrent Batch Processing:** The offline evaluation runner utilizes a ThreadPoolExecutor to process multiple video tasks in parallel, safely guarding against timeouts.
- **Single-Pass Stylization:** Why make four API calls when you can make one? Nami requests `formal`, `sarcastic`, `humorous_tech`, and `humorous_non_tech` all at once via a heavily tuned, few-shot JSON schema prompt.
- **Dual Architecture:** Nami serves both as an isolated, headless batch processor (for the judges) and a sleek, minimalist full-stack web application (for humans).

---

## 🚀 Running Nami

Nami offers two operational modes depending on your needs.

### Mode A: The Headless Batch Runner (Hackathon Evaluation)

This is the exact setup required by the hackathon judges. It reads tasks from an input directory and outputs strict JSON.

1. **Build the Engine** (Apple Silicon users: use `--platform linux/amd64`)
   ```bash
   docker buildx build -f Dockerfile.submission -t nami-eval .
   ```
2. **Execute the Batch**
   ```bash
   docker run --rm \
     -v $(pwd)/input:/input \
     -v $(pwd)/output:/output \
     nami-eval
   ```

### Mode B: The Minimalist Web Application

Experience Nami through our beautifully designed, glassmorphic React frontend powered by a robust FastAPI + PostgreSQL backend.

1. **Spin up the stack**:
   ```bash
   docker-compose up --build
   ```
2. **Interact**: 
   - Open `http://localhost:5173` to view the stunning minimalist frontend.
   - Open `http://localhost:8000/docs` to view the interactive API documentation.

---

## 🛠 Under the Hood

### Environment Configuration
Whether you are running locally or via Docker, Nami respects standard `.env` variables for seamless integration:

```ini
FIREWORKS_API_KEY=your_key_here
MIN_VIDEO_SECONDS=2
MAX_VIDEO_SECONDS=300
FRAMES_PER_SECOND=1.0
FRAME_JPEG_QUALITY=80
```

### Core Stack
- **Vision Inference**: `httpx` and `accounts/fireworks/models/minimax-m3`
- **Video Extraction**: `opencv-python-headless`
- **Backend API**: FastAPI, Uvicorn, SQLAlchemy
- **Frontend UI**: React, Vite, Custom Glassmorphism CSS

---

<div align="center">
  <p><i>Crafted for the AMD Developer Hackathon.</i></p>
</div>
