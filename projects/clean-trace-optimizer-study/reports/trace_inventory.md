# Trace Inventory — clean-trace-optimizer-study

Total traces: **3432** across **500** distinct tasks, **12** repos, **6** harnesses.

## Trace count by solver

| solver | model_hint | harness | role | n | resolve rate |
|---|---|---|---|---|---|
| solver_A | opus-4.7 | SWE-agent-1.0(HAL) | development | 466 | 79.8% (371/465) |
| solver_B | opus-4.5 | live-SWE-agent | development | 500 | 80.0% (396/495) |
| solver_C | sonnet-3.5 | SWE-agent-1.0 | development | 500 | 34.6% (168/485) |
| solver_E | SWE-agent-LM-32B(ft) | SWE-agent-LM | ood_finetuned | 500 | 40.5% (201/496) |
| solver_F | opus-4.6 | SWE-agent-1.0(HAL) | capability_audit | 466 | 74.6% (346/464) |
| solver_G | Skywork-SWE-32B | OpenHands | ood_openhands | 500 | 38.9% (190/489) |
| solver_H | EntroPO-Qwen3-30B | OpenHands/R2E | ood_openhands | 500 | 53.5% (261/488) |

## Coverage & integrity

- resolved-label coverage: 3382/3432 (98.5%)
- action-count availability: 3431/3432
- parser failures: 0
- duplicate trace_ids: 0
- NOTE: raw token counts (prefill/decode) are NOT in these trajectory files; `total_tokens` proxy = n_actions/n_steps (action-step count). The HAL ledger has true tokens for A/F only; cost_estimate exists for B. Token cost analysis uses n_actions as the available cost proxy and flags this limitation honestly.

## Source harness distribution

- SWE-agent-1.0(HAL): 932
- live-SWE-agent: 500
- SWE-agent-1.0: 500
- SWE-agent-LM: 500
- OpenHands: 500
- OpenHands/R2E: 500

## Top repos

- django: 1617
- sympy: 525
- sphinx-doc: 308
- scikit-learn: 224
- matplotlib: 170
- astropy: 154
- pydata: 154
- pytest-dev: 133
- pylint-dev: 70
- psf: 56
- mwaskom: 14
- pallets: 7

## Confound warning

Solver and harness are **partially confounded**: opus-4.5=live-SWE-agent, opus-4.7/4.6=SWE-agent-1.0(HAL), sonnet-3.5=SWE-agent-1.0, 32B-class=OpenHands/SWE-agent-LM. Per the spec, solver-capability differences must NOT be read off raw prevalence without controlling for harness and task. All correlation models include solver + harness + repo + task FE.