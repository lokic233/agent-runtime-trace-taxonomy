# GENERALIZATION_PREREGISTRATION — cross_model_generalization_v1

**Frozen at:** Phase A completion, branch `crossmodel-generalization`, before any outcome-bearing run.
**Anchor:** Opus-4.7 canonical artifacts (freeze `bb43b49`), reused — NOT rerun (unless provenance replay fails).
**Scope:** mechanism-generalization + frozen-static-policy transport. NOT a controller-generalization study.
`CONTROLLER_GENERALIZATION` stays **NOT_TESTED — REQUIRES COMPLETED MRT**.

## Research questions
- **Q1 Cache tax** replicates across Claude tiers (Opus→Sonnet→Haiku)?
- **Q2 Intelligence tax** changes (grows?) as capability decreases?
- **Q3** Do frozen Opus-selected static actions transfer **zero-shot** to Sonnet, Haiku, and a peer-frontier model?
- **Q4** Which effects are caused by capability vs provider caching / pricing / tokenization / trajectory?

## Models (frozen)
- Anchor: `anthropic/claude-opus-4-7` (thinking off, temp 0.0, call limit 75) — reuse artifacts.
- Within-provider scaling: `anthropic/claude-sonnet-4-6`, `anthropic/claude-haiku-4-5` — identical route/cache/templates/tools/limit/temp/thinking/tasks/grader; ONLY the backend changes.
- Cross-provider: **`gpt-5-5`** (PRIMARY; verified reachable → fallback chain gpt-5-4 → gemini-3-1-pro is UNUSED). One cross-provider frontier only.

## Frozen treatments (function hashes in RUNTIME_PROVENANCE_AUDIT)
`C0_identity, SHAM, HYBRID1_m7_agg2, LINEDEDUP_e4, GENTLE6K_stable, CAP1K_stable` (+ `RETRIEVREF_e4` secondary).
**No threshold tuning** (LINEDEDUP min-len/threshold, GENTLE6K 6000, CAP1K, HYBRID1 windows, retrieval format are FROZEN). Zero-shot transport only. Any retuning is a separately-labeled later study.

## Task sets (frozen)
- Cache/intelligence tax: the exact **interesting-10** repeated-measures tasks (listed in runtime_provenance.json).
- Static-policy transport: **golden-50** (regex filter, 50 ids). Start at **30** preregistered, expand to 50 only after adapters+grader pass, no silent model switch, first-30 instrumentation valid.

## Estimands
- **Cache tax (Q1):** `cache_creation_fraction = cache_creation/(cache_creation+cache_read)`. Contrast: C0≈SHAM ≪ HYBRID1. Per-model, 5 reps × 10 tasks. Cross-provider: NOT computed for gpt-5-5 (no comparable estimand) — report physical cached-token share only if exposed.
- **Intelligence tax (Q2):** dose-controlled drift — API-call ratio, output-token ratio, repeated reads/cmds/errors, no-progress rework vs necessary verification; capability interaction = CAP1K drift larger on weaker models. Opus/Sonnet/Haiku, same 10 tasks, 3 reps (→5 if inconclusive), arms C0/LINEDEDUP/GENTLE6K/CAP1K.
- **Policy transport (Q3):** per model, effective-cost (Anthropic decomposition for Claude; provider-native vs own-C0 for gpt-5-5) for C0/LINEDEDUP/GENTLE6K/CAP1K on golden-50; report full-set + common-support set (common support defined from C0 runs **before** viewing treatment outcomes).

## Three transport concepts (kept distinct)
mechanism transport (direction survives) ≠ effect-size transport (magnitude similar) ≠ policy transport (frozen action still useful). A mechanism may transport while the policy does not.

## Verdict vocabulary
SUPPORTED / PARTIALLY_SUPPORTED / NOT_SUPPORTED / UNDERPOWERED / NOT_IDENTIFIABLE / EXPLORATORY.

## Forbidden conclusions (hard gates)
- learned controller generalizes · trace features identify optimal action · duplicate ratio is a causal moderator · large observations inherently waste · MRT unnecessary · single-run regression is discardable noise. `CONTROLLER_GENERALIZATION = NOT_TESTED`.

## Phase order & gates
A (this) → B 5-task smoke (validity only, no claims) → C cache-tax (Sonnet/Haiku) → D intelligence-tax (Opus/Sonnet/Haiku) → E static-policy transport (Sonnet/Haiku/gpt-5-5, 30→50) → optional RETRIEVREF. Each phase passes consistency gates before the next. C0 & SHAM byte-identity asserted every run; transform module+function hashes logged every run.

## Cost discipline
Smoke = 5 tasks × 6 arms × 3 models = 90 agent runs (≤75 calls each). No full paid phase launches until A's 3 artifacts pass internal checks (DONE: 14/14 reconstruction + provenance tied to canonical). Checkpoint with the user before paid phases.
