# MRT Confirmatory (Study 2) — Data Audit

Auto-generated from `results/pruning_ab/mrt_confirmatory/analysis_output.json`.
Frozen confirmatory shim, seed 20260702, opus-4.7 temp=0, thinking OFF.

| quantity | value |
|---|---|
| total logged events | 4469 |
| randomized interventions | 70 |
| valid (excl. infra failures) | 70 |
| excluded (infra failure) | 0 |
| arms | {'LINEDEDUP': 36, 'NO_OP': 34} |
| strata | {'HIGH_REDUNDANCY': 30, 'MIXED_REDUNDANCY': 40} |
| repos | 11 (astropy, django, matplotlib, mwaskom, psf, pydata, pylint-dev, pytest-dev, scikit-learn, sphinx-doc, sympy) |
| activation rate (LINEDEDUP changed) | 1.0 |

Stopping rule: precision target (ATE CI half-width<=1000) OR pool exhaustion; never on p-value/trend.
