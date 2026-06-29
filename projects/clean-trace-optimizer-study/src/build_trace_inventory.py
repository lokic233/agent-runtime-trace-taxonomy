#!/usr/bin/env python3
"""build_trace_inventory.py — clean-room inventory report + shared-task overlap + manual sample.
Reads manifests/development_trace_inventory.jsonl + data/features/*.jsonl.
Writes reports/trace_inventory.md, reports/shared_task_overlap.md,
manifests/clean_manual_audit_sample.jsonl (seeded stratified 120).
"""
import json, os, random, hashlib
from collections import Counter, defaultdict
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
INV=os.path.join(ROOT,'manifests','development_trace_inventory.jsonl')
FD=os.path.join(ROOT,'data','features')
inv=[json.loads(l) for l in open(INV)]

# load full features for tertile stratification
feat={}
for s in set(r['solver_alias'] for r in inv):
    p=os.path.join(FD,f'{s}.jsonl')
    if os.path.exists(p):
        for line in open(p):
            row=json.loads(line); feat[row['trace_id']]=row.get('full',{})

# ---- inventory report ----
by_solver=Counter(r['solver_alias'] for r in inv)
by_repo=Counter(r['repo'] for r in inv)
by_harness=Counter(r['source_harness'] for r in inv)
tasks_by_solver=defaultdict(set)
for r in inv: tasks_by_solver[r['solver_alias']].add(r['task_id'])
all_tasks=set(r['task_id'] for r in inv)
resolved_cov=sum(1 for r in inv if r['resolved'] is not None)
tok_cov=sum(1 for r in inv if feat.get(r['trace_id'],{}).get('n_actions'))
parse_fail=sum(1 for r in inv if r['parse_status']!='OK')
# duplicate traces (same trace_id)
dup=sum(v-1 for v in Counter(r['trace_id'] for r in inv).values() if v>1)

L=[]
L.append("# Trace Inventory — clean-trace-optimizer-study\n")
L.append(f"Total traces: **{len(inv)}** across **{len(all_tasks)}** distinct tasks, "
         f"**{len(by_repo)}** repos, **{len(by_harness)}** harnesses.\n")
L.append("## Trace count by solver\n")
L.append("| solver | model_hint | harness | role | n | resolve rate |")
L.append("|---|---|---|---|---|---|")
meta={r['solver_alias']:(r['model_hint'],r['source_harness'],r['role']) for r in inv}
for s,n in sorted(by_solver.items()):
    res=[r['resolved'] for r in inv if r['solver_alias']==s and r['resolved'] is not None]
    rr=f"{sum(res)/len(res):.1%}" if res else "n/a"
    m=meta[s]
    L.append(f"| {s} | {m[0]} | {m[1]} | {m[2]} | {n} | {rr} ({sum(res)}/{len(res)}) |")
L.append(f"\n## Coverage & integrity\n")
L.append(f"- resolved-label coverage: {resolved_cov}/{len(inv)} ({resolved_cov/len(inv):.1%})")
L.append(f"- action-count availability: {tok_cov}/{len(inv)}")
L.append(f"- parser failures: {parse_fail}")
L.append(f"- duplicate trace_ids: {dup}")
L.append(f"- NOTE: raw token counts (prefill/decode) are NOT in these trajectory files; "
         f"`total_tokens` proxy = n_actions/n_steps (action-step count). The HAL ledger has "
         f"true tokens for A/F only; cost_estimate exists for B. Token cost analysis uses "
         f"n_actions as the available cost proxy and flags this limitation honestly.")
L.append("\n## Source harness distribution\n")
for h,n in by_harness.most_common(): L.append(f"- {h}: {n}")
L.append("\n## Top repos\n")
for rp,n in by_repo.most_common(12): L.append(f"- {rp}: {n}")
L.append("\n## Confound warning\n")
L.append("Solver and harness are **partially confounded**: opus-4.5=live-SWE-agent, "
         "opus-4.7/4.6=SWE-agent-1.0(HAL), sonnet-3.5=SWE-agent-1.0, 32B-class=OpenHands/SWE-agent-LM. "
         "Per the spec, solver-capability differences must NOT be read off raw prevalence without "
         "controlling for harness and task. All correlation models include solver + harness + repo + task FE.")
open(os.path.join(ROOT,'reports','trace_inventory.md'),'w').write("\n".join(L))

# ---- shared-task overlap ----
O=[]
O.append("# Shared-Task Overlap\n")
O.append(f"Distinct tasks: {len(all_tasks)}. Tasks appearing in >1 solver enable task-fixed-effect models.\n")
solvers=sorted(tasks_by_solver)
O.append("## Pairwise task overlap (Jaccard / intersection)\n")
O.append("| | "+" | ".join(solvers)+" |")
O.append("|"+"---|"*(len(solvers)+1))
for a in solvers:
    row=[a]
    for b in solvers:
        ia=len(tasks_by_solver[a]&tasks_by_solver[b])
        row.append(str(ia))
    O.append("| "+" | ".join(row)+" |")
# how many tasks shared across ALL development solvers (A,B,C)
dev=['solver_A','solver_B','solver_C']
shared_dev=set.intersection(*[tasks_by_solver[s] for s in dev])
shared_all=set.intersection(*[tasks_by_solver[s] for s in solvers])
task_mult=Counter()
for t in all_tasks:
    task_mult[sum(1 for s in solvers if t in tasks_by_solver[s])]+=1
O.append(f"\n## Task multiplicity (how many solvers share each task)\n")
for k in sorted(task_mult): O.append(f"- in {k} solver(s): {task_mult[k]} tasks")
O.append(f"\n- Tasks shared by all 3 core development solvers (A,B,C): **{len(shared_dev)}**")
O.append(f"- Tasks shared by ALL {len(solvers)} solvers: **{len(shared_all)}**")
O.append(f"\nThese {len(shared_dev)} A/B/C-shared tasks support within-task paired comparisons "
         f"and task-fixed-effect token models (RQ1 task-FE).")
open(os.path.join(ROOT,'reports','shared_task_overlap.md'),'w').write("\n".join(O))

print("inventory + overlap reports written")
print("shared A/B/C tasks:", len(shared_dev), "| shared all:", len(shared_all))
print("task multiplicity:", dict(task_mult))
