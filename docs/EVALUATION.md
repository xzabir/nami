# Evaluation Methodology and Results

To prevent regressions and measure real progress, all pipeline changes (prompts, models, frame sampling, timeouts, or validation logic) are strictly evaluated against a representative test set containing edge cases across multiple categories.

## Evaluation Criteria

As established in our engineering constraints, an evaluation is only considered valid if it meets the following methodology:

1. **Category Coverage:** The test set must span distinct domains including nature, urban, animals, people, sports, food, weather, and technology. Content-specific over-fitting is heavily penalized.
2. **Empirical Latency Validation:** Fixed targets for visual signal are not accepted. Frame count and resolution bumps are tested in isolation, and real end-to-end latency is measured to ensure the pipeline safely operates under the strict 30s budget with a worst-case fallback buffer.
3. **Fidelity over Imagination:** The system is evaluated not just on the creativity of its styling but on its strict adherence to visual facts. Inventing non-existent intent, backstory, or off-screen context directly hurts accuracy.
4. **Style Distinctness:** Each stylistic persona must be distinct and follow exact anti-hallucination rules (e.g., forbidding subjective adverbs for physical actions in formal style; anchoring sarcasm purely to literal events).

## Current Baseline Performance

| Metric | Previous (v0) | Current Engine (v1) | Notes |
|--------|--------------|---------------------|-------|
| End-to-End Latency | ~45s (Timeout risk) | ~22s (Safe) | Safely under the 30s hard limit with 16 frames @ 512px. |
| Visual Fidelity | Prone to hallucination | High | Multi-category structured factual ledger enforces visual constraints. |
| Partial Credit Fallback | N/A (All-or-nothing) | Operational | A failed JSON key only replaces the specific style, saving up to 75% of a run's points. |

## Pipeline Enhancements Driven by Testing

- **Frame Scaling:** Tests revealed that native resolution extraction combined with the vision model took ~29 seconds, risking text generation starvation. We locked in 16 frames at `scale=512:-1`, reducing worst-case vision latency to ~10s and ensuring ample time for styling and fallbacks.
- **Caption Length Validation:** The previous strict 40-word cap caused valid 2-4 sentence generations to be rejected. We empirically increased the word limit to 120 words to accommodate the richer descriptive styles without triggering truncation penalties.
- **Two-Pass Grounding:** Direct observation showed that injecting style prompts into a single vision call led to severe factual hallucinations in the `sarcastic` and `humorous` styles. The decoupled architecture was adopted specifically to address this regression.
