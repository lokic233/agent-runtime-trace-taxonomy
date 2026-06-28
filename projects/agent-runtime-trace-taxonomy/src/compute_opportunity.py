#!/usr/bin/env python3
"""compute_opportunity.py — improvement-opportunity analysis (HEURISTIC, not empirical).

For each waste pattern: prevalence + capability-gap (weak-strong) + observability -> opportunity
tier, overall AND per-model. Uses DETERMINISTIC PROXY detectors over the normalized index
(NOT the semantic labels — full annotation sharpens these). Tier = 'worth trying', NOT proven
efficacy: proving an intervention helps needs paired config outcomes (NOT_EMPIRICALLY_GROUNDED).
"""
from __future__ import annotations
import json, collections, yaml, os, sys

PROXY = {
 "REDUNDANT_FILE_REREAD": lambda F:(F.get('duplicate_file_reads') or 0)>=2,
 "CONTEXT_BLOAT":         lambda F:(F.get('duplicate_file_reads') or 0)>=2,
 "FILENAME_SEARCH_THRASH":lambda F:(F.get('unique_files_searched') or 0)>=10,
 "SEARCH_WITHOUT_NEW_EVIDENCE":lambda F:(F.get('exact_duplicate_call_rate') or 0)>0.10,
 "PATCH_CHURN":           lambda F:(F.get('patch_attempts') or 0)>=5,
 "PREMATURE_SCRATCH_REPRO":lambda F:(F.get('first_edit_step') or 99)<=1 and (F.get('search_call_count') or 0)==0,
 "EDIT_TOOL_MECHANICAL_FAILURE":lambda F:(F.get('longest_tool_error_run') or 0)>=2,
 "VERIFICATION_GAP":      lambda F:(F.get('targeted_test_count') or 0)==0,
 "REDUNDANT_TEST":        lambda F:(F.get('unchanged_repeated_tests') or 0)>=1,
 "STAGNATION":            lambda F:(F.get('longest_no_new_evidence_streak') or 0)>=3,
 "FAILED_RECOVERY":       lambda F:(F.get('patch_attempts') or 0)>=3 and (F.get('targeted_test_count') or 0)>=2,
 "BUDGET_EXHAUSTION_NONCONVERGENCE":lambda F:str(F.get('termination_reason') or '').lower() in ('exit_cost','max_steps','timeout','limitsexceeded'),
 "PREEMPTIVE_HELPER_TOOL_BUILD":lambda F:(F.get('environment_setup_events') or 0)>=3,
 "HELPER_TOOL_FAILURE_LOOP":lambda F:(F.get('longest_tool_error_run') or 0)>=3,
 "DEPENDENCY_SETUP_DRIFT":lambda F:(F.get('environment_setup_events') or 0)>=2,
 "ENVIRONMENT_BLOCKED":   lambda F:(F.get('longest_tool_error_run') or 0)>=3,
}
# patterns where weak<=strong prevalence => intervening would hurt strong solvers (harness/capability artifact)
HARNESSY={'PREEMPTIVE_HELPER_TOOL_BUILD','DEPENDENCY_SETUP_DRIFT','FILENAME_SEARCH_THRASH'}

def load(index_path):
    rows=[json.loads(l) for l in open(index_path)]
    by=collections.defaultdict(list)
    for r in rows: by[r['solver_alias']].append(r)
    return by

def prev(by, alias, k):
    R=by.get(alias,[])
    return 100*sum(1 for r in R if PROXY[k](r['features'])) / len(R) if R else 0.0

def model_tier(p, k):
    if k in HARNESSY: return "SKIP_HARNESS"
    if p>=40: return "HIGH"
    if p>=15: return "MED"
    if p>=5:  return "LOW"
    return "NONE"

def overall(by, strong=('solver_B',), weak=('solver_C',)):
    out={}
    allk=list(by)
    for k in PROXY:
        pa=100*sum(1 for a in allk for r in by[a] if PROXY[k](r['features']))/sum(len(by[a]) for a in allk)
        ps=sum(prev(by,a,k) for a in strong)/len(strong)
        pw=sum(prev(by,a,k) for a in weak)/len(weak)
        gap=pw-ps
        s=0
        if pa>=40: s+=2
        elif pa>=15: s+=1
        if gap>=20: s+=2
        elif gap>=5: s+=1
        elif gap<=-20: s-=1
        if k in HARNESSY: s-=2
        tier="HIGH" if s>=4 else ("MEDIUM" if s>=2 else "LOW")
        out[k]=dict(all=round(pa,1),strong=round(ps,1),weak=round(pw,1),gap=round(gap,1),score=s,tier=tier)
    return out

if __name__=="__main__":
    idx=sys.argv[1] if len(sys.argv)>1 else "/tmp/index_all.jsonl"
    by=load(idx)
    ov=overall(by)
    res={"_method":"HEURISTIC deterministic-proxy; tier=worth-trying NOT proven efficacy; full annotation sharpens; config efficacy NOT_EMPIRICALLY_GROUNDED",
         "overall":ov,
         "per_model":{a:{k:{"prevalence":round(prev(by,a,k),1),"tier":model_tier(prev(by,a,k),k)} for k in PROXY} for a in by}}
    json.dump(res, open("reports/opportunity_analysis.json","w"), indent=2)
    print("wrote reports/opportunity_analysis.json")
    print("models:", {a:len(by[a]) for a in by})
