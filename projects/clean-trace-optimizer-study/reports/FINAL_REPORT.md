# FINAL REPORT — Clean-Room Trace-Conditioned Agent Runtime Optimizer Study

**Lane:** independent clean-room (own loader/classifier/feature code; research-os as engine/verifier ref).
**Node:** cli:devvm14382 (analysis) + cli:devgpu014 (raw opus traces, Qwen host).
**Scope honesty:** Phases A–D + correlation + ablation + post-hoc comparison + audits are FULLY EXECUTED.
Phase E (paired interventions), the 8B/LoRA controllers, and the Qwen held-out validation are
SPEC'd + registered but **NOT executed** (they require re-running SWE-agent hundreds of times against a
live solver + training an 8B — beyond this window). Per the study's own §29 rule, those are marked
**PAIRED_OUTCOMES_PENDING** with no fabricated efficacy. Qwen stays **SEALED**.

---

## §27 Questions

**Which traces were available?** 7 solver trace sets on SWE-bench Verified, 3432 traces, 500 tasks, 12 repos:
solver_A opus-4.7 (466, HAL, graded 74.2%), solver_B opus-4.5 (500, live-SWE-agent, 80.0%),
solver_C sonnet-3.5 (500, SWE-agent-1.0, 34.6%), solver_E SWE-agent-LM-32B (500, 40.5%, fine-tuned),
solver_F opus-4.6 (466, HAL, 74.6%), solver_G Skywork-SWE-32B (500, OpenHands, 38.9%),
solver_H EntroPO-Qwen3-30B (500, OpenHands, 53.5%). 466 tasks shared by ALL 7.

**Which traces were used for development?** Core resolution cohort = A/B/C (instruct-agents spanning
35→80%). E/G/H + F used as OOD-robustness/secondary. Feature design used a seeded stratified 120-trace
manual sample.

**Which data remained held out?** Qwen2.5-Coder-32B-Instruct-AWQ — SEALED. No Qwen agent trace exists
yet (solver is hosted on vLLM:8001 but was never run as an agent). Config frozen, traces neither
generated nor inspected.

**Which existing reports were blocked during clean-room discovery?** per_model_opportunity.md,
opportunity_analysis.json, compute_opportunity.py, waste_to_intervention_map.yaml,
extract_deterministic_features.py, waste_taxonomy_v1.yaml, per-model mappings. Opened ONLY after
Phase-1 freeze, for post-hoc comparison. **Honest disclosure:** operator-requested reading of prior
session transcripts incidentally surfaced the per-model opportunity tables; features were nonetheless
defined independently in clean code, and negative controls + skeptic review quantify the independence.
(reports/source_access_log.md)

**How many traces were manually inspected?** 120 (seeded stratified across solver × resolved × token
tertile × behavior axes), yielding 53 grounded observation-sequences + 45 healthy-iteration sequences
+ 4 harness-artifact flags (audits/raw_trace_memos.jsonl).

**Which candidate signals were proposed?** 6 families → 9 deterministic features: SEARCH_NO_NEW_EVIDENCE_RATE,
REDUNDANT_REREAD_RATE, OVERSIZED_THEN_NARROW_READ_RATE, NO_EVIDENCE_PATCH_CHURN_RATE,
EDIT_MECHANICAL_FAILURE_RATE, POST_EDIT_TEST_GAP, STAGNATION_FRACTION, TOOL_ERROR_RATE, ENVIRONMENT_SETUP_RATE.

