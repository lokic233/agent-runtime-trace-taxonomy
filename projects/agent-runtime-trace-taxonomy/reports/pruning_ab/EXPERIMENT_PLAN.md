# Safe Pruning A/B Experiment — opus-4.7 golden cases

**Goal:** Empirically test which context-pruning methods are SAFE (token-saving AND
non-regressional) on opus-4.7's resolved SWE-bench cases. Turn the heuristic opportunity
map into PAIRED config_outcomes (upgrades PARETO_POLICY_DATA_VERDICT toward EMPIRICAL).

## Apparatus
- Pruning applied at the SHIM (prune_shim.py) on the Anthropic `messages` wire body, per
  TS_PRUNE_METHOD env. Agent keeps full history; the MODEL sees pruned context only.
- One shim per method on its own port -> one SWE-agent run over the golden set -> grade.
- Faithful re-run: temperature=0.0 (matches original full_opus47 generation), SWE-agent-1.0,
  opus-4.7 via PlugBoard.

## Golden set
- 50 cases, stratified EVENLY across repos (6 each x 8 repos + 2 singletons) from opus-4.7's
  371 resolved instances. /tmp/golden50.json. (vs natural 197-django skew.)
- Screening wave = 12 cases (>=1 per repo) to kill bad arms cheaply before the full 50.

## Methods (safety-graded; TokenSaver RULER + ARO priors)
| arm | method | prior |
|-----|--------|-------|
| C0_identity | no prune (baseline control) | — |
| M1_dedup_exact | replace identical repeated observations w/ pointer | LOSSLESS |
| M2_stale_read_elide | elide file-read superseded by later read/edit | keeps latest |
| M3_obs_cap_10k | bound any obs to 10k chars (head+tail) | bounded |
| M4_obs_cap_5k | bound to 5k | more aggressive |
| M5_search_head | keep first 20 hits + count for search results | acts-on-first prior |
| M6_env_log_collapse | collapse SUCCESSFUL build/env logs; keep failures | low-reference |
| M7_old_obs_elide | clear tool-obs older than last 8 actions (Anthropic context-editing) | industry pattern |
| CNEG_recency | last-N-turns window | NEGATIVE CONTROL — TokenSaver: 0.88->0.16. MUST be killed. |

## Kill rule (per arm)
On the 12-case screen: KILL if (regressions > 0) OR (median token-saving <= 0). A method that
breaks a resolved case OR inflates tokens is stopped immediately. CNEG_recency is expected to die.

## Outcome (paired vs C0 re-run, per case)
- regression_event = baseline_resolved AND NOT candidate_resolved
- token_saving_fraction = (baseline_prompt_tokens - candidate)/baseline
- GLOBAL-SAFE = 0 regressions + saving>0 across all 50
- REGIONAL-SAFE = safe on an identifiable stratum (repo / trace-length / search-vs-edit-heavy)
  but not globally -> report the safe region.

## Parallelization (5 nodes)
- devgpu014 (cert, shim, podman, 17TB): primary — runs several arms.
- devvm14382 / devvm14202 (cert? podman): additional arms if cert+egress confirmed.
- devgpu499 (MI350X): aux if container egress works.
- mac: orchestration/monitoring only.
Each arm = independent shim port + output dir; grade with the SWE-bench harness (network=none).

## HONESTY
- This produces REAL paired outcomes (not shadow). A method is "safe" only by measured
  0-regression + positive saving on real re-runs + grading.
- Context-DELETION arms (M3/M4/M7/CNEG) carry the TokenSaver regression risk; the kill-switch
  is the safety net. LOSSLESS arms (M1/M2/M6) are the a-priori safest.

## VALIDATION RESULTS (2026-06-29, apparatus green)
- Apparatus PROVEN: opus-4.7 -> prune_shim -> PlugBoard, end-to-end, 1 golden task resolved clean (rc=0, $0.21).
- Infra fixes (all required): (1) pyhooks sitecustomize DELETES proxy env — inherited NO_PROXY has [::1]
  which breaks litellm/httpx "Invalid port ':1]'"; (2) litellm.drop_params=True (opus-4.7 rejects temp!=1);
  (3) shims launched via the bash background tool (systemd-run --user silently drops them; nohup gets SIGTERM'd);
  (4) prune transforms must operate on tool_result BLOCK content (obs live in user-msg tool_result blocks,
  NOT top-level text) — fixed _txt/_set_obs_text/_is_obs.
- PRUNE-YIELD on 8 golden opus-4.7 traces (median % cut): M1/M2/M5 0% (frontier traces have no exact-dup
  reads / stale rereads / huge search dumps), M3 0%(max11%), M4 0%(max35%), M6 0%(max13%), M7 33.6%,
  CNEG 52%. KEY: clean frontier SUCCESS traces have little SAFE headroom — the lossless methods barely fire.
- IMPLICATION: the scientific result is likely "frontier success traces are near-Pareto-efficient; only
  aggressive (regression-risky) cuts save materially." Still worth proving with paired A/B + the kill-switch.

## REFINED LAUNCH (token-efficient)
- Keep the arms that actually prune: C0(control), M4_obs_cap_5k, M7_old_obs_elide, M3_obs_cap_10k,
  M6_env_log_collapse, CNEG_recency(neg control). Run M1/M2/M5 too but expect ~0 cut (cheap to include;
  they'll register as trivially-safe-but-useless).
- Screen on 12 tasks first; kill any arm with regression>0 OR median token-saving<=0 (M1/M2/M5 will be
  killed for ~0 saving; CNEG for regressions). Survivors -> full 50.
