import json, os, subprocess, sys
BASE="/data/users/dengcchi/prune_ab"
events=[json.loads(l) for l in open(f"{BASE}/results/pruning_ab/mrt_blind_views.jsonl")]
ACTIONS="NO_OP, KEEP_FULL_CONTENT, LINE_DEDUP, GENTLE_CAP, RETRIEVABLE_REFERENCE"
ROLES={
"A_systems":"You are a SYSTEMS/RUNTIME analyst. Focus ONLY on: caching, repeated computation, tool I/O, storage/compute waste, prefix stability, recoverability, runtime phase. Determine if this segment is redundant, recoverable, or essential for cache continuity.",
"B_reasoning":"You are an AGENT-REASONING analyst. Focus ONLY on: semantic dependency, active hypotheses, evidence liveness, information supersession, reasoning progress, likely future use. Determine if the agent still needs this content or has moved past it.",
"C_hostile":"You are a HOSTILE CAUSAL REVIEWER. DOUBT everything: is the signal observable BEFORE acting? what confounds it? hindsight bias? is it ACTION-SPECIFIC? Could the segment be both redundant AND needed? List counterexamples where this pattern fails.",
}
SCHEMA='Output ONLY valid JSON: {"event_id":"","annotator_id":"","evidence_span_ids":["quote concrete lines"],"semantic_role":"source_code|test_output|stack_trace|dir_listing|env_state|instruction|progress|stale_state|superseding_state|boilerplate|unknown","semantic_liveness":"active|latent|superseded|dead|redundant|unknown","redundancy_type":"exact|near|semantic|stale|latest_state|repeated_but_active|none","recoverability":"exact_copy|deterministic_refetch|expensive_refetch|nondeterministic|mutable|nonrecoverable|unknown","dependency_risk":"low|medium|high|unknown","task_phase":"exploration|localization|editing|verification|recovery|looping|near_completion|unknown","preferred_action":"NO_OP|KEEP_FULL_CONTENT|LINE_DEDUP|GENTLE_CAP|RETRIEVABLE_REFERENCE","benefit_mechanism":"","risk_mechanism":"","required_preconditions":[],"counterexamples":[],"confidence":0.0}'

def annotate(ev, rk):
    prompt=(ROLES[rk]+"\n\nAnnotate a DECISION POINT. A tool observation (candidate segment) arrived. A controller decides: keep or apply "+ACTIONS+". You see ONLY the prefix. NO future, NO outcome, NO cost. Identify the latent pattern + safest action. MUST cite concrete lines. MUST list counterexamples.\n\nEVENT (strata="+str(ev.get("strata",""))+", size="+str(ev.get("segment_size_chars",""))+"c, dup_lines="+str(ev.get("eligibility_metadata",{}).get("dup_lines",""))+")\nSEGMENT TEXT (truncated):\n"+ev.get("candidate_segment_text","")[:5000]+"\n"+("...TAIL:\n"+ev.get("candidate_segment_tail","") if ev.get("candidate_segment_tail") else "")+"\n\n"+SCHEMA)
    try:
        p=subprocess.run(["claude","-p",prompt],capture_output=True,text=True,timeout=120)
        out=p.stdout.strip(); s=out.find("{"); e=out.rfind("}")
        if s>=0 and e>s:
            obj=json.loads(out[s:e+1]); obj["annotator_id"]=rk; obj["event_id"]=ev["event_id"]; return obj
    except Exception as ex:
        return {"annotator_id":rk,"event_id":ev["event_id"],"_error":str(ex)[:150]}
    return {"annotator_id":rk,"event_id":ev["event_id"],"_error":"no_json"}

n=int(sys.argv[1]) if len(sys.argv)>1 else len(events)
roles=sys.argv[2].split(",") if len(sys.argv)>2 else list(ROLES)
fn=f"{BASE}/results/pruning_ab/mrt_blind_annotations.jsonl"
done=set()
if os.path.exists(fn):
    for l in open(fn):
        try: d=json.loads(l); done.add((d.get("event_id"),d.get("annotator_id")))
        except: pass
out=open(fn,"a"); cnt=0
for ev in events[:n]:
    for rk in roles:
        if (ev["event_id"],rk) in done: continue
        obj=annotate(ev,rk); out.write(json.dumps(obj)+"\n"); out.flush(); cnt+=1
        act=obj.get("preferred_action","ERR") if "_error" not in obj else "ERR:"+obj["_error"][:30]
        print(f"  {ev['event_id'][:30]} {rk}: {act}")
print(f"annotated {cnt} pairs")
