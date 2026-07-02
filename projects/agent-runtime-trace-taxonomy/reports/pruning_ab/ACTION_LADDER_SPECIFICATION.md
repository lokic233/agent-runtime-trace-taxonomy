# Action Ladder Specification (FROZEN v1)

Auto-mirrors `results/pruning_ab/parity_study/action_ladder.json`. Frozen BEFORE outcome inspection.
Primary objective: **task-total effective cost = input + 0.1*cache_read + 1.25*cache_creation + 5*output (incl all downstream calls)**.

Each action is grounded in an ALREADY-BUILT, ALREADY-PAID deterministic transform in
`src/pruning_ab/prune_methods.py` (no new transform code; no LLM compression => no prompt/temperature to freeze).

| Action | dose | impl | byte preservation | expected cache | quality risk |
|---|---|---|---|---|---|
| A0_KEEP | 0 | `identity(messages)` | full (prefix+suffix byte-identical) | no disturbance; full prefix cache reuse | baseline |
| A1_LINEDEDUP | 1 | `dedup_exact_obs(messages)` | all PRIOR-prefix bytes identical; only n | low cache tax (prefix preserved -> high cache | low (exact duplicates only) |
| A2_MODERATE | 2 | `env_log_collapse(messages) primary; dedu` | prior prefix preserved where feasible; N | moderate; content-stable => cache mostly pres | plausible-but-not-catastrophic (removes recoverable content) |
| A3_AGGRESSIVE | 3 | `old_tool_obs_elide(messages, keep_recent` | one-time prefix change at compaction; by | one-time cache_creation spike, then reduced p | higher (elides older context that may be re-referenced) |

Frozen tolerances: [0.0, 0.02, 0.05, 0.1]. Fallback: if eligibility not met, action falls back to A0 (byte-identical) for that call. Failure: fail-closed: transform error -> A0 passthrough + logged.

Map to existing paid methods: {
 "A0_KEEP": "C0_identity",
 "A1_LINEDEDUP": "dedup_exact_obs (Study-2 LINEDEDUP arm; DEDUP-family)",
 "A2_MODERATE": "M6_env_log_collapse / M4_obs_cap_5k (content-stable)",
 "A3_AGGRESSIVE": "M7_old_obs_elide (aggressive) ; HYBRID1_m7_agg2 (recency, cache-busting variant)"
}
