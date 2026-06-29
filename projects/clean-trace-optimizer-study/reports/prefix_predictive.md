# Prefix Predictive Check (online-relevant)

Can EARLY clean features (first T actions) predict eventual non-convergence (top action-count quartile)?
This is what an ONLINE selector would key on. GroupKFold by task. Compared vs prefix-length-only.

| prefix | nonconv AUROC (features+len) | nonconv AUROC (len only) | feature lift |
|---|---|---|---|
| T5 | 0.624 | 0.5083 | 0.1157 |
| T10 | 0.7039 | 0.5623 | 0.1416 |
| T20 | 0.8271 | 0.7275 | 0.0996 |

## Interpretation
- If feature+len AUROC > len-only at the SAME prefix, early clean features carry online signal beyond
  'the trace is already long'. This is the most decision-relevant prefix result for a controller.
- Honest caveat: non-convergence here is an action-count quartile (self-referential to length), so a
  positive lift means the BEHAVIORAL features (search-no-new-evidence, stagnation, mech-failure) add
  information about WHICH early traces blow up, beyond raw early length.