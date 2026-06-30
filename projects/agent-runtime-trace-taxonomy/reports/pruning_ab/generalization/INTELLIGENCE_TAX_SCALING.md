# INTELLIGENCE_TAX_SCALING (Phase D) — SKELETON

**Hypotheses:** H1 destructive truncation (CAP1K) drift > redundancy-preserving (LINEDEDUP) / gentle (GENTLE6K).
H2 capability interaction: CAP1K-induced intelligence tax LARGER on weaker models.
**Design:** Opus4.7(anchor) + Sonnet4.6 + Haiku4.5 × {C0, LINEDEDUP, GENTLE6K, CAP1K} × 3 reps × 10 tasks.
**Metrics:** API-call ratio, output-token ratio, resolution, repeated reads/cmds/errors (rework vs necessary verification).
**Anchor (Opus):** dose_coef≈0, destructive_coef 0.415; CAP1K call_ratio 1.24 / out_ratio 1.34 vs LINEDEDUP 1.0/0.97.
**Populated from:** intelligence_tax_scaling.json (analyze_intelligence_tax.py).

## Results _[pending Phase D paid run]_
| model | LINEDEDUP call/out | GENTLE6K call/out | CAP1K call/out | CAP1K worst? |
|-------|--------------------|--------------------|-----------------|--------------|
| opus47 | | | | |
| sonnet46 | | | | |
| haiku45 | | | | |

## H2 (capability interaction): CAP1K call_ratio opus → sonnet → haiku _[direction]_
