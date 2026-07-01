# MRT Formal — Eligibility Audit (Steps 9 & 13, from REAL run data)

Auto-generated from `results/pruning_ab/mrt_formal/eligibility_audit.json` (events sha256[:16]
`e01d167205f6eb37`). **This uses the actual formal_locked online eligibility** — the
definitive measurement, superseding any pre-run NO_OP dry-run estimate.

## Availability (base eligibility: newest obs, seg≥2000, dup_lines≥5, LINEDEDUP removes ≥1 line)

| quantity | value |
|---|---|
| tasks attempted | 18 |
| tasks reaching availability | 13 |
| per-task availability rate | 72.2% |
| total available events (all calls) | 40 |
| **randomized interventions (single-shot: first available/task)** | **13** |

The gap between 40 available events and 13 interventions is the **single-shot ×
newest-only** rule: only the *first* available call per task is randomized.

## Redundancy (dup_frac) distribution among available events

| stat | value |
|---|---|
| min | 0.077 |
| median | 0.343 |
| max | 1.000 |
| HIGH (dup_frac>0.40) | 17 |
| MIXED (0<dup_frac≤0.40) | 23 |

Both strata have real support among available events — the moderator has range to be estimated;
the limitation is **N of randomized interventions**, not moderator range.

## Tasks with zero availability (structural, not a bug)
django__django-14771, django__django-16136, pytest-dev__pytest-7324, pytest-dev__pytest-7432, sympy__sympy-14248

Verified: none had a single newest observation meeting BOTH seg≥2000 AND dup_lines≥5. See
MRT_FORMAL_DATA_AUDIT.md.

## Finding
Single-shot x newest-only x opus-4.7 efficiency: 13/18 tasks reached availability, 13 interventions total. 5 tasks never produced a newest observation with seg>=2000 AND dup_lines>=5. This is the binding constraint below the 60-event floor.

⟹ Confirms the power analysis: reaching the 60-event floor requires a **much larger buildable
task pool**, not a threshold or code change. This run attempted all 18 and stopped per the rule.
