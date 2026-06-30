# GENERALIZATION_PREREGISTRATION — cross_model_generalization_v1

**Frozen at:** Phase A completion, branch `crossmodel-generalization`, before any outcome-bearing run.
**Anchor:** Opus-4.7 canonical artifacts (freeze `bb43b49`), reused — NOT rerun (unless provenance replay fails).
**Scope:** mechanism-generalization + frozen-static-policy transport. NOT a controller-generalization study.
`CONTROLLER_GENERALIZATION` stays **NOT_TESTED — REQUIRES COMPLETED MRT**.

## Research questions
- **Q1 Cache tax** replicates across Claude tiers (Opus→Sonnet→Haiku)?
- **Q2 Intelligence tax** changes (grows?) as capability decreases?
- **Q3** Do frozen Opus-selected static actions transfer **zero-shot** to Sonnet, Haiku, and a peer-frontier model?
- **Q4** Which effects are caused by capability vs provider caching / pricing / tokenization / trajectory?

## Models (frozen)
- Anchor: `anthropic/claude-opus-4-7` (thinking off, temp 0.0, call limit 75) — reuse artifacts.
- Within-provider scaling: `anthropic/claude-sonnet-4-6`, `anthropic/claude-haiku-4-5` — identical route/cache/templates/tools/limit/temp/thinking/tasks/grader; ONLY the backend changes.
- Cross-provider: **`gpt-5-5`** (PRIMARY; verified reachable → fallback chain gpt-5-4 → gemini-3-1-pro is UNUSED). One cross-provider frontier only.

## Frozen treatments (function hashes in RUNTIME_PROVENANCE_AUDIT)
`C0_identity, SHAM, HYBRID1_m7_agg2, LINEDEDUP_e4, GENTLE6K_stable, CAP1K_stable` (+ `RETRIEVREF_e4` secondary).
**No threshold tuning** (LINEDEDUP min-len/threshold, GENTLE6K 6000, CAP1K, HYBRID1 windows, retrieval format are FROZEN). Zero-shot transport only. Any retuning is a separately-labeled later study.

## Task sets (frozen)
- Cache/intelligence tax: the exact **interesting-10** repeated-measures tasks (listed in runtime_provenance.json).
- Static-policy transport: **golden-50** (regex filter, 50 ids). Start at **30** preregistered, expand to 50 only after adapters+grader pass, no silent model switch, first-30 instrumentation valid.

## Estimands
- **Cache tax (Q1):** `cache_creation_fraction = cache_creation/(cache_creation+cache_read)`. Contrast: C0≈SHAM ≪ HYBRID1. Per-model, 5 reps × 10 tasks. Cross-provider: NOT computed for gpt-5-5 (no comparable estimand) — report physical cached-token share only if exposed.
- **Intelligence tax (Q2):** dose-controlled drift — API-call ratio, output-token ratio, repeated reads/cmds/errors, no-progress rework vs necessary verification; capability interaction = CAP1K drift larger on weaker models. Opus/Sonnet/Haiku, same 10 tasks, 3 reps (→5 if inconclusive), arms C0/LINEDEDUP/GENTLE6K/CAP1K.
- **Policy transport (Q3):** per model, effective-cost (Anthropic decomposition for Claude; provider-native vs own-C0 for gpt-5-5) for C0/LINEDEDUP/GENTLE6K/CAP1K on golden-50; report full-set + common-support set (common support defined from C0 runs **before** viewing treatment outcomes).

## Three transport concepts (kept distinct)
mechanism transport (direction survives) ≠ effect-size transport (magnitude similar) ≠ policy transport (frozen action still useful). A mechanism may transport while the policy does not.

## Verdict vocabulary
SUPPORTED / PARTIALLY_SUPPORTED / NOT_SUPPORTED / UNDERPOWERED / NOT_IDENTIFIABLE / EXPLORATORY.

## Forbidden conclusions (hard gates)
- learned controller generalizes · trace features identify optimal action · duplicate ratio is a causal moderator · large observations inherently waste · MRT unnecessary · single-run regression is discardable noise. `CONTROLLER_GENERALIZATION = NOT_TESTED`.

