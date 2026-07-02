# MRT Confirmatory (Study 2) — Robustness & Falsification

## Placebo distribution (5000 deterministic placebos)
- real b3 = -260.9; |b3_real| percentile in placebo dist = 91.7%
- placebo b3 quantiles: {'5': -4170.928609102791, '50': 19.068533520227664, '95': 4172.030148036424}

## Threshold sensitivity (pi_signal, Hajek cost)
{
 "0.3": {
  "hajek": 5888.7262500000015
 },
 "0.4": {
  "hajek": 6186.256944444445
 },
 "0.5": {
  "hajek": 6222.913888888889
 }
}

## Leave-top-k ATE(H1)
{
 "k=1": -701.662626262626,
 "k=3": -239.51326164874627,
 "k=5": -188.427380952382
}

## Leave-one-repo-out ATE(H1)
{
 "drop_astropy": -856.5667644183777,
 "drop_psf": -929.9202020202019,
 "drop_sympy": -820.1627380952386,
 "drop_scikit-learn": -1041.0531250000004,
 "drop_pydata": -1009.2874551971327,
 "drop_django": -1303.4449074074064,
 "drop_mwaskom": -931.0411764705896,
 "drop_pylint-dev": -995.747878787879,
 "drop_sphinx-doc": -929.6415476190477,
 "drop_pytest-dev": -1388.1242424242428,
 "drop_matplotlib": -749.070303030303
}

## Mechanism decomposition (mean LINEDEDUP vs NO_OP)
{
 "cache_creation": {
  "mean_LINEDEDUP": 1692.8333333333333,
  "mean_NOOP": 2311.794117647059,
  "diff": -618.9607843137258
 },
 "cache_read": {
  "mean_LINEDEDUP": 16192.805555555555,
  "mean_NOOP": 14870.735294117647,
  "diff": 1322.070261437908
 },
 "output_tokens": {
  "mean_LINEDEDUP": 344.75,
  "mean_NOOP": 415.44117647058823,
  "diff": -70.69117647058823
 },
 "input_tokens": {
  "mean_LINEDEDUP": 1.0,
  "mean_NOOP": 1.0,
  "diff": 0.0
 }
}
