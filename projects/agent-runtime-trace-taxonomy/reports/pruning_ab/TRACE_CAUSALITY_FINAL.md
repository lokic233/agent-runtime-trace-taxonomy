# TRACE CAUSALITY — Final Report & 8-Part Verdict

**Mission:** Can pre-treatment trace features causally identify when a cache-aware context transformation reduces task-level cost within a quality-regression budget — well enough to support a deployable controller?

**Frozen commit:** `bb43b49` · **All numbers auto-generated** (7/7 consistency assertions pass — see `consistency_assertions.json`). Optimized for hostile-review survival, not a positive story.

---

## THE 8 VERDICTS

```
CACHE_TAX_CAUSALITY:            SUPPORTED
INTELLIGENCE_TAX_CAUSALITY:     SUPPORTED
TRACE_SIGNAL_PREDICTIVENESS:    NOT_SUPPORTED
HETEROGENEOUS_TREATMENT_EFFECT: PARTIALLY_SUPPORTED  (exists; not feature-predictable)
ORACLE_GAP:                     SUPPORTED            (+27% post-hoc; BUT static +10% non-robust, see below)
DEPLOYABLE_CONTROLLER_VALUE:    NOT_SUPPORTED
QUALITY_BUDGET_CALIBRATION:     UNDERPOWERED
CROSS_MODEL_STATUS:             UNDERPOWERED / EXPLORATORY
```

---

## What is CAUSALLY DEMONSTRATED

1. **Cache tax (SUPPORTED).** Rewriting a cached prefix causes the cache-creation cost fraction to rise ~10× (C0=0.077, SHAM=0.066, HYBRID1=0.784; non-overlapping CIs). The **SHAM no-op control** (identical code path, byte-identical output) stays at C0 levels → the tax is caused by *prefix rewriting*, not the shim. Repeated-measures (5 reps × 10 tasks), provider-prompt-cache regime. *(CACHE_TAX_CAUSALITY.md)*

2. **Intelligence tax (SUPPORTED, dose-controlled).** Trajectory drift (extra calls) is caused by removing *unique/needed* content, not by token volume. Dose-adjusted regression: dose coef ≈ 0 (+0.0001/kchar), is_destructive coef = +0.415; destructive > redundant drift at every dose bin. Quasi-experimental (type is method-determined). *(INTELLIGENCE_TAX_CAUSALITY.md)*

## What is ONLY CORRELATED / NOT predictable

