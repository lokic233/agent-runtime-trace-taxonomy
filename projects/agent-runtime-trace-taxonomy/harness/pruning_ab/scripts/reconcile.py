#!/usr/bin/env python3
"""Reconcile contradictions across prior reports vs raw data."""
import json, os, re
BASE="/data/users/dengcchi/prune_ab"
REPO="/home/dengcchi/agent_runtime_trace_taxonomy/projects/agent-runtime-trace-taxonomy"
G=set(json.load(open("/tmp/golden50.json")))

def resolved(p):
    return set(json.load(open(p)).get("resolved_ids",[]))&G if os.path.exists(p) else None

# RAW TRUTH from grades
c0_stable=resolved(f"{BASE}/results/pruning_ab/stable/grade_C0_identity.json")
c0_orig=resolved(f"{BASE}/results/pruning_ab/grade_C0_identity.json")
ld=resolved(f"{BASE}/results/pruning_ab/e4/grade_LINEDEDUP_e4.json")

contradictions=[]
# 1. C0 baseline count: reports cite both 48 and 46
contradictions.append({
 "issue":"C0 baseline resolved count",
 "values_in_reports":{"PARETO_v2/original":48,"stable-tagged/E3/E4 reports":46},
 "raw_truth":{"original_grade":len(c0_orig) if c0_orig else None,"stable_tagged_grade":len(c0_stable)},
 "resolution":"TWO DIFFERENT C0 RUNS. Original full_C0 run=48/50 (used by v2). Stable tagged C0 run=46/50 (used by E3/E4 pairing, canonical for cost). Both real; different runs => run-to-run variance of ~2 tasks. Canonical for causal pairing = stable tagged C0 (46/50)."
})
# 2. LINEDEDUP regression count: reports cite 5 and 2
ld_reg_vs_stable = sorted(c0_stable - ld) if (c0_stable and ld) else None
contradictions.append({
 "issue":"LINEDEDUP regression count",
 "values_in_reports":{"EXPERIMENT4 (46-task snapshot)":5,"corrected full-49":2},
 "raw_truth":{"vs_stable_C0_full":len(ld_reg_vs_stable) if ld_reg_vs_stable else None,"regressed_ids":ld_reg_vs_stable},
 "resolution":"The 5-count was at 46/50 completed (3 of the 5 were incomplete tasks, not true regressions). Full-49 reconstruction vs stable C0 = 2 regressions. The corrected count (2) is authoritative. NOTE: per the causal rules, these 2 are NOT to be dismissed as 'noise' — they are flips whose causal attribution is unresolved from single paired runs."
})
# 3. LINEDEDUP saving: +24% (partial) vs +6.3% (full)
contradictions.append({
 "issue":"LINEDEDUP effective-cost saving",
 "values_in_reports":{"partial-sampling (n=22)":24.3,"full-50":6.3},
 "raw_truth":"full-50 = +6.3% (the +24% was optimistic early-completion sampling: big-saver tasks finished first)",
 "resolution":"+6.3% (full) is authoritative. +24% was sampling bias; superseded."
})
# 4. The forbidden 'A/A noise => real regression 0' framing
contradictions.append({
 "issue":"'real regression = 0' framing (LINEDEDUP/GENTLE)",
 "problem":"Earlier reports computed 'real regressions' by excluding tasks that flip under C0 A/A. The causal-mission rules FORBID this: a task flipping under C0 does NOT prove a treatment has zero added effect.",
 "resolution":"RETRACTED. Single paired-run flips have UNRESOLVED causal attribution. Where A/A repeated runs exist (the 10 interesting tasks), estimate P(success|treat)-P(success|C0) directly instead. Raw regression counts stand; 'real reg = 0' claims are withdrawn."
})
json.dump(contradictions, open(f"{BASE}/results/pruning_ab/report_reconciliation.json","w"), indent=1, default=str)
for c in contradictions:
    print(f"\n### {c['issue']}")
    print(f"  reports said: {c.get('values_in_reports', c.get('problem'))}")
    print(f"  RESOLUTION: {c['resolution'][:200]}")
