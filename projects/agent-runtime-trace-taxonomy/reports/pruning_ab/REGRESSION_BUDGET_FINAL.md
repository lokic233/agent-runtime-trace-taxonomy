# Regression-Budget Cost-Efficiency — FINAL HONEST VERDICT

After 30+ pruning methods across 5 experiments on cached frontier opus-4.7 (golden-50, SWE-bench graded, task-tagged cache-aware effective cost), under the user's **regression-budget framing** (regressions acceptable; rank by cost-efficiency).

## The complete frontier (all graded methods, vs tagged C0 = 46/50)

| method | exp | overall eff-cost saving | raw-prompt saving | regressions | loss_UB | call-ratio | in budget (≤0.11)? |
|--------|-----|------:|------:|:---:|------:|------:|:---:|
| **LINEDEDUP_e4** | 4 | **+6.3%** | **+9.9%** | 5 | 0.207 | 1.00 | ❌ over budget |
| GENTLE6K_stable | 3 | +10.1%¹ | +18%¹ | 1² | 0.094 | 1.04 | ✅ (but ¹variance-inflated) |
| GENTLE4K_stable | 3 | +5.4% | +12% | 1² | 0.092 | 1.00 | ✅ (but median −6%) |
| RETRIEVREF_e4 | 4 | −4.5% | −0.4% | 1 | 0.092 | 1.00 | ✅ but no saving |
| COMBOSS_e4 | 4 | −18.0% | −27.8% | 1 | 0.094 | 1.28 | ✅ but costs more |
| WINCOMBO_e4 | 4 | −10.2% | −4.7% | 3 | 0.152 | 1.00 | ❌ |
| SIGNAL_e4 | 4 | −23.4% | −37.3% | 2 | 0.123 | 1.26 | ❌ |
| SMARTGENTLE_stable | 3 | −9.5% | +9% | 3 | 0.152 | 1.07 | ❌ |
| CAP/SMART (aggressive) | 3 | −12 to −56% | — | — | — | 1.2-2.3 | ❌ drift |
| HYBRID1 (recency) | 1 | −67% | — | — | — | — | ❌ cache-bust |

¹ GENTLE6K's +10.1% is partly trajectory-variance (its top savers are A/A-noise tasks). ² GENTLE's 1 regression is a noise-floor flipper.

## The honest verdict: NO clean regression-budget win

**No method both saves cost AND stays within the loss budget (loss_UB ≤ 0.11) on a statistically-defensible basis.** The frontier splits into two non-overlapping camps:
- **Savers** (LINEDEDUP +6-10%) → blow the regression budget (loss_UB 0.207, 5 reg / 0 imp)
- **In-budget** (RETRIEVREF/COMBOSS/GENTLE, loss_UB ~0.09) → save ~0% or cost more

The closest to a win is **GENTLE6K** (+10.1% overall, loss_UB 0.094) — but its saving is variance-inflated and its per-task median is ~0. The most robust saver is **LINEDEDUP** (+6.3% real, drift-free) — but it carries 5 regressions.

## WHY — the deep, real finding (the publishable result)

On a **cached** frontier agent, the prompt is billed at **0.1× (cache_read)** — it is already ~10× cheap. Therefore:
1. **Any cost saving requires removing content** (you can't save on something already cheap without cutting it).
2. **Removing content regresses ~10% of tasks** — even "redundant" already-seen lines (LINEDEDUP) occasionally remove something the agent re-needed (mild drift on sympy tasks).
3. **The cache makes pruning counterproductive when it rewrites the prefix** (recency methods: cache-bust → 1.25× re-creation → −67%).

**There is no free lunch.** The safe-pruning ceiling that stays within a tight regression budget is **≈ break-even (0%)**; pushing to +6-10% saving costs ~5 regressions. This is a hard, characterized tradeoff — the regression-budget Pareto frontier has no favorable knee on cached frontier models.

## What this means for the controller / Pareto project
The frontier IS the deliverable, and it's now fully mapped:
- **Tight budget (loss_UB ≤ 0.10):** best is ~break-even — pruning offers no reliable cost win. Recommend NO pruning (or RETRIEVREF for safety with ~0 saving).
- **Loose budget (accept ~5 regressions / loss_UB ~0.20 for +6-10% saving):** LINEDEDUP (cross-observation line dedup) is the method — drift-free mechanism, real saving, but lossy on a minority of tasks.
- **Never:** recency pruning (HYBRID1) or content truncation (CAP/SIGNAL) — they cost MORE.

## Honest meta-note
An earlier framing of LINEDEDUP as "1 real regression" over-leaned on excluding A/A-noise tasks. The rigorous raw count is **5 regressions (loss_UB 0.207)** — over budget. The defensible claim is the tradeoff, not a clean win.
