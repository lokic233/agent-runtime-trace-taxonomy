# Parity-Existence Study — Design

## Question
Do different runtime states require different optimization actions to maximize task-total effective
savings under an explicit quality-loss tolerance? This is an **existence diagnostic + decision gate**,
NOT a learned-policy study. Claims tested in order: (1) tradeoff existence, (2) action-parity
existence, (3) predictability — we do NOT reach (3) unless (1) and (2) pass.

## Data strategy (analysis-first, before any new paid campaign)
The project already contains a **paid task x action matrix**: 6 dose-ordered methods (C0/M4/M6/M7
recency variants) x 50 golden tasks with per-task provider cost + SWE-bench resolution, plus
per-call cache ledgers for C0 + HYBRID1 + SHAM (10 tasks). We first extract maximum signal from
this existing matrix as a **lower-bound existence probe** before spending on a new replicated run.

## Critical noise control
SHAM = a byte-identical NO_OP. SHAM-vs-C0 task-total effective-cost differences are PURE run-to-run
stochasticity (agents diverge even at temp=0). This is the noise floor any real action difference
must exceed. We use it to calibrate a NULL simulation of the oracle gap.

## Precision analysis (why reps matter)
With run-to-run cost sigma ~0.46 (from SHAM), a min-over-4-actions on single draws manufactures a
large apparent oracle gap even if all actions are identical. Detecting a real ~5-10% gap above the
floor needs ~10-20 reps/cell (=> ~3000 paid runs for 50x4). A new campaign is justified ONLY if the
existing-data probe shows a gap that plausibly survives the noise floor.

## Tolerance-conditioned framework (frozen)
F_i(eps) = {a : Q(A0)-Q(a) <= eps}; best feasible a*(eps)=argmin_{a in F} C_i(a).
eps in {0, 0.02, 0.05, 0.10}. Oracle gap = best_static - oracle (lower cost better).
Report naive AND bias-corrected (split-sample + noise-null); aggregate (cost-weighted) AND
equal-weight task-level; repo-clustered; leave-one-repo-out; leave-top-k.
