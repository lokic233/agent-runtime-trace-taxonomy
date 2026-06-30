# Phase B Cross-Model Smoke Test — VALIDITY GATE REPORT

> **VALIDITY-ONLY.** This report verifies plumbing/identity gates over a 5-task smoke. It makes **NO scientific claims**. 5 tasks is far too few for any effect estimate. The `gpt-5-5` cells are a **cross-provider** caveat: GPT exposes no cache decomposition, so there is **no cache estimand** for GPT — cache fields are null *by design*.

**Overall validity gate verdict: FAIL ❌**  (35 failure(s), 1/18 DONE markers)

## ⚠️ RUN ABORTED — only 1 of 18 cells completed

The orchestrator (`run_smoke.sh`, PID 3485171) **DIED** after completing only the first cell
(`sonnet46/C0_identity`). Two distinct bugs caused a total cascade:

### Bug 1 (PRIMARY) — staged `prune_methods.py` deleted mid-run → 11 anthropic cells "SHIM DOWN"
`run_smoke.sh` stages the canonical PM next to the frozen anthropic shim with
`cp "$PM_DIR/prune_methods.py" "$REPO_SCRIPTS/prune_methods.py"` and removes it via
`trap 'rm -f "$REPO_SCRIPTS/prune_methods.py"' EXIT`. That staged copy is now **MISSING**
(`harness/pruning_ab/scripts/prune_methods.py` — gone; the source under
`/data/users/dengcchi/prune_ab/scripts/prune_methods.py` is intact). With it gone, every
anthropic shim crashed at import:
`ModuleNotFoundError: No module named 'prune_methods'` (see `shim_sonnet46_SHAM.log`),
so the 3s `curl` health check failed → **"SHIM DOWN"** for all 5 remaining sonnet46 arms
and all 6 haiku45 arms (11 cells, never launched, 0 paid calls — good).
The most likely trigger: the orchestrator's parent received **SIGTERM** (same session-reap
event that killed the monitor's background blocker), firing the `EXIT` trap that rm'd the file
while child cells were still iterating. The `trap ... EXIT` + long-lived background orchestrator
is fragile.

