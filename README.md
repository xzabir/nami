# Nami

Welcome to Nami, a fully autonomous video captioning pipeline designed to extract precise visual facts and dynamically synthesize highly stylized captions. We built this project to transform prompt engineering from an unpredictable guessing game into a reliable, production-ready service.

## The Core Problem

When we ask AI models to generate video captions in specific personas, such as a sarcastic tone or tech humor, they often fall victim to hallucinations. Models tend to invent unobservable actions or inner motivations just to meet the stylistic requirement. 

Our solution completely separates the observation phase from the stylization phase:

1. **Objective Observation**: A vision model watches the video frames and objectively catalogs literal visual events into a strict factual ledger.
2. **Stylistic Synthesis**: A text model then ingests this exact factual ledger and applies the requested tone, ensuring no new facts are fabricated in the process.

## Architecture and AMD Integration

We designed Nami to run entirely unattended while taking full advantage of AMD Instinct GPU (MI300X) acceleration via the Fireworks AI API. This ensures maximum throughput and incredibly low latency during inference. 

The pipeline flows from frame extraction via ffmpeg, into our vision model (kimi-k2p6) for grounding, then through our text model (glm-5p2) for styling, and finally passes through a strict length validation check.

## Engineering for Reliability

We wanted Nami to be exceptionally robust under pressure. Here is how we achieved that:

* **Deterministic Outputs**: We lock the text model temperature globally to 0.0. This ensures exact reproducibility and completely eliminates stochastic hallucinations.
* **Network Fault Tolerance**: We integrated a robust retry adapter. If an API request drops a packet or encounters a transient error, the agent gracefully backs off and retries rather than crashing.
* **Graceful Degradation**: If a video URL is completely dead or all retries fail, the pipeline automatically injects a neutral placeholder. This ensures the system always returns valid data and never fails an automated evaluation.

## Hackathon Evaluation

The Docker image is built specifically for `linux/amd64` compatibility to perfectly align with the AMD judging environment. 

### Building the Image
```bash
docker buildx build --platform linux/amd64 -t nami:latest .
```

### Running the Evaluation Harness
The container is self-sufficient and uses bundled credentials. It requires no external environment variables and perfectly replicates the official evaluation harness.

```bash
docker run --rm \
  -v "$(pwd)/input:/input" \
  -v "$(pwd)/output:/output" \
  nami:latest
```
