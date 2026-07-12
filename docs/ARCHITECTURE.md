# Architecture: Nami Caption Pipeline

Nami employs a decoupled, two-pass architecture for video caption generation. It separates visual factual extraction from stylistic persona text generation. This guarantees high fidelity to the visual source material while enabling robust, hallucination-free stylized captions.

## High-Level Flow

1. **Pre-Emptive Fallback (Placeholder Write):**
   - At the very beginning of the task, safe, fallback captions are generated and written for all requested styles. This ensures that even if every subsequent step fails (due to timeouts, OOM, or API errors), a valid, parsable result exists.

2. **Frame Extraction (Uniform Sampling):**
   - The pipeline fetches the video via direct network stream (using `ffmpeg`) rather than downloading the entire file locally.
   - It extracts 16 frames uniformly spaced across the clip's duration at a fixed width (512px). Uniform sampling guarantees predictable payload sizes and latency, avoiding the unpredictable frame counts inherent in scene-change or motion-adaptive extraction.

3. **Grounding Call (Vision Pass):**
   - The extracted frames are sent to a neutral, factual vision model.
   - The model is instructed to act as a forensic analyst and output a structured JSON ledger covering the scene setting, environment context, subjects, actions, notable visual details, and chronological flow.
   - This pass explicitly forbids inferring off-screen context, invisible intentions, or adopting personas.

4. **Styling Call (Text Pass):**
   - The verified factual ledger from the Grounding Call is passed to a high-capacity text model.
   - The text model dynamically rewrites the verified facts into the four requested stylistic personas (`formal`, `sarcastic`, `humorous_tech`, `humorous_non_tech`).
   - Because the styling model never sees the raw pixels, it cannot invent details to service a joke. This decoupling drastically reduces hallucination risk.

5. **Validation (Partial Credit):**
   - The output JSON from the styling call is validated.
   - Validation is performed on a per-style basis. If one style exceeds the word count or produces malformed text, it falls back to its placeholder independently. The valid styles are kept, ensuring maximum partial credit.

For deeper insights into why we chose this architecture, see [Decision Log](DECISIONS.md).
