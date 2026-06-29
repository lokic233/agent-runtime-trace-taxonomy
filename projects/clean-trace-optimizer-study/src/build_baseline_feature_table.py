#!/usr/bin/env python3
"""build_baseline_feature_table.py — assemble the task x solver baseline table (parquet + csv).
Preserves raw count, normalized rate, and missingness SEPARATELY. Does not fill missing with 0.
"""
import json, os
import pandas as pd, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
INV=os.path.join(ROOT,'manifests','development_trace_inventory.jsonl')
FD=os.path.join(ROOT,'data','features')
inv={json.loads(l)['trace_id']:json.loads(l) for l in open(INV)}

PRIMARY=['search_no_new_evidence_rate','redundant_reread_rate','oversized_then_narrow_read_rate',
         'no_evidence_patch_churn_rate','post_edit_test_gap','fraction_actions_in_no_new_evidence_streaks',
         'tool_error_rate','environment_setup_rate']
RAWCOUNTS=['search_call_count','read_call_count','edit_count','test_count','n_actions','n_steps',
           'exact_repeated_search_count','same_file_reedit_count','no_evidence_reedit_count',
           'tool_error_count','environment_setup_event_count','longest_no_new_evidence_streak',
           'unique_files_read','unique_files_modified','candidate_files_discovered']

rows=[]
for s in sorted(set(r['solver_alias'] for r in inv.values())):
    p=os.path.join(FD,f'{s}.jsonl')
    for line in open(p):
        d=json.loads(line); tid=d['trace_id']; full=d.get('full',{})
        meta=inv.get(tid,{})
        row=dict(trace_id=tid, task_id=d['task_id'], repo=meta.get('repo'),
                 solver_alias=s, source_harness=meta.get('source_harness'),
                 model_hint=meta.get('model_hint'), role=meta.get('role'),
                 resolved=meta.get('resolved'),
                 n_events=full.get('n_steps'), n_actions=full.get('n_actions'))
        # termination reason from last action class / patterns
        # primary rates (None preserved)
        for f in PRIMARY: row[f]=full.get(f)
        # raw counts
        for f in RAWCOUNTS: row['cnt_'+f]=full.get(f)
        # explicit missingness flags
        for f in PRIMARY: row['miss_'+f]= (full.get(f) is None)
        rows.append(row)
df=pd.DataFrame(rows)
# total_tokens proxy = n_actions (documented limitation: true tokens unavailable/unattributable)
df['total_tokens_proxy']=df['n_actions']
os.makedirs(os.path.join(ROOT,'data'),exist_ok=True)
df.to_parquet(os.path.join(ROOT,'data','baseline_trace_feature_table.parquet'))
df.to_csv(os.path.join(ROOT,'data','baseline_trace_feature_table.csv'),index=False)
print("rows:",len(df),"cols:",len(df.columns))
print("\nmissingness per primary feature:")
for f in PRIMARY:
    print(f"  {f}: {df['miss_'+f].sum()}/{len(df)} missing ({df['miss_'+f].mean():.1%})")
print("\nresolved coverage:", df['resolved'].notna().sum(),"/",len(df))
