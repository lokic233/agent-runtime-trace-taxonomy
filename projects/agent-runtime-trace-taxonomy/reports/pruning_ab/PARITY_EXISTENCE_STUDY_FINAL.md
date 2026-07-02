# Parity-Existence Study — FINAL

Auto-derived from machine artifacts in `results/pruning_ab/parity_study/`. Existence diagnostic on
existing paid data (6 dose-ordered actions x 50 tasks, single rep/cell) + SHAM noise control.

## Three claims
1. **Tradeoff existence:** PARTIAL. Actions differ in direct token reduction and in cache behavior
   (content-stable A1/A2 preserve cache; aggressive recency busts it). But on **task-total** cost the
   aggressive end LOSES after cache tax, and quality is monotone-decreasing with dose (C0 48 -> M4 47
   -> M6 46 -> M7 44 resolved). There is a cost-quality tradeoff, but it favors KEEP / low dose.
2. **Action-parity existence:** **NOT SUPPORTED.** The apparent 4-way oracle action mix and ~15-22%
   oracle gap are **below the SHAM noise floor** (a byte-identical no-op manufactures a 40.6% gap).
   **0/50 tasks show a stable action crossing.** Ranking fluctuations are run-to-run noise.
3. **Predictability / policy value:** NOT REACHED (gate failed at claim 2). Not tested.

## Verdict: Decision C — No useful parity
Best static = **KEEP (A0)** at every tolerance; aggressive actions lose on both cost (cache tax) and
quality. No credible oracle headroom survives the noise floor. Signal learning is NOT justified.

## What is real (retain) vs killed
- **Retain:** A1 prefix-preserving LINEDEDUP as a **static** low-risk primitive within its eligibility
  region (cache-stable, directionally useful, low quality risk) — but as a fixed policy, not adaptive.
- **Kill:** A2/A3 as adaptive-controller candidates. Aggressive/recency compaction is a net cost
  increase after cache + rework tax.
