# MRT Confirmatory (Study 2) — Controller Policy Value

Hajek self-normalized IPW (primary) + DR cross-fit (LORO). Lower cost = better. Frozen policies.

| policy | Hajek IPW | DR-LORO |
|---|---:|---:|
| pi_keep (always NO_OP) | 6455.0 | 6434.0 |
| pi_static (always LINEDEDUP) | 5460.0 | 5468.0 |
| pi_signal (dup_frac>0.40) | 6186.0 | 6229.0 |

- best static (Hajek): pi_static · best static (DR): pi_static
- pi_signal beats BOTH statics (Hajek): **False** · (DR): **False**

Controller value SUPPORTED only if pi_signal beats both statics on the primary estimator with
credible uncertainty and no quality collapse. Verdict: **NOT_SUPPORTED / UNDERPOWERED**.
