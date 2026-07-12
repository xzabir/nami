# Reliability & Failure Modes

Nami is engineered to be highly fault-tolerant. The video captioning environment is fraught with potential failures (network timeouts, unreadable files, API rate limits, model hallucinations). 

Instead of relying on fragile monolithic calls that fail entirely upon encountering an issue, Nami uses preemptive fallbacks, chunked timeouts, and partial-credit parsing to guarantee that a scorable artifact is generated even in worst-case scenarios.

## Failure Mode Matrix

| Failure Mode | Trigger | System Behavior | Why it's Safe |
|--------------|---------|-----------------|---------------|
| **Network Stall during Extraction** | Remote video host hangs or throttles | `ffmpeg` is wrapped in a hard 20s subprocess timeout. If triggered, it aborts extraction and falls back to placeholders. | Prevents indefinite hangs and ensures the overall 30s budget isn't exceeded waiting for dead network sockets. |
| **Primary Vision API Down / Timeout** | Fireworks API lags or returns 503 | Timeout is computed dynamically based on the 30s budget. If `primary_vision` fails or times out, the system routes to a lighter `fallback_vision` model. | Maximizes the chance of getting factual grounding by gracefully degrading model capability rather than crashing. |
| **Insufficient Fallback Budget** | Vision extraction and primary call leave <3s on the clock | Pipeline detects it lacks budget for a safe text generation step and skips the fallback. | Hard respects the 30s limit; skipping to placeholder is safer than attempting a call guaranteed to exceed the time budget. |
| **Malformed JSON in Text Generation** | LLM outputs markdown blocks or unparseable text | The `validate_and_overwrite` logic intercepts the string, regex-strips markdown, and attempts parsing. If impossible, it fails back. | A single missed JSON bracket won't crash the pipeline, preserving the placeholders. |
| **Single Style Hallucination/Length Violation** | The `sarcastic` style hallucinates or exceeds 120 words | The validation function catches the error for the single style key and overwrites *only* that style with its placeholder. | Discarding three perfect captions because of one bad style key throws away real accuracy points. This ensures partial credit is maximized. |
| **Global Pipeline OOM / Fatal Crash** | System-level error abruptly kills the container | Placeholders were explicitly written to disk at the beginning of processing (Step 1). | The evaluation platform will read the placeholder output file and score it (generic but safe) instead of logging a missing file zero-score. |
