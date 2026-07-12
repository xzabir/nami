Use when writing, reviewing, or modifying any code for the nami video captioning agent (AMD Developer Hackathon ACT II, Track 2).
---
# Track 2 Hard Constraints

These are CONFIRMED official rules from the participant guide and direct
organizer confirmation — not assumptions. Every code change must respect
all of them. If a proposed change would violate one, stop and flag it
instead of proceeding.

## Exact I/O contract

Input, read from `/input/tasks.json`:
```json
[{"task_id": "v1", "video_url": "https://...", "styles": ["formal", "sarcastic", "humorous_tech", "humorous_non_tech"]}]
```

Output, written to `/output/results.json`:
```json
[{"task_id": "v1", "captions": {"formal": "...", "sarcastic": "...", "humorous_tech": "...", "humorous_non_tech": "..."}}]
```

## Hard limits — confirmed, not negotiable

- Container ready within 60 seconds of start
- **30 seconds is the real per-clip processing budget** — confirmed
  directly with organizers, not inferred
- 10 minutes total runtime across the whole batch
- A missing caption for even ONE requested style scores ZERO for that
  entire clip — no partial credit at the clip level
- Docker image: public registry, linux/amd64 manifest, well under 10GB
  compressed (large images have hit intermittent PULL_ERROR under load —
  aim under ~2-3GB)
- No model/API restrictions for Track 2 — any provider is fine
- Scoring: two 0-1 axes per caption (accuracy, style match), averaged
  across all clips and styles, by an undisclosed LLM-judge
- Hidden evaluation set is ~12 clips spanning nature, urban, animals,
  people, sports, food, weather, technology — broader than any 3 public
  samples. Never tune prompts or few-shot examples to specific sample
  content; this WILL overfit and score poorly on categories never tested.

## Non-negotiable design invariants

Do not remove or weaken these without an explicit, separate decision:
- Placeholder-first: write a safe, valid output before any real
  processing begins, so total failure never produces missing/malformed output
- Placeholders must be DISTINCT text per style, never identical — a
  single sentence cannot simultaneously score as all four tones
- Per-style partial credit on validation — one bad/missing style must
  never discard the other three good captions for that clip
- Any timeout/retry logic must be justified against the 30s/clip and
  10min total budgets explicitly, with the worst-case math shown, not
  just a comfortable-looking number picked by feel

## When in doubt

If a proposed change's worst-case latency isn't obviously safe under the
30s/clip budget, say so explicitly and propose how to measure it
empirically against real sample clips before shipping it.