3. **Trace-signal predictiveness (NOT_SUPPORTED).** The best candidate feature (dup_line_ratio) predicts LINEDEDUP saving only weakly (Spearman +0.19, CIs span zero) and **FAILS the negative control**: it predicts GENTLE6K (+0.27, which doesn't deduplicate) at least as strongly → it is a general task-structure proxy, not a method-specific effect modifier. Within-repo correlations reverse (sphinx +0.94, sympy −0.37). *(HETEROGENEOUS_TREATMENT_EFFECTS.md)*

4. **Heterogeneity EXISTS but isn't feature-captured (PARTIALLY_SUPPORTED).** Oracle (post-hoc per-task best) saves +27.0% vs +10.1% best-static — large real heterogeneity. But pre-treatment features cannot identify it.

## What is DEPLOYABLE

5. **Controller value (NOT_SUPPORTED).** The best deployable Tier-1 trace policy (dup>0.25→LINEDEDUP) saves +9.3% — **less than simply always using GENTLE6K (+10.1%)** — even with in-sample threshold tuning. Trace signals route no better than a constant choice. *(ORACLE_GAP.md)*

6. **Quality-budget calibration (UNDERPOWERED).** Only 10 tasks have repeated runs. Success-CATE: HYBRID1 vs C0 = +0.00 (mean over 5 reps), SHAM = +0.02 (control validates). **5/10 interesting tasks are intrinsically unstable under C0** → single-run regression flips have *unresolved* causal attribution (the earlier "real reg = 0 via noise-exclusion" framing was RETRACTED in Phase 0). Cannot calibrate a quality budget at this scale. *(success_cate_repeated.json)*

## What remains HYPOTHESIS

7. **Cross-model (UNDERPOWERED/EXPLORATORY).** Cache tax is cache-regime-specific (vanishes uncached, by mechanism). Re-pricing bound suggests pruning saves more uncached (LINEDEDUP +6.3%→+9.6%, GENTLE6K +10.1%→+17.4%), but this reuses opus trajectories — a real weaker model would have different trajectories + higher intelligence tax. Not validated. *(CROSS_MODEL_SMOKE_TEST.md)*

---


## ⚠️ MANDATORY ROBUSTNESS CHECKS (ROBUSTNESS_FALSIFICATION.md) — they weaken the saving claims

1. **Leave-top-k-expensive-out:** LINEDEDUP +6.3%→+0.9%(−1)→−4.0%(−3); GENTLE6K +10.1%→+2.5%(−1)→−7.1%(−3). **All aggregate saving comes from 1–3 expensive tasks; removing them flips it negative.**
2. **SHAM cost negative control FAILS:** dup_line_ratio predicts SHAM (no-op) cost-delta at Spearman −0.76 → the feature tracks run-to-run cost INSTABILITY, not treatment benefit. Cleanest falsification of trace predictiveness.
3. **Repo-cluster bootstrap:** LINEDEDUP +6.3% → 95% CI [−9.9%, +18.0%] (straddles zero).
5. **Leave-one-repo-out controller cross-fit:** trace policy +4.9% out-of-sample (vs in-sample +9.3%) < best-static +10.1% → controller does NOT generalize across repos (leakage-free).
4. **Decomposition:** where saving exists it is real cache_read reduction — but concentrated in a few tasks.

**Net effect:** the aggregate saving numbers are point-positive but **NOT robust**; the controller comparison's static champion is itself fragile. This makes TRACE_SIGNAL_PREDICTIVENESS=NOT_SUPPORTED and DEPLOYABLE_CONTROLLER_VALUE=NOT_SUPPORTED *more* strongly supported, not less.

## Bottom line (survives hostile review)

**Mechanisms are causally established; the controller is not.**

- The cache tax and intelligence tax are real, causally-identified mechanisms explaining *why* methods succeed or fail: cache-busting (recency) is catastrophic; destroying unique content (truncation) causes drift; removing only redundant/recoverable content (LINEDEDUP) is the only safe-ish lever.
- **But pre-treatment trace features do NOT predict the heterogeneous treatment effect well enough to build a calibrated controller that beats the best static method.** The oracle gap is large (+27%), proving the heterogeneity is real and worth capturing — yet the available signals can't capture it (weak correlations, failed negative control, repo-confounded, underpowered at n≈50/10).

**This is a valid NEGATIVE controller result with POSITIVE mechanism results** — exactly the honest outcome the mission anticipated:
> *"The methods exhibit heterogeneous outcomes, but available pre-treatment trace signals do not predict them reliably enough to support a calibrated controller."*

## Honest scientific corrections made this mission
- **RETRACTED** the earlier "real regression = 0 (A/A noise exclusion)" framing as invalid; replaced with repeated-measures success-CATE where data permit, "unresolved attribution" elsewhere.
- **Reconciled** 4 cross-report contradictions (C0 48 vs 46, LINEDEDUP reg 5 vs 2, saving +24% vs +6.3%) to raw-data truth.
- **Distinguished** bill-weighted (+6.3%) from task-weighted (−1.1% median) LINEDEDUP saving — the win is concentrated in a few big tasks, not typical.

## Canonical artifacts
Reports: CAUSAL_DATA_AUDIT, CACHE_TAX_CAUSALITY, INTELLIGENCE_TAX_CAUSALITY, TRACE_FEATURE_DICTIONARY, HETEROGENEOUS_TREATMENT_EFFECTS, ORACLE_GAP, CONTROLLER_PREREGISTRATION, CROSS_MODEL_SMOKE_TEST, this file.
Results (machine-readable): causal_data_manifest, report_reconciliation, mechanism_effects, pre_treatment_features, hte_estimates, controller_policies, success_cate_repeated, consistency_assertions (7/7 pass), untouched_manifest.
