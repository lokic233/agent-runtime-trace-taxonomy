# SWE-Agent Context-Pruning Harness — Reproducible Apparatus

Everything needed to **replay and verify** the 12-method context-pruning A/B on opus-4.7.
This is the runtime apparatus behind `reports/pruning_ab/PARETO_FRONTIER_v2_VERIFIED.md`.

## What's here

```
harness/pruning_ab/
├── README.md                 ← this file
├── RUNTIME_CONFIG.json       ← per-method runtime binding (fn, port, env, verified result)
├── prune_methods.py          ← ALL pruning transforms (the METHODS dispatch dict)
├── configs/
│   └── swe_agent_run_batch.config.yaml   ← the exact SWE-agent run config all arms used
└── scripts/
    ├── prune_shim.py         ← localhost Anthropic-Messages shim → PlugBoard mTLS (applies the prune)
    ├── prune_shim_openai.py  ← OpenAI-format variant of the shim
    ├── run_arm.sh            ← per-method runtime driver (sweagent run-batch through the shim)
    ├── grade_arm.sh          ← SWE-bench grading (podman, network-isolated)
    ├── analyze_arms.py       ← saving/regression/loss_UB Pareto table
    └── plugboard_fix.py      ← the [::1] no_proxy bug fix (deletes bracketed IPv6 from no_proxy)
```

## The architecture (how pruning is applied at runtime)

```diagram
SWE-agent run-batch (opus-4.7)
        │  ANTHROPIC_BASE_URL=http://127.0.0.1:<port>
        ▼
   prune_shim.py  ──►  apply_method(TS_PRUNE_METHOD, messages)   ← THE PRUNING HAPPENS HERE
        │                (mutates the messages[] array in-flight)
        │  curl --noproxy *  (mTLS)
        ▼
   PlugBoard  ──►  claude-opus-4-7
```

The shim is a transparent pass-through that **only mutates the `messages` array** using the
configured prune method. Everything else (model, tools, system, max_tokens) is forwarded verbatim.
Token saving is measured from the PlugBoard usage block: `input + cache_read + cache_creation`.

## Per-method runtime config

Every method is a key in `prune_methods.METHODS` selected at runtime via `TS_PRUNE_METHOD`.
See `RUNTIME_CONFIG.json` for the machine-readable version. Verified results (opus-4.7, golden-50):

| method | prune_methods fn | shim port | saving% | reg | loss_UB | tier |
|--------|------------------|:---:|------:|:--:|------:|:---:|
| C0_identity | `identity` | 8751 | 0.0 | 0 | — | baseline |
| HYBRID1_m7_agg2 | `hybrid_m7_agg2` | 8773 | +41.5 | 1 | 0.088 | LOW |
| COMBO1_m7_cap5k | `m7_plus_cap5k` | 8764 | +42.5 | 2 | 0.118 | MED |
| PROG1_progressive | `progressive_compression` | 8775 | +37.9 | 2 | 0.118 | MED |
| AGG3_recency_obs_4 | `recency_keep_task_4` | 8763 | +50.6 | 3 | 0.146 | MED |
| AGG2_recency_obs_8 | `recency_keep_task_8` | 8762 | +47.7 | 3 | 0.146 | MED |
| AGG1_recency_obs_12 | `recency_keep_task` | 8761 | +39.9 | 3 | 0.146 | MED |
| SUM1_summarize_old | `summarize_old_obs` | 8771 | +38.2 | 3 | 0.146 | MED |
| COMP1_tool_compress | `tool_result_compress` | 8772 | +22.6 | 3 | 0.146 | MED |
| DEDUP2_similar_obs | `dedup_similar_obs` | 8774 | +19.0 | 3 | 0.146 | MED |
| M4_obs_cap_5k | `METHODS['M4_obs_cap_5k']` (lambda) | 8755 | +1.4 | 3 | 0.146 | MED |
| M6_env_log_collapse | `env_log_collapse` | 8757 | +0.5 | 3 | 0.146 | MED |
| M7_old_obs_elide | `old_tool_obs_elide` | 8758 | +37.0 | 5 | 0.199 | HIGH |

## Replay one method (3 steps)

```bash
M=HYBRID1_m7_agg2; PORT=8773
GOLDEN='^(astropy__astropy-12907|...)$'   # the 50 golden task ids (see data/pruning_ab/golden_traces/)

# 1. start the prune shim (applies the method to every request)
TS_PRUNE_METHOD=$M PB_SHIM_PORT=$PORT PB_LEDGER=logs/ledger_$M.jsonl \
  python scripts/prune_shim.py &

# 2. run SWE-agent through the shim on the golden-50
bash scripts/run_arm.sh "$M" "$PORT" "$GOLDEN" arms/full_$M 4

# 3. grade against real SWE-bench test suites
bash scripts/grade_arm.sh "$M"
# → prune_ab.prune_$M.json with resolved_ids; diff against C0 for regressions
```

## Verify the published numbers

```bash
python scripts/analyze_arms.py pareto full   # regenerates saving/regression/loss_UB table
# compare against ../../results/pruning_ab/final_verified_table.json
```

## CRITICAL runtime gotchas (or it won't reproduce)

1. **Unset ALL proxy env vars** before running. The inherited `no_proxy` contains `[::1]` which
   crashes litellm/httpx with `Invalid port: ':1]'`. `run_arm.sh` does this; if you call sweagent
   directly, you must too. (The shim does its own mTLS egress via `curl --noproxy *`.)
2. **opus-4.7, thinking NOT enabled, temperature=0.0.** The published frontier is scoped to standard
   mode. Methods that reorder/clear turns may behave differently with extended thinking.
3. **podman, not docker**: `MSWEA_DOCKER_EXECUTABLE=podman` + `DOCKER_HOST=unix://.../podman.sock`.
   If grading wedges, clear orphaned eval containers (`podman rm -fa`) — do NOT `system prune`
   (it deletes the cached sweb.eval images and forces re-pulls).
4. **Token saving = `input + cache_read + cache_creation`**, NOT raw `input` (PlugBoard caches
   context, so raw input is ~6 tokens — measuring that alone is the #1 way to get bogus saving numbers).
5. **Grade, don't trust submissions.** Submission count ≠ resolution. A method can submit a patch
   that fails tests. ALWAYS grade with the SWE-bench harness. (v1 of this study made exactly this
   error — see PARETO_FRONTIER_v1.md superseded note.)

## Portability note

The scripts hardcode this study's paths (`/data/users/dengcchi/hal_work/...`,
`/data/users/dengcchi/prune_ab/...`) and conda envs (`hal`, `swe-agent-1.0`). To replay elsewhere:
- Point `run_arm.sh`/`grade_arm.sh` at your own HAL-harness + SWE-agent-1.0 checkout and conda envs.
- The SWE-agent run config (`configs/swe_agent_run_batch.config.yaml`) embeds tool-bundle paths under
  `hal-harness/agents/SWE-agent-v1.0/tools/` — adjust to your checkout.
- `configs/golden50_filter.txt` is the exact 50-task instance filter (portable as-is).
- The only Meta-specific dependency is **PlugBoard** (the mTLS model gateway). Swap `prune_shim.py`'s
  `call_plugboard()` for a direct Anthropic API call (`ANTHROPIC_API_KEY` + `api.anthropic.com`) to
  run fully externally — the pruning logic (`apply_method`) is gateway-agnostic.

No secrets are committed; `ANTHROPIC_API_KEY="shim"` is a dummy (the shim injects real auth at the
PlugBoard egress, not in these files).
