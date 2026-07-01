# SMOKE_TEST_REPORT (Phase B validity gates)

**Cells present:** 18/18  ·  **All gates pass:** True

VALIDITY ONLY — no scientific claims from 5 tasks.

| cell | n_calls | rc | gate | cc_fraction |
|---|--:|--:|:--:|--:|
| sonnet46/C0_identity | 213 | 0 | byte-id ✓ | 0.0347 |
| sonnet46/SHAM | 210 | 0 | byte-id ✓ | 0.0392 |
| sonnet46/HYBRID1_m7_agg2 | 193 | 0 | act ✓ | 0.7881 |
| sonnet46/LINEDEDUP_e4 | 229 | 0 | act ✓ | 0.0368 |
| sonnet46/GENTLE6K_stable | 212 | 0 | act ✓ | 0.0384 |
| sonnet46/CAP1K_stable | 251 | 0 | act ✓ | 0.0591 |
| haiku45/C0_identity | 671 | 0 | byte-id ✓ | 0.0312 |
| haiku45/SHAM | 330 | 0 | byte-id ✓ | 0.0305 |
| haiku45/HYBRID1_m7_agg2 | 329 | 0 | act ✓ | 0.804 |
| haiku45/LINEDEDUP_e4 | 343 | 0 | act ✓ | 0.0281 |
| haiku45/GENTLE6K_stable | 327 | 0 | act ✓ | 0.0326 |
| haiku45/CAP1K_stable | 380 | 0 | act ✓ | 0.0366 |
| gpt55/C0_identity | 151 | 0 | byte-id ✓ | — |
| gpt55/SHAM | 145 | 0 | byte-id ✓ | — |
| gpt55/HYBRID1_m7_agg2 | 199 | 0 | act ✓ | — |
| gpt55/LINEDEDUP_e4 | 167 | 0 | act ✓ | — |
| gpt55/GENTLE6K_stable | 160 | 0 | act ✓ | — |
| gpt55/CAP1K_stable | 255 | 0 | act ✓ | — |

## Exploratory cache_creation_fraction by model (NOT a result)
- **sonnet46**: C0_identity=0.0347, SHAM=0.0392, HYBRID1_m7_agg2=0.7881, LINEDEDUP_e4=0.0368, GENTLE6K_stable=0.0384, CAP1K_stable=0.0591
- **haiku45**: C0_identity=0.0312, SHAM=0.0305, HYBRID1_m7_agg2=0.804, LINEDEDUP_e4=0.0281, GENTLE6K_stable=0.0326, CAP1K_stable=0.0366

## gpt-5-5 cross-provider caveat
- No cache_read/creation estimand (null by design) -> NO cache-tax claim; provider-native cost only.
- Observations arrive as role:tool; the shim tool-view adapter applies frozen transforms (verified activation).