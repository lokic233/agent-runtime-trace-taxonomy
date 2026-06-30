# RUNTIME_PROVENANCE_AUDIT — Phase A

**Goal:** Tie the transform implementation that WILL run to the canonical frozen treatment, and resolve
every harness hazard, before any paid run. Machine-readable: `results/pruning_ab/generalization/runtime_provenance.json`.

## Identity
- repo HEAD: `5b5fc94` · canonical freeze: `bb43b49` (reachable)
- live workspace: `/data/users/dengcchi/prune_ab`
- SWE-agent: commit `d872eb74`, config `250225_anthropic_filemap_simple_review.yaml` sha256 `c9a3eb93…`
- golden-50 filter: `harness/pruning_ab/configs/golden50_filter.txt` (50 ids) · interesting-10: from `interesting10.json`

## ⚠️ THE central provenance finding — three copies of prune_methods.py
| copy | module sha256 | status |
|------|--------------|--------|
| `src/pruning_ab/prune_methods.py` | `cb06efb6…` | **CANONICAL** (matches manifest) |
| `harness/pruning_ab/prune_methods.py` | `536c4ed8…` | **STALE PARTIAL — missing SHAM, LINEDEDUP_e4, GENTLE6K_stable, RETRIEVREF_e4. DO NOT USE.** |
| `/data/users/dengcchi/prune_ab/scripts/prune_methods.py` | `e35b6fbc…` | **LIVE** — the copy the shim actually imported during the frozen runs |

**Resolution (decisive):** per-method **function** SHA-256 for all 6 frozen treatments
(C0, HYBRID1, LINEDEDUP_e4, GENTLE6K_stable, CAP1K_stable, RETRIEVREF_e4) are **byte-identical**
between `src_canonical` and `live_scripts`. The module-hash mismatch is confined to non-treatment code
(helpers, other registry methods, comments). The shim's `sys.path.insert(0, dirname(__file__))` means it
imports the **scripts/** copy — whose treatment functions == canonical. **The runtime transform is tied to
the frozen treatment.** The `harness/` copy is never imported and must not be used (it lacks the e4 set).

Per-method frozen function hashes (authoritative, to be re-logged before every run):
```
C0_identity      50d7379887e1   HYBRID1_m7_agg2  6c9ab8b642bd
LINEDEDUP_e4     d3745ee0e66a   GENTLE6K_stable  b6946b104e2e
CAP1K_stable     7ccec6960f05   RETRIEVREF_e4    03c05e5078e3
```

## SHAM
SHAM is a **shim mode** (`TS_PRUNE_METHOD=SHAM` in `prune_shim_v2.py`), not a `METHODS` entry — identical
deepcopy/normalize/token-count code path, byte-identical output. Its absence from the registry is expected.

## Shims
- `prune_shim_v2.py` (`ddf68b6f…`) — Anthropic format → **PlugBoard `/v1/messages`** via mTLS (`curl --noproxy *`).
  Forwards the body **untouched** (model string comes from `run_arm.sh --agent.model.name`). Sonnet/Haiku
  need only the model-string swap.
- `prune_shim_openai.py` (`832288f5…`) — OpenAI format but targets a **local vLLM**, NOT PlugBoard. GPT-5.5
  needs a **new PlugBoard OpenAI adapter** (forward to `/v1/chat/completions`, mTLS).

## Hazards (all resolved)
1. `run_arm.sh` hardcodes `anthropic/claude-opus-4-7` → **parameterize** `--agent.model.name` (keep Opus replay byte-compatible).
2. `run_arm.sh` cd's into the external SWE-agent checkout → expected; record the path.
3. shim relative import → **resolved** (functions match canonical).
4. E4 launches from `/data/users/dengcchi/prune_ab` → expected; record.
5. two copies differ → **resolved** (use canonical/live; never harness-stale).

## Model routing (all verified live via PlugBoard, served-model identity confirmed)
| requested | endpoint | served | cache fields |
|-----------|----------|--------|--------------|
| claude-sonnet-4-6 | /v1/messages | claude-sonnet-4.6 | YES |
| claude-haiku-4-5 | /v1/messages | claude-haiku-4.5 | YES |
| claude-opus-4-7 (anchor) | /v1/messages | claude-opus-4.7 | YES |
| **gpt-5-5 (PRIMARY)** | /v1/chat/completions | gpt-5-5 | **NO** (prompt/completion/total only) |
| gpt-5-4, gemini-3-1-pro | — | — | fallbacks, **UNUSED** (gpt-5-5 reachable) |

**Cross-provider constraint:** gpt-5-5 exposes no cache_read/cache_creation → use provider-native cost vs
its OWN C0 + physical token/call metrics; **no Anthropic pricing weights**; **cannot** claim cache-tax
replication (no comparable cache-recreation estimand). Matches mission §6.

**No paid runs were issued in Phase A.**
