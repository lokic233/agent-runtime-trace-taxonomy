# Mechanism B — Intelligence Tax: Causal Test (dose-controlled)

**Question:** Is cost/quality degradation driven by *what* information is removed (unique vs redundant) rather than merely *how much* (token volume)?

## Design (dose-stratified + dose-adjusted regression)
- **Removal TYPE (the treatment of interest):**
  - **redundant** = exact-duplicate-line removal (LINEDEDUP) + retrievable-reference replacement (RETRIEVREF) — information is recoverable / already-seen
  - **destructive** = uniform truncation (CAP1K, CAP500) + signal-line skim (SIGNAL) — drops potentially-unique content
- **Dose** = per-task characters removed (the confound to control)
- **Outcome (drift / intelligence tax proxy):** call_ratio = agent api_calls(method) / api_calls(C0) per task (>1 = agent re-fetches/loops). n=206 task-records.

## Result 1: dose-stratified drift (auto-generated)

| dose bin | redundant drift | destructive drift | n (r/d) |
|----------|------:|------:|:--:|
| 0–5 kchars | 0.91 | 1.15 | 16/6 |
| 5–15 kchars | 0.87 | 1.24 | 9/8 |
| 15–40 kchars | 0.86 | 1.29 | 11/16 |
| 40+ kchars | 1.15 | 1.50 | 29/67 |

**At every dose level, destructive removal causes more drift than redundant removal.** The gap is consistent (≈+0.25–0.43 call-ratio) and does not close as dose varies.

## Result 2: dose-adjusted regression
`drift ~ β₁·dose(kchars) + β₂·is_destructive` (n=206):
- **β₁ (dose) = +0.0001 per kchar** — removal *volume* has essentially **zero** independent effect on drift.
- **β₂ (is_destructive) = +0.415** — removing unique/needed content adds ~0.42 to the call-ratio, **independent of dose**.

## Causal reading
The drift (extra calls → extra cost + regression risk) is **caused by removing information the agent later needs (unique content), not by the number of tokens removed.** Exact-duplicate removal (already-seen lines) and retrievable references preserve the agent's ability to proceed (drift ≈ 1.0); truncation/skim that can sever unique content forces re-derivation (drift 1.15–1.50).

## Confounders & limits
- **Type and dose are correlated** in the raw methods (destructive methods remove more) — addressed by stratification + dose-adjusted regression, both of which isolate type.
- **Not randomized:** removal type is method-determined, not randomly assigned per task. The dose-stratified consistency + near-zero dose coefficient make the type effect credible but **quasi-experimental**, not RCT.
- call_ratio is a drift *proxy*; it correlates with but is not identical to quality regression.
- "redundant" via LINEDEDUP = *exact* duplicate lines; near-duplicate/semantic redundancy not tested here.

## Verdict
**INTELLIGENCE_TAX_CAUSALITY: SUPPORTED** (dose-controlled, consistent across strata, β_dose≈0 vs β_type=+0.42). Drift is driven by removal *type* (novelty/recoverability), not dose — quasi-experimental evidence.