### Bug 2 — `gpt-5-5` is not a litellm-routable model string → gpt55/C0_identity rc=137
The gpt55 plugboard shim came up (it uses `PB_PM_DIR` env path, not a cwd import, so Bug 1
didn't hit it), but the SWE-agent run failed: litellm rejected the model with
`BadRequestError: LLM Provider NOT provided ... You passed model=gpt-5-5`. After retries the
batch was **Killed (rc=137)**. The arm string `gpt-5-5` needs a provider prefix / litellm
registration (e.g. `openai/gpt-5-5` or a custom provider route) before any gpt55 cell can run.
**No valid gpt55 ledger rows were produced**, so `gpt55_obs_role_layout` could not be observed
(reported as `null`).

### State at abort
- **1/18 DONE**: `sonnet46/C0_identity` only — and it **PASSES all its validity gates** (see below).
- Orphaned podman containers from the dead gpt55 attempt may still be running — left untouched
  (monitor is read-only). Recommend `podman ps` cleanup before any relaunch.
- **No scientific data**; this is a plumbing abort.

### The one good cell (sonnet46/C0_identity) — validity gates PASS
n_calls=213, n_tasks=5, rc=0, **byte-identical ✓** (changed=False on all 213 calls),
**cache_fields_ok ✓** (cache_read/creation populated), cache_creation_fraction=**0.0347**
(sum_cc=238,097 / sum_cr=6,620,664). served_model absent in `prune_shim_v2` ledger (expected).
This confirms the anthropic shim + ledger + C0 identity path are wired correctly.

### Fix recommendations for the parent (do NOT relaunch from monitor)
1. Make PM staging robust: drop the `trap EXIT rm`, or copy `prune_methods.py` into a stable
   location and set `PYTHONPATH` for the anthropic shim too (mirror the gpt55 `PB_PM_DIR` pattern)
   so a parent-process signal can't strip it mid-run.
2. Fix the gpt55 model string to a litellm-routable form (provider prefix or registered route).
3. Guard each cell: re-`cp` the PM (idempotent) immediately before launching each anthropic shim,
   and verify `prune_methods.py` exists before the curl check.
4. Clean orphaned podman containers, then relaunch. DONE-marker resume logic will skip the one
   completed cell.

## Per-cell table

| model | arm | n_calls | n_tasks | rc | served-OK | byte-id (C0/SHAM) | activated | cache-OK | cc_frac |
|---|---|--:|--:|--:|:--:|:--:|:--:|:--:|--:|
| sonnet46 | C0_identity | 213 | 5 | 0 | — | ✓ | — | ✓ | 0.035 |
| sonnet46 | SHAM | 0 | 0 | — | — | ✗ | — | ✗ | — |
| sonnet46 | HYBRID1_m7_agg2 | 0 | 0 | — | — | — | ✗ | ✗ | — |
| sonnet46 | LINEDEDUP_e4 | 0 | 0 | — | — | — | ✗ | ✗ | — |
| sonnet46 | GENTLE6K_stable | 0 | 0 | — | — | — | ✗ | ✗ | — |
| sonnet46 | CAP1K_stable | 0 | 0 | — | — | — | ✗ | ✗ | — |
| haiku45 | C0_identity | 0 | 0 | — | — | ✗ | — | ✗ | — |
| haiku45 | SHAM | 0 | 0 | — | — | ✗ | — | ✗ | — |
| haiku45 | HYBRID1_m7_agg2 | 0 | 0 | — | — | — | ✗ | ✗ | — |
| haiku45 | LINEDEDUP_e4 | 0 | 0 | — | — | — | ✗ | ✗ | — |
| haiku45 | GENTLE6K_stable | 0 | 0 | — | — | — | ✗ | ✗ | — |
| haiku45 | CAP1K_stable | 0 | 0 | — | — | — | ✗ | ✗ | — |
| gpt55 | C0_identity | 0 | 0 | 137 | — | ✗ | — | ✗ | — |
| gpt55 | SHAM | 0 | 0 | — | — | ✗ | — | ✗ | — |
| gpt55 | HYBRID1_m7_agg2 | 0 | 0 | — | — | — | ✗ | ✗ | — |
| gpt55 | LINEDEDUP_e4 | 0 | 0 | — | — | — | ✗ | ✗ | — |
| gpt55 | GENTLE6K_stable | 0 | 0 | — | — | — | ✗ | ✗ | — |
| gpt55 | CAP1K_stable | 0 | 0 | — | — | — | ✗ | ✗ | — |

Legend: ✓ pass · ✗ fail · — not applicable (e.g. byte-id only for C0/SHAM; activated only for transform arms; served-OK — for anthropic = served_model absent in prune_shim_v2 ledger; cc_frac anthropic-only).

## Cache-creation fraction by model (EXPLORATORY — not a result)

> Preview of the cache-tax baseline. Labelled **exploratory**: 5 tasks, no controls, no claims.

- **sonnet46** aggregate cache_creation_fraction = 0.035  (per-arm: C0_identity=0.035, SHAM=—, HYBRID1_m7_agg2=—, LINEDEDUP_e4=—, GENTLE6K_stable=—, CAP1K_stable=—)
- **haiku45** aggregate cache_creation_fraction = —  (per-arm: C0_identity=—, SHAM=—, HYBRID1_m7_agg2=—, LINEDEDUP_e4=—, GENTLE6K_stable=—, CAP1K_stable=—)

- gpt55 obs_role_layout = `None` (expected `user_pleintext`, must NOT be `tool`)

## Anomalies / Failures

- ❌ sonnet46/SHAM: NOT byte-identical (changed=True on 0/0 calls)
- ❌ sonnet46/SHAM: EMPTY ledger
- ❌ sonnet46/HYBRID1_m7_agg2: transform NOT activated (changed_any=False, chars_removed=0, cmc=0)
- ❌ sonnet46/HYBRID1_m7_agg2: EMPTY ledger
- ❌ sonnet46/LINEDEDUP_e4: transform NOT activated (changed_any=False, chars_removed=0, cmc=0)
- ❌ sonnet46/LINEDEDUP_e4: EMPTY ledger
- ❌ sonnet46/GENTLE6K_stable: transform NOT activated (changed_any=False, chars_removed=0, cmc=0)
- ❌ sonnet46/GENTLE6K_stable: EMPTY ledger
- ❌ sonnet46/CAP1K_stable: transform NOT activated (changed_any=False, chars_removed=0, cmc=0)
- ❌ sonnet46/CAP1K_stable: EMPTY ledger
- ❌ haiku45/C0_identity: NOT byte-identical (changed=True on 0/0 calls)
- ❌ haiku45/C0_identity: EMPTY ledger
- ❌ haiku45/SHAM: NOT byte-identical (changed=True on 0/0 calls)
- ❌ haiku45/SHAM: EMPTY ledger
- ❌ haiku45/HYBRID1_m7_agg2: transform NOT activated (changed_any=False, chars_removed=0, cmc=0)
- ❌ haiku45/HYBRID1_m7_agg2: EMPTY ledger
- ❌ haiku45/LINEDEDUP_e4: transform NOT activated (changed_any=False, chars_removed=0, cmc=0)
- ❌ haiku45/LINEDEDUP_e4: EMPTY ledger
- ❌ haiku45/GENTLE6K_stable: transform NOT activated (changed_any=False, chars_removed=0, cmc=0)
- ❌ haiku45/GENTLE6K_stable: EMPTY ledger
- ❌ haiku45/CAP1K_stable: transform NOT activated (changed_any=False, chars_removed=0, cmc=0)
- ❌ haiku45/CAP1K_stable: EMPTY ledger
- ❌ gpt55/C0_identity: transform_fired=True on 0/0 (must be False for C0/SHAM)
- ❌ gpt55/C0_identity: EMPTY ledger
- ❌ gpt55/C0_identity: arm log rc=137
- ❌ gpt55/SHAM: transform_fired=True on 0/0 (must be False for C0/SHAM)
- ❌ gpt55/SHAM: EMPTY ledger
- ❌ gpt55/HYBRID1_m7_agg2: transform_fired never True (0/0)
- ❌ gpt55/HYBRID1_m7_agg2: EMPTY ledger
- ❌ gpt55/LINEDEDUP_e4: transform_fired never True (0/0)
- ❌ gpt55/LINEDEDUP_e4: EMPTY ledger
- ❌ gpt55/GENTLE6K_stable: transform_fired never True (0/0)
- ❌ gpt55/GENTLE6K_stable: EMPTY ledger
- ❌ gpt55/CAP1K_stable: transform_fired never True (0/0)
- ❌ gpt55/CAP1K_stable: EMPTY ledger

