# Phase 4D/F — Mandatory Robustness & Falsification Checks

The mission required these; running them materially weakens the saving claims. All auto-generated from `robustness.json` + `falsification.json`.

## 1. Leave-top-k-expensive-out (the saving is NOT robust)

| method | full (k=0) | drop top 1 | drop top 3 | drop top 5 |
|--------|---:|---:|---:|---:|
| LINEDEDUP_e4 | +6.3% | **+0.9%** | **−4.0%** | −8.8% |
| GENTLE6K_stable | +10.1% | **+2.5%** | **−7.1%** | −8.4% |

**Both methods' entire aggregate saving comes from 1–3 expensive tasks.** Removing them flips the saving negative. The headline +6.3%/+10.1% are **driven by a handful of high-cost tasks, not a typical task** — they fail the leave-top-k robustness check.

## 2. Cost decomposition (where saving comes from)
LINEDEDUP eff-cost saving by component (units, +=saved): cache_read +196k · cache_creation +77k · output +77k · input +3k → **dominated by cache_read reduction** (prompt genuinely shrank). GENTLE6K similar (cache_read +363k dominant). So *where* saving exists it is real prompt reduction — but §1 shows it exists only on a few tasks.

## 3. ⚠️ SHAM cost negative control — FAILS (critical)
On the A/A 10 tasks (5 reps), **dup_line_ratio predicts SHAM's cost-delta with Spearman = −0.76** — a strong correlation with a **no-op method's** "effect." SHAM also shows +4.0% mean cost-delta despite being byte-identical. → **dup_line_ratio predicts run-to-run cost INSTABILITY, not treatment benefit.** A controller keyed on it would be routing on noise. This is the cleanest falsification of trace-signal predictiveness.

## 4. Repo-cluster bootstrap — saving CI straddles zero
LINEDEDUP overall saving: point +6.3%, **repo-clustered 95% CI = [−9.9%, +18.0%]**. Accounting for repository clustering, the saving is **not statistically distinguishable from zero.**

## Impact on verdicts
These checks downgrade the saving claims:
- The "best static method saves +10.1%" (which DEPLOYABLE_CONTROLLER_VALUE compared against) is itself **non-robust** (vanishes leave-top-3, CI straddles 0).
- TRACE_SIGNAL_PREDICTIVENESS = NOT_SUPPORTED is **strengthened** (SHAM cost control fails at −0.76).
- The honest aggregate-saving claim is: **point estimate positive but not robust to removing a few expensive tasks, and not significant under repo-clustered inference.**
