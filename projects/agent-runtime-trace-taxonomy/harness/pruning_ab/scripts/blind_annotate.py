import json, os, subprocess, sys
BASE="/data/users/dengcchi/prune_ab"
events=[json.loads(l) for l in open(f"{BASE}/results/pruning_ab/blind_decision_views.jsonl")]
ACTIONS="NO_OP, LINE_DEDUP, GENTLE_CAP, RETRIEVABLE_REFERENCE, EXTERNALIZE, KEEP_FULL_CONTENT"
ROLES={
"A_systems":"You are a SYSTEMS/RUNTIME analyst. Focus ONLY on: caching, repeated computation, tool I/O, storage/compute waste, prefix stability, recoverability, runtime phase.",
"B_reasoning":"You are an AGENT-REASONING analyst. Focus ONLY on: semantic dependency, active hypotheses, evidence liveness, information supersession, reasoning progress, likely future use.",
"C_hostile":"You are a HOSTILE CAUSAL REVIEWER. DOUBT everything: is the signal observable BEFORE acting? what confounds it? hindsight bias? alternative explanation? is it ACTION-SPECIFIC or just 'expensive task'? List counterexamples.",
}
SCHEMA='Output ONLY valid JSON (no prose), schema: {"event_id":"","evidence_trace_spans":["quote concrete lines"],"pattern_name":"snake_case","pattern_description":"","signal_scope":"segment|call|phase|task","latent_state":{"semantic_role":"new_evidence|repeated_evidence|source_code|stack_trace|test_output|dir_listing|env_state|instruction|progress|stale_state|superseding_state|boilerplate","semantic_liveness":"active|latent|superseded|dead|redundant|unknown","redundancy_type":"exact_duplicate|near_duplicate|semantic_duplicate|stale_duplicate|latest_state_duplicate|repeated_but_active|none","recoverability":"exact_copy_elsewhere|deterministic_refetch|nondeterministic_refetch|expensive_refetch|mutable_external|nonrecoverable","dependency_risk":"directly_referenced|supports_unresolved_hypothesis|likely_needed_for_verification|no_known_future_dependency|unknown","task_phase":"exploration|localization|editing|verification|recovery|looping|near_completion"},"candidate_actions":[],"preferred_action":"NO_OP|LINE_DEDUP|GENTLE_CAP|RETRIEVABLE_REFERENCE|EXTERNALIZE|KEEP_FULL_CONTENT","benefit_mechanism":"","risk_mechanism":"","required_preconditions":[],"counterexamples":[],"observable_before_action":true,"predicted_local_effect":{"cost":"decrease|neutral|increase","cache":"improve|neutral|worsen","trajectory_drift":"low|medium|high","quality_risk":"low|medium|high"},"confidence":0.0}'

def annotate(ev, rk):
    view={k:ev[k] for k in ["event_id","task_id","repo","decision_call_obs_index","task_statement_excerpt","n_prior_observations","candidate_segment_chars","candidate_segment_lines","candidate_dup_lines_vs_prior","candidate_segment_text","candidate_segment_tail"]}
    prompt=(ROLES[rk]+"\n\nAnnotate a DECISION POINT in a SWE-agent trajectory. A large tool-observation (candidate segment) just arrived. A controller must decide: keep it or apply an action: "+ACTIONS+".\nYou see ONLY the prefix. NO future, NO outcome, NO action taken, NO cost/quality result. Identify the candidate segment's latent pattern + safest action. MUST cite concrete evidence_trace_spans (quote actual lines). MUST list counterexamples.\n\nDECISION VIEW:\n"+json.dumps(view)[:9000]+"\n\n"+SCHEMA)
    try:
        p=subprocess.run(["claude","-p",prompt],capture_output=True,text=True,timeout=120)
        out=p.stdout.strip(); s=out.find("{"); e=out.rfind("}")
        if s>=0 and e>s:
            obj=json.loads(out[s:e+1]); obj["_role"]=rk; obj["_event_id"]=ev["event_id"]; return obj
    except Exception as ex:
        return {"_role":rk,"_event_id":ev["event_id"],"_error":str(ex)[:150]}
    return {"_role":rk,"_event_id":ev["event_id"],"_error":"no_json","_raw":out[:200] if 'out' in dir() else ""}

n=int(sys.argv[1]) if len(sys.argv)>1 else len(events)
roles=sys.argv[2].split(",") if len(sys.argv)>2 else list(ROLES)
fn=f"{BASE}/results/pruning_ab/blind_frontier_annotations.jsonl"
done=set()
if os.path.exists(fn):
    for l in open(fn):
        try: d=json.loads(l); done.add((d.get("_event_id"),d.get("_role")))
        except: pass
out=open(fn,"a"); cnt=0
for ev in events[:n]:
    for rk in roles:
        if (ev["event_id"],rk) in done: continue
        obj=annotate(ev,rk); out.write(json.dumps(obj)+"\n"); out.flush(); cnt+=1
        print(f"  {ev['event_id']} {rk}: {('ERR '+obj['_error']) if '_error' in obj else obj.get('preferred_action','?')}")
print(f"annotated {cnt} pairs")
