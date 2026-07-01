# MRT Formal — Phase A Infrastructure Smoke (Step 13)

**Run:** infra_smoke · 2 cached tasks (sympy-14976, sympy-24539) · shim `df08cebcfd2b37c6`.
Isolated dir `results/pruning_ab/mrt_formal_smoke/` (does NOT pollute the formal ledgers).

## Verified (infrastructure only)
| check | result |
|---|---|
| valid provider response | ✅ 27/27 events have real H=1 cost |
| main-agent call detection | ✅ internal (<=2 msg) calls filtered; 27 real calls logged |
| event logging (full schema) | ✅ all 23 required fields present on every event |
| NO synthetic fallback | ✅ 0 infrastructure_failure; 0 fabricated content |
| task-state persistence | ✅ ledgers created; reconstructed_tasks=0 at start |
| no duplicate intervention | ✅ (0 interventions — see below) |
| provenance recording | ✅ model=claude-opus-4-7, git=0599c55 consistent on all events |

## Observation: cached sympy tasks do not reach availability
27 events, **0 available**, max segment 2476 chars. Both sympy tasks solved without producing
a newest observation meeting `seg>=2000 & dup_lines>=5`. Consistent with the rescue finding
that opus-4.7 solves efficiently with little redundant re-reading. The protocol pilot (Step 14)
uses tasks with high prior C0 availability (pylint-4551=11, pylint-8898=7) to exercise the
randomization path.

## Conclusion
Infrastructure is sound. The formal shim runs live, logs the full schema, fails closed, and
persists state. Proceeding to the protocol pilot on high-availability tasks.
