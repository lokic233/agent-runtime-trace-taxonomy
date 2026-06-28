# Trace Source Inventory

Status of every trace root the project knows about (validated 2026-06-28).
This is the human-readable companion to config/trace_sources.yaml.

| alias | model | node | layout | trajs | resolve | status | role |
|-------|-------|------|--------|------:|--------:|--------|------|
| solver_A | claude-opus-4-7 (live) | devgpu014 | nested_traj | ~466→500 | ungraded | GENERATING | dev |
| solver_B | live-SWE-agent + opus-4.5 | devvm14382 | mini_swe_agent | 500 | 79.2% | AVAILABLE | dev (SOTA) |
| solver_C | SWE-agent + claude-3.5-sonnet | devvm14382 | flat_traj | 500 | 33.6% | AVAILABLE | dev (mid/weak) |
| solver_D | Qwen2.5-Code-Agent-8B | — | — | 0 | — | **ABSENT** | dev slot EMPTY |
| solver_E | SWE-agent-LM-32B (Qwen2.5) | devvm14382 | flat_traj | 500 | 40.2% | AVAILABLE | **HELD OUT** |
| solver_F | claude-opus-4-6 (live) | devgpu014 | nested_traj | ~40 | ungraded | QUEUED | capability audit |

**TRACE_PATHS_PENDING = NO** — real validated paths in config/trace_sources.yaml (paths kept out of
committed artifacts; the trace_id→path locator is gitignored under private/).

## Layouts (the normalizer handles all 4)
- `flat_traj`: trajs/<inst>.traj — classic SWE-agent, trajectory[] with action/observation/thought/state
- `nested_traj`: <inst>/<inst>.traj — same content, per-instance subdir (live runs)
- `mini_swe_agent`: trajs/<inst>/<inst>.traj.json — messages[]; assistant=THOUGHT+bash, user=<returncode><output>

## Grading (resolve status, sampling-balance only)
Per-instance report.json, two shapes both handled: nested {inst:{resolved}} (opus/sonnet) and flat
{resolved} (32B). All three graded sets match the swebench.com leaderboard exactly.

## Coverage gap (see config/holdout_policy.yaml)
The prompt's split names Qwen-8B as dev and Qwen-32B as held-out. On disk we have 32B (held out) but
NOT 8B. Policy kept AS WRITTEN — 32B stays firewalled; the 8B dev slot is empty. NOT silently swapped.
