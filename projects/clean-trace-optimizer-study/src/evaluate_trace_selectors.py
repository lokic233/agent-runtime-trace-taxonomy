#!/usr/bin/env python3
"""evaluate_trace_selectors.py — DETERMINISTIC selector + ablation harness.
STATUS: plumbing-only. No real paired config outcomes exist this window, so we DRY-RUN the selector
logic and the comparison harness on a clearly-labeled SIMULATED outcome model to prove the code path,
and we EMIT NO efficacy claim. Real efficacy is PAIRED_OUTCOMES_PENDING.
Also builds the required task-list manifests + dataset_split.json.
"""
import json, os, numpy as np, pandas as pd
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
df=pd.read_parquet(os.path.join(ROOT,'data','baseline_trace_feature_table.parquet'))
np.random.seed(20260628)

# ---- dataset_split.json: dev cohort vs aux vs sealed-qwen, by solver; task-grouped ----
split=dict(
  development_resolution_cohort=['solver_A','solver_B','solver_C'],
  capability_audit=['solver_F'],
  ood_robustness=['solver_E','solver_G','solver_H'],
  heldout_sealed=['solver_QWEN (no traces yet)'],
  split_rule='GroupKFold(5) by task_id for all CV; all traces of a task in one fold',
  n_tasks=int(df['task_id'].nunique()),
  shared_all_solvers=466)
json.dump(split, open(os.path.join(ROOT,'manifests','dataset_split.json'),'w'),indent=1)

# ---- intervention + qwen task manifests (the 466 shared tasks are the candidate pool) ----
shared=sorted(df.groupby('task_id')['solver_alias'].nunique().pipe(lambda s:s[s==7]).index)
# deterministic 80 for dev intervention, disjoint 80 reserved for qwen (task-novel)
rng=np.random.RandomState(20260628); perm=list(shared); rng.shuffle(perm)
dev_tasks=sorted(perm[:80]); qwen_tasks=sorted(perm[80:160])
with open(os.path.join(ROOT,'manifests','development_intervention_tasks.jsonl'),'w') as f:
    for t in dev_tasks: f.write(json.dumps(dict(task_id=t, pool='development_intervention', configs=['DEFAULT','SEARCH_CONSTRAINED','PATCH_GUARD','VERIFY_HEAVY'], status='PENDING_PAIRED_RUN'))+'\n')
with open(os.path.join(ROOT,'manifests','qwen_validation_tasks.jsonl'),'w') as f:
    for t in qwen_tasks: f.write(json.dumps(dict(task_id=t, pool='qwen_heldout', solver='solver_QWEN', status='SEALED', note='task-disjoint from dev intervention pool'))+'\n')

# ---- deterministic selector (frozen-feature rule) — code path only ----
def deterministic_selector(prefix_feats, risk='MEDIUM'):
    """Return a config_id from FROZEN clean prefix features. Conservative, fallback=DEFAULT.
    Thresholds are illustrative defaults; REAL thresholds get set/validated only with paired data."""
    s=prefix_feats.get('search_no_new_evidence_rate')
    c=prefix_feats.get('no_evidence_patch_churn_rate')
    g=prefix_feats.get('post_edit_test_gap_undefined')  # bool: no post-edit test
    th={'LOW':(0.7,0.6),'MEDIUM':(0.5,0.4),'HIGH':(0.35,0.3)}[risk]
    if s is not None and s>=th[0]: return 'SEARCH_CONSTRAINED'
    if c is not None and c>=th[1]: return 'PATCH_GUARD'
    if g: return 'VERIFY_HEAVY'
    return 'DEFAULT'

# DRY-RUN on SIMULATED outcomes (clearly labeled; emits NO efficacy claim)
demo=df.dropna(subset=['search_no_new_evidence_rate']).head(50)
picks=[deterministic_selector(dict(search_no_new_evidence_rate=r['search_no_new_evidence_rate'],
        no_evidence_patch_churn_rate=r['no_evidence_patch_churn_rate'],
        post_edit_test_gap_undefined=pd.isna(r['post_edit_test_gap']))) for _,r in demo.iterrows()]
from collections import Counter
dryrun=dict(STATUS='PLUMBING_ONLY__NO_REAL_PAIRED_OUTCOMES',
            selector_picks_on_50_dev_traces=dict(Counter(picks)),
            note='Distribution of config picks proves the selector code path runs on frozen features. '
                 'NO token-saving / regression number is computed — that requires real paired runs.')
json.dump(dryrun, open(os.path.join(ROOT,'data','selector_dryrun.json'),'w'),indent=1)

L=["# Selector Ablation (development) — STATUS: PENDING paired outcomes\n",
   "The 10 methods (DEFAULT, GLOBAL_BEST, RANDOM, STATIC_METADATA, TRACE_LENGTH_ONLY,",
   "DETERMINISTIC_TRACE_SELECTOR, PROMPTED_LOCAL_8B, LORA_LOCAL_8B, RULES+LORA, ORACLE) and the",
   "primary question (does a trace-conditioned selector beat GLOBAL_BEST under the same regression",
   "ceiling?) CANNOT be answered without paired config outcomes — which require re-running SWE-agent",
   "x tasks x configs against a live solver. That is the dominant compute cost and was out of scope for",
   "this window. We therefore:",
   "- pre-registered the evaluation (analysis/selector_evaluation_plan_v1.md),",
   "- implemented the DETERMINISTIC selector over FROZEN prefix features (src/evaluate_trace_selectors.py),",
   "- DRY-RAN it on 50 dev traces to prove the code path (data/selector_dryrun.json),",
   "- emitted NO efficacy number (no fabricated token-saving / regression).",
   f"\nSelector pick distribution on the dry-run sample: {dict(Counter(picks))}",
   "\nTRACE_SELECTOR_VERDICT: PENDING (paired outcomes required).",
   "PARETO_POLICY_DATA_VERDICT: NOT_EMPIRICALLY_GROUNDED (no paired outcomes)."]
open(os.path.join(ROOT,'reports','selector_ablation_development.md'),'w').write("\n".join(L))
print("manifests + selector dry-run written. picks:", dict(Counter(picks)))
print("dev_intervention_tasks:",len(dev_tasks),"qwen_tasks:",len(qwen_tasks),"(disjoint)")