## Phase order & gates
A (this) → B 5-task smoke (validity only, no claims) → C cache-tax (Sonnet/Haiku) → D intelligence-tax (Opus/Sonnet/Haiku) → E static-policy transport (Sonnet/Haiku/gpt-5-5, 30→50) → optional RETRIEVREF. Each phase passes consistency gates before the next. C0 & SHAM byte-identity asserted every run; transform module+function hashes logged every run.

## Cost discipline
Smoke = 5 tasks × 6 arms × 3 models = 90 agent runs (≤75 calls each). No full paid phase launches until A's 3 artifacts pass internal checks (DONE: 14/14 reconstruction + provenance tied to canonical). Checkpoint with the user before paid phases.

## ⚠️ Preflight finding (Phase A engineering) — OpenAI-format transform no-op hazard
The frozen `_is_obs()` recognizes observations only as Anthropic `user`+`tool_result` blocks OR plain
`{role:user, content:str}`. Empirically:
- SWE-agent v1.0 with the frozen config emits **plain-text `{role:user}` observations** → transforms FIRE for all providers (verified: LINEDEDUP/GENTLE6K/CAP1K all change byte counts).
- BUT if function-calling tool-role messages are emitted (`role:"tool"`, agents.py:715), `_is_obs` returns False → **all transforms silently NO-OP** → a fake "no effect" result.
**Mitigation (no frozen code changed):** the gpt-5-5 shim logs `transform_fired` + `obs_role_layout` on every call; Phase B MUST gate on `transform_fired==True` for non-C0 arms on every provider. If GPT runs route through tool-role layout, that is an instrumentation failure to fix in the adapter (Anthropic-view transform), NOT a scientific "no effect". `_is_obs` is FROZEN and never edited.

## Phase B abort #1 — three infra bugs fixed (no frozen code touched; re-launch pending)
First smoke launch aborted after 1/18 cells. Root causes + fixes (all validated by re-probe):
1. **PM staging/trap** (11 anthropic cells "SHIM DOWN"): `run_smoke.sh` cp'd prune_methods.py next to the
   repo shim and `trap rm EXIT` deleted it mid-run. **FIX:** run all shims FROM the live
   `/data/users/dengcchi/prune_ab/scripts/` dir, where prune_methods.py (functions == frozen) and the
   byte-identical prune_shim_v2.py (ddf68b6f) already co-locate. Removed the cp + trap entirely.
2. **litellm provider prefix** (gpt55 BadRequestError): `gpt-5-5` → litellm "LLM Provider NOT provided".
   **FIX:** model string `openai/gpt-5-5`; shim strips the `openai/` prefix before forwarding to PlugBoard.
3. **litellm cost map** (gpt55 rc=137 after 1 call): `completion_cost` raised "This model isn't mapped yet"
   → ModelConfigurationError. **FIX:** `--agent.model.litellm_model_registry=configs/litellm_gpt5_registry.json`
   (registers gpt-5-5 cost so the harness resolves; AUTHORITATIVE cost remains provider-native token counts
   per §6). Re-probe: gpt-5-5 ran 26 calls, $0.41, prediction written, C0 byte-identical.
4. **gpt-5-5 tool-role observations** (the preflight hazard, now CONFIRMED LIVE): gpt uses `role:tool`
   observations on 25/26 calls; frozen `_is_obs` would NO-OP treatments → fake "no effect". **FIX (no frozen
   edit):** the gpt shim's `_apply_with_tool_view` presents role:tool obs AS role:user to the FROZEN
   apply_method, then restores roles + tool_call_ids. Re-probe LINEDEDUP on tool-role: transform_fired=True,
   characters_removed=2086, frozen LINEDEDUP hash d3745ee0 logged. Anthropic path uses plain-text obs (fires
   natively, no adapter). `_is_obs` is FROZEN and untouched.

Validated single cells: Sonnet-4.6/C0 (14 calls, cc_fraction 0.169, byte-identical); gpt-5-5/C0 (26 calls,
byte-identical); gpt-5-5/LINEDEDUP tool-role (transform fires). Smoke re-launch will resume past DONE markers.
