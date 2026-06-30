# Phase 2 — Contrast Sets (discovery dataset)

Unit = **task × call × candidate segment** (decision event), not whole task. Built from existing C0/LINEDEDUP/GENTLE6K runs. Outcomes **sealed separately** (`sealed_outcomes.json`) so the blind annotation stage (Phase 3) cannot see them.

## Coverage (50 task-units, auto-generated)
| contrast class | n tasks |
|----------------|--------:|
| LINEDEDUP_helped (>+5%) | 17 |
| LINEDEDUP_hurt (<-5%) | 21 |
| LINEDEDUP_neutral | 12 |
| GENTLE6K_helped | 19 |
| GENTLE6K_hurt | 19 |
| GENTLE6K_neutral | 11 |
| LINEDEDUP_regressed (quality) | 2 |
| high_cost outlier | 6 |
| ordinary_cost | 44 |

Good representation of both helped and hurt cases for every action — essential for discovering what *distinguishes* them.

## Blind decision views (`blind_decision_views.jsonl`, 48 events)
One decision event per task (the largest-observation call, eligible ≥2000 chars). Each view exposes ONLY:
- task statement excerpt, n prior observations, candidate segment text (truncated 6k) + tail, candidate segment size/lines, candidate dup-lines-vs-prior.
- **NO** future trajectory, action taken, cost, cache, or grading result.

## Leakage control
- `sealed_outcomes.json` holds contrast classes + savings + resolution — used ONLY in Phase 4 (outcome-aware adjudication), never shown to blind annotators.
- The blind view is prefix-only by construction (extracted up to the decision call).

## Files
- `results/pruning_ab/signal_discovery_contrast_sets.jsonl` (50 task-units, span refs)
- `results/pruning_ab/blind_decision_views.jsonl` (48 blind decision events)
- `results/pruning_ab/sealed_outcomes.json` (SEALED — Phase 4 only)
