# Micro-Randomized Trial — Preregistered Protocol

**Status: PREREGISTERED. Frozen before any analysis of trial outcomes.**

## Rationale
Event-level causal effects are UNIDENTIFIED from observational runs (Part 4). The MRT creates matched event-level counterfactuals by randomizing the action at the *same eligible prefix*, with logged propensity for IPW/doubly-robust estimation.

## Identification scope (honest)
- **Cleanly identified: the H=1 local effect** — at a randomized decision, the prefix up to that call is shared across arms, so E[Y₁(action)−Y₁(NO_OP)] is a valid randomized contrast (this call's own billed cost + the immediately-following call's behavior, before deep divergence).
- **Partially identified (drift): H=3 and beyond** — each call re-randomizes, so longer horizons mix many treatments; estimated via the marginal structural / per-decision-randomization framework (effect of treating *this* decision averaged over the random policy on others). Reported with that caveat.
- **Not a whole-task RCT** — we do not claim a clean task-level ATE from the MRT; that's what the task-level study already covered.

## Eligibility (conservative)
Randomize at a call only when: candidate segment (largest current observation) ≥ 2000 chars; action implementation deterministic; original segment retained for rollback; no safety invariant violated.

## Actions & randomization (frozen)
- 50% NO_OP · 25% LINEDEDUP_seg (dedup the candidate segment's already-seen lines) · 25% GENTLE_CAP_seg (cap candidate >6k).
- Per-(task, call_index, seed) deterministic RNG → reproducible; propensity logged.

## Stratification
repository · segment-size bin · dup-ratio bin (prefix) · task phase · calls-so-far bin.

## Features (PREFIX-STATE only, computed at event time)
calls_so_far, context_chars_so_far, n_obs_so_far, largest_obs_so_far, dup_line_ratio_prefix, segment size, segment dup fraction vs prior, repo, task phase. NO full-trajectory or post-treatment values.

## Outcomes
- Primary local cost: incremental eff-cost at H=1 (this call's input+0.1·cr+1.25·cc+5·out).
- Cache: cache_read, cache_creation at H=1.
- Drift/harm proxies (H=1..3): output spike, latency spike, cache_creation spike, repeated tool call.
- Quality: eventual task resolution (task-level, charged to the policy).

## Sample-size target
≥ 300 eligible randomized events (≈ the 50 golden tasks produce ~277+ eligible calls based on observational reconstruction). Stop at task-set completion (all 50 tasks run once under the MRT policy) or 2× for power if compute permits.

## Estimators
- IPW / Horvitz-Thompson for E[Y(action)−Y(NO_OP)] using logged propensity.
- Doubly-robust (AIPW) if outcome model fits.
- Stratified means + cluster-bootstrap by repository.

## Primary outcomes / success criteria
1. Does LINEDEDUP_seg reduce H=1 eff-cost vs NO_OP at the same prefix? (event ATE)
2. Does it raise the harm proxies (reread/repeat/spike)?
3. Does the effect vary with prefix dup-ratio / segment size? (event CATE)
4. Negative control: action label permuted → effect should vanish.

## Safety / stopping
- Original content retained every fire (rollback possible).
- Abort if eligible-event quality (resolution) drops > 20% vs C0 task baseline mid-trial.

## Compute note
Running the MRT = 1 full pass over 50 golden tasks through the MRT shim + grading. ~30-45 min. Feasible tonight.
