#!/usr/bin/env python3
"""build_clean_audit_sample.py — seeded stratified manual-audit sample (target 120).
Strata: solver x resolved/unresolved x token(=n_action) tertile x behavior-axis flags.
Excludes held-out Qwen (none present). Reproducible via fixed seed.
"""
import json, os, random
from collections import defaultdict
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
INV=os.path.join(ROOT,'manifests','development_trace_inventory.jsonl')
FD=os.path.join(ROOT,'data','features')
SEED=20260628
random.seed(SEED)

inv=[json.loads(l) for l in open(INV)]
feat={}
for s in set(r['solver_alias'] for r in inv):
    for line in open(os.path.join(FD,f'{s}.jsonl')):
        row=json.loads(line); feat[row['trace_id']]=row.get('full',{})

# n_action tertiles GLOBAL
nacts=sorted(f.get('n_actions') or 0 for f in feat.values())
def tert(v):
    if v is None: return 'na'
    lo=nacts[len(nacts)//3]; hi=nacts[2*len(nacts)//3]
    return 'low' if v<=lo else ('mid' if v<=hi else 'high')

# behavior axis flags (continuous->bool via simple presence; used only for STRATIFICATION coverage)
def axes(tid):
    f=feat.get(tid,{})
    a=[]
    if (f.get('search_call_count') or 0)>=5: a.append('search_heavy')
    if (f.get('edit_count') or 0)>=5: a.append('edit_heavy')
    if (f.get('test_count') or 0)>=2: a.append('test_heavy')
    if (f.get('tool_error_rate') or 0)>=0.15: a.append('high_error')
    elif (f.get('tool_error_rate') or 0)==0: a.append('low_error')
    n=f.get('n_actions') or 0
    if n<=8: a.append('short_traj')
    elif n>=40: a.append('long_traj')
    return a or ['generic']

# build strata cells: (solver, resolved_bucket, tertile)
cells=defaultdict(list)
for r in inv:
    tid=r['trace_id']
    rb = 'res' if r['resolved'] else ('unres' if r['resolved'] is False else 'ungraded')
    cells[(r['solver_alias'], rb, tert(feat.get(tid,{}).get('n_actions')))].append(r)

# allocate ~ proportional but ensure each solver & axis represented; aim 120
TARGET=120
sample=[]; seen=set()
# pass 1: at least 1 per non-empty cell (caps breadth)
cell_keys=sorted(cells)
random.shuffle(cell_keys)
for k in cell_keys:
    pool=cells[k]
    if pool:
        pick=random.choice(pool)
        if pick['trace_id'] not in seen:
            sample.append(pick); seen.add(pick['trace_id'])
# pass 2: ensure each behavior axis has >=6 traces
axis_need={ax:6 for ax in ['search_heavy','edit_heavy','test_heavy','high_error','low_error','short_traj','long_traj']}
for r in inv:
    for ax in axes(r['trace_id']):
        if ax in axis_need and axis_need[ax]>0 and r['trace_id'] not in seen:
            sample.append(r); seen.add(r['trace_id']); axis_need[ax]-=1
# pass 3: fill to TARGET proportionally across solvers
while len(sample)<TARGET:
    r=random.choice(inv)
    if r['trace_id'] not in seen:
        sample.append(r); seen.add(r['trace_id'])
sample=sample[:TARGET]

# annotate sample rows with strata + axes for the auditor
out=[]
for r in sample:
    tid=r['trace_id']; f=feat.get(tid,{})
    out.append({**{k:r[k] for k in ('trace_id','task_id','repo','solver_alias','source_harness','resolved','source_path')},
                'n_actions':f.get('n_actions'),'tertile':tert(f.get('n_actions')),'axes':axes(tid)})
with open(os.path.join(ROOT,'manifests','clean_manual_audit_sample.jsonl'),'w') as fh:
    for r in out: fh.write(json.dumps(r)+'\n')

from collections import Counter
print("sample size:", len(out), "seed:", SEED)
print("by solver:", dict(Counter(r['solver_alias'] for r in out)))
print("by resolved:", dict(Counter(('res' if r['resolved'] else 'unres' if r['resolved'] is False else 'ungraded') for r in out)))
print("by tertile:", dict(Counter(r['tertile'] for r in out)))
axc=Counter()
for r in out:
    for a in r['axes']: axc[a]+=1
print("axis coverage:", dict(axc))
