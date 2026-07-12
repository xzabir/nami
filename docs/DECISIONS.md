# Architecture Decision Log (ADR)

This document outlines the major architectural choices made in Nami and the engineering reasoning behind them.

## 1. Decoupled Two-Pass Architecture vs. Monolithic Call
**Decision:** We split visual extraction (grounding) and text styling into two separate LLM calls.
**Why:** A single vision model call asked to simultaneously observe the video and adopt four extreme personas risks hallucination under humor (e.g., inventing details to service a joke). 
**Trade-off accepted:** Slightly higher API latency/cost due to two sequential calls, but heavily mitigates factual hallucination.

## 2. Uniform Frame Sampling vs. Adaptive/Motion-Weighted Sampling
**Decision:** We use fixed uniform frame sampling (16 frames at 512px) calculated via duration-agnostic fps.
**Why:** Scene-change detection yields an unpredictable frame count (e.g., 3 frames for a static clip, 50 frames for high motion). Unpredictable payload sizes lead to unpredictable API latency, risking timeouts. Uniform sampling is deterministic and ensures worst-case latency fits within the 30-second budget.
**Trade-off accepted:** We might sample redundant frames on static videos or miss micro-actions in chaotic videos, but we gain iron-clad predictability and avoid timeouts.

## 3. Placeholder-First Pipeline
**Decision:** We initialize output files with style-distinct placeholders before any heavy compute begins.
**Why:** If the pipeline crashes, hits a global timeout, or runs OOM, it guarantees a valid, non-empty, JSON-compliant output exists on disk. This results in a "scorable (if generic) result" rather than throwing away an entire clip or blocking the entire test suite.
**Trade-off accepted:** Slightly increased disk I/O at the start of the pipeline.

## 4. Per-Style Partial Credit Validation
**Decision:** We validate and overwrite placeholders on a per-style basis rather than using all-or-nothing validation.
**Why:** If one style hallucinates, violates length limits, or produces malformed text, we only fail that specific style. Discarding three perfectly good captions because of one bad style key throws away real accuracy and style points. 
**Trade-off accepted:** Slightly more complex validation code.
