# Agentic-Memory Parity Pilot — Staged Design (DESIGN ONLY, NOT RUN)

A small **sequential** pilot, NOT a 3,000-run campaign. Goal: answer whether the memory ladder
creates action crossing **above the repeated-run noise floor** — measured, not assumed. The SHAM
control is **embedded from the start**, not reconstructed afterward (the key lesson from the
retrospective study). No execution tonight.

## Stage 0 — Deterministic validation (NO model trajectories, ~free)
Verify before spending anything:
- memory write/read correctness; exact dereference returns byte-identical content;
- snapshot byte-stability between epochs (same bytes ⇒ prefix cache reused);
- cache-boundary behavior (consolidation creates cache once, reused after);
- deterministic serialization (snapshot_id = content hash is stable);
- fail-closed fallback to A0 on any memory error;
- raw-evidence preservation (nothing needed for recovery is lost).
**Gate:** all invariants pass, else fix before Stage 1.

## Stage 1 — Noise estimation (small, with EMBEDDED SHAM)
- Small representative task subset (≈6–8 tasks, ≥4 repos, span short/medium/long trajectories).
- Run **repeated identical controls** (A0 and a byte-identical SHAM of A0) ≥5 reps each.
- Estimate: within-task task-total-cost variance; quality flip variance; **whether noise is
  multiplicative vs additive**; whether it scales with task cost/trajectory length; **within-task
  action-noise correlation** (the quantity the retrospective study could not measure).
- Output: required repetitions r per cell to make the min-selection noise floor < the preregistered
  practical threshold (e.g. 5% task-total). If r is infeasible, **stop and report undetectable**.

## Stage 2 — Small replicated existence pilot (only if Stage 1 says detectable)
- Structure: **8–12 tasks × 3–4 actions × adaptive reps** (r from Stage 1).
- **Sequential stopping rules** (frozen before outcomes):
  - stop early if one action clearly dominates across the pilot tasks (posterior P(best) > 0.95);
  - stop early if variance makes practical parity undetectable at feasible r;
  - expand only if preliminary crossing exceeds the preregistered practical threshold with a
    conservative lower confidence bound.
- Embedded SHAM continues throughout (live noise floor, not post-hoc).

## What the pilot must NOT do
- No fixed large campaign before Stage-1 noise is measured.
- No single-run per-task oracle (see REPEATED_ORACLE_ESTIMATION_PLAN.md).
- No post-treatment features as deployable signals.
- No threshold tuning to manufacture a crossing.

## Success / stop criteria
- **Proceed to a powered study** only if Stage 2 shows action crossing whose conservative lower bound
  exceeds the practical threshold at ≥1 tolerance, stable across repos and repetitions.
- **Clean negative** (memory ladder does not create detectable parity) is an acceptable, publishable
  outcome — it would extend the static-primitive conclusion to a second, stronger action family.

## Frozen inputs to create at pilot time (schemas drafted in results/pruning_ab/memory_parity_design/)
action_specification.json · task_manifest.json · randomization_plan.json · repetition_plan.json ·
sham_plan.json · stopping_rules.json · cost_definition.json · quality_definition.json · noise_model_plan.json.