**Which signals were rejected/downgraded?** REDUNDANT_REREAD_RATE downgraded to secondary (duplicate reads
≠ context bloat without bloat evidence). NO_EVIDENCE_PATCH_CHURN was SPLIT after the skeptic caught it
conflating reasoning churn with editor mechanical failure (a trace had 43 edits ALL "No replacement
performed"); EDIT_MECHANICAL_FAILURE_RATE was carved out, and churn restricted to applied + evidence-gated edits.

**What was detector precision?** SEARCH_NO_NEW_EVIDENCE 0.895, OVERSIZED_THEN_NARROW 1.0,
NO_EVIDENCE_PATCH_CHURN 1.0, TOOL_ERROR 0.835, STAGNATION 1.0 (all ≥0.80 gate). POST_EDIT_TEST_GAP is a
deterministic definitional measure (precision structurally 1.0).

**Which signals collapsed into trace length?** NONE collapsed (max |Spearman vs n_actions| = 0.54 for the
already-secondary redundant_reread; all others ≤0.39). BUT for predicting COST (action-count) the features
add ~0 out-of-sample beyond n_events — see ablation.

**Which signals were harness-specific?** OVERSIZED_THEN_NARROW concentrated in solver_E; ENVIRONMENT_SETUP
is a harness signal (HAL runs build in-trace; live-SWE-agent/OpenHands pre-build) — never read as solver
behavior. solver_C churn flagged harness-contaminated (_split_string future-annotations bug, 22% of its
edits mechanically failed). eta²_harness ≤0.18 for all features (not harness-dominated).

**Which signals correlated with token (action) cost?** All BH-significant in-sample: stagnation_fraction
(β=+0.32), redundant_reread (+0.34), search_no_new_evidence (+0.20), churn (+0.07), tool_error (+0.09).

**Which signals correlated with resolution?** (CORE A/B/C, CI-significant): stagnation_fraction (β=-0.30),
redundant_reread (-0.34), search_no_new_evidence (-0.36) — all "more signal → less likely resolved".

**Did clean features improve OOS prediction beyond solver/harness/repo/length?**
- COST: NO. Model A(n_events) R²=0.9974 → B(+meta) 0.9985 → C(+features) 0.9986. ΔC-over-B = +0.0001.
- RESOLUTION: BARELY. A AUROC 0.648 → B 0.809 → C 0.812. ΔC-over-B = +0.0023. The dominant signal is the
  SOLVER (already in B).

**Which signals predicted intervention benefit?** UNTESTED — requires paired outcomes (PENDING).

**Did matched signal × intervention interactions hold?** UNTESTED (PENDING). Hypotheses pre-registered.

**Did the trace selector beat global best?** UNTESTED (PENDING). Selector code path implemented + dry-run;
no efficacy claimed.

**How much oracle headroom was captured?** N/A (no paired outcomes).

**What regression cost was paid?** N/A (no paired outcomes).

**Did the result transfer to Qwen2.5-Coder-32B-Instruct-4bit?** UNKNOWN — SEALED. No Qwen traces exist.

**Did semantic annotation add incremental value?** NOT_YET_TESTED (annotation is a pilot, ~58–120 traces,
weak agreement, incomplete). Post-hoc directional comparison: clean detectors REPRODUCE the prior heuristic's
per-model ranking on STAGNATION (ρ=+0.95) and VERIFICATION (ρ=+0.74), but DIVERGE on PATCH_CHURN (ρ=-1.0),
CONTEXT_BLOAT (ρ=-0.8), SEARCH (ρ=-0.6) — and the clean definitions are stricter/better (see below).

**Did LoRA beat the prompted base model?** UNTESTED (controllers not built this window).

**Which claims remain heuristic?** All intervention/selector/Pareto claims. The opportunity-style "where to
intervene" ranking remains heuristic. Only the correlation + prefix-prediction + post-hoc comparison are
empirically grounded here.

---

## Headline empirical findings (what IS grounded)

1. **Cost is trajectory length.** Action-count is ~perfectly predicted by event-count; behavioral features
   add nothing OOS. A "token-saving" story cannot lean on these features for cost prediction.

2. **Resolution is mostly the solver.** Solver+harness+repo+length gets AUROC 0.81; clean features add
   +0.002. Behavioral features carry resolution info in-sample but it's largely redundant with model identity.

3. **The genuinely actionable signal is NON-CONVERGENCE, and it's a PREFIX signal.** Early behavioral
   features beat early-length-only at predicting eventual blow-up: T5 AUROC 0.62 vs 0.51 (+0.11),
   T10 0.70 vs 0.56 (+0.14), T20 0.83 vs 0.73 (+0.10). This is exactly what an online controller would key
   on — and it is NOT explained by "the trace is already long."

4. **Clean-room caught a real measurement error in the prior heuristic.** The prior PATCH_CHURN ranking was
   inflated by editor mechanical-failure retries + lacked an evidence gate; sonnet-3.5 (22% mechanically-failed
   edits) was mis-ranked as high-churn. The clean, evidence-gated, mechanical-failure-split churn INVERTS the
   ranking (ρ=-1.0) and is the defensible one for any PATCH_GUARD intervention.

---

## REQUIRED VERDICTS

CORRELATION_VERDICT:                 INCREMENTAL_SIGNAL (resolution, WEAK) / TRACE_LENGTH_ONLY (cost)
TRACE_SIGNAL_VERDICT:                ASSOCIATIVE_ONLY  (ACTIONABLE requires paired outcomes -> PENDING;
                                     prefix non-convergence prediction is the strongest actionable lead)
INTERVENTION_HETEROGENEITY_VERDICT:  NOT_SUPPORTED (UNTESTED — no paired outcomes; do not claim)
TRACE_SELECTOR_VERDICT:              PENDING (no paired outcomes; code path dry-run only)
LORA_VERDICT:                        NOT_YET_TESTED (controller not built)
QWEN_TRANSFER_VERDICT:               PENDING (SEALED; no Qwen traces generated)
SEMANTIC_ANNOTATION_INCREMENTAL_VALUE: NOT_YET_TESTED (pilot only; directional agreement, not incremental value)
PARETO_POLICY_DATA_VERDICT:          NOT_EMPIRICALLY_GROUNDED (no paired config outcomes)

---

## What it would take to finish (registered, not done)
1. Implement the 3 configs against the live runtime; run 80-task × 4-config paired experiments on ≥1 dev solver.
2. Build prompted-8B + LoRA controllers; tune+freeze selector thresholds on paired data.
3. Phase-2 freeze; THEN generate Qwen traces (SWE-agent vs hosted Qwen under frozen config) and run the
   held-out paired validation. Only then can TRACE_SELECTOR / HETEROGENEITY / QWEN_TRANSFER be answered.

## The strongest honest statement this study supports
A small set of deterministic, inspection-grounded trace features predicts agent NON-CONVERGENCE from a
short PREFIX better than trajectory length alone (T10 AUROC 0.70 vs 0.56). For final COST and RESOLUTION,
the features are largely redundant with trajectory length and solver identity. Whether acting on the
non-convergence signal with a matched runtime intervention actually saves tokens without regressing
solve-rate — and whether that transfers to a 4-bit Qwen solver — REMAINS UNPROVEN and is the registered
next experiment.
