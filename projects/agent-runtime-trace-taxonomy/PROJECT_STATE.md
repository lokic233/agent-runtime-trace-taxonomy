# PROJECT STATE — agent-runtime-trace-taxonomy

**Engine:** research-os (lokic233/research-os) · **Claim:** CLAIM-0001 · **Experiment:** EXP-0001 (CPU L1)
**Owner:** dengcchi · **Stage gate:** Stage A (taxonomy) MUST precede Stage B (full annotation).

## CURRENT STATUS (2026-06-28)
- `STAGE = A` · `TAXONOMY_STATUS = DRAFTING` · `ANNOTATION_ALLOWED = false`
- `TRACE_PATHS_PENDING = NO` — we already have real validated trace roots (see config/trace_sources.yaml).
- Recovering from a provider failure (110 dropped tool calls) that committed NOTHING durable.
  Trace downloads survived; project skeleton rebuilt from scratch and committed.

## TRACE INVENTORY (validated on disk)
| alias    | model                         | resolve | trajs   | node        | status    | role in study      |
|----------|-------------------------------|---------|---------|-------------|-----------|--------------------|
| solver_A | claude-opus-4-7 (live run)    | TBD     | ~297→500| devgpu014   | GENERATING| dev (when graded)  |
| solver_B | live-SWE-agent + opus-4.5     | 79.2%   | 500/500 | devvm14382  | AVAILABLE | dev (SOTA ceiling) |
| solver_C | SWE-agent + claude-3.5-sonnet | 33.6%   | 500/500 | devvm14382  | AVAILABLE | dev (mid tier)     |
| solver_E | SWE-agent-LM-32B (Qwen2.5)    | 40.2%   | 500/500 | devvm14382  | AVAILABLE | **HELD OUT**       |
| solver_F | claude-opus-4-6 (live run)    | TBD     | ~40→500 | devgpu014   | QUEUED    | capability audit   |

## ⚠️ KNOWN POLICY/DATA MISMATCH (documented, not silently resolved)
The prompt's default split names **Qwen2.5-Code-Agent-8B** as a taxonomy-DEV model and
**Qwen2.5-32B** as the HELD-OUT solver. On disk we have the **32B** (held-out one) and **NO 8B**.
DECISION (autonomous, reversible): keep the holdout policy AS WRITTEN — 32B stays held out, excluded
from taxonomy creation + LoRA training. Document the missing 8B as a coverage gap. Do NOT swap them.
If owner wants 32B promoted to dev, that requires a versioned decision in config/holdout_policy.yaml.

## STAGE A PLAN (taxonomy discovery → pilot → freeze)
1. [done] research-os instance + claim + exp registered; project skeleton committed.
2. [next] LANE 1: TokenSaver contract (context/tokensaver_contract.md) — relocate clone off /tmp.
3. LANE 2: normalized event/trace schemas + parsers (handle BOTH .traj flat and live-SWA nested .traj.json).
4. L0 deterministic feature extraction + coverage report.
5. Bootstrap sampling (60–80 traces, dev models only, stratified) → manifest.
6. Open coding ×3 independent lanes (A/B/skeptic).
7. Synthesizer → workload_taxonomy_v0 + waste_taxonomy_v0.
8. Closed-label pilot (80–120 fresh traces, 3 annotators) → agreement gates.
9. ≤2 revision rounds → FREEZE v1 → TAXONOMY_STATUS=FROZEN_V1.

## STAGE B (gated, do not start until FROZEN_V1 + paths validated)
Full annotation (2 annotators + adjudicator), per-task + per-model mappings, LoRA exports, red-team audit.

## HARD RULES
- No GPU jobs. No fabricated Pareto/config-gold labels (frontier agreement ≠ empirical truth).
- Annotators blinded to real model names (private/model_alias_map.json is gitignored).
- Prefix views (T0/T5/T10/T20) must pass automated future-leakage tests.
- Held-out 32B: NOT used to create/revise taxonomy; NOT in LoRA training export.
- Commit every durable artifact. Never leave completed work only in a transcript.
