#!/usr/bin/env python3
"""H=3 joiner for the confirmatory study — MAIN-AGENT-CALL aware (FIX 3).
The H=3 proximal outcome = the intervention response + the next two MAIN-AGENT responses of the
same task, ordered by persistent event_ordinal. Internal/setup calls are NEVER counted toward the
horizon. All provider calls remain in provider_events.jsonl for total-cost accounting.
Never mutates raw logs. Usage: join_h3_confirmatory.py <events.jsonl> <out.json>
"""
import json, sys, collections

def load(path): return [json.loads(l) for l in open(path) if l.strip()]

def join_h3(events):
    by=collections.defaultdict(list)
    for e in events:
        if e.get("task_id"): by[e["task_id"]].append(e)
    rows=[]
    for tid,evs in by.items():
        # only MAIN-AGENT calls participate in the proximal horizon
        mac=[e for e in evs if e.get("call_class")=="main_agent_call"]
        mac.sort(key=lambda e: e.get("event_ordinal", e.get("call_index",0)))
        exp=[e for e in mac if e.get("experimental_event")]
        if not exp: continue
        iv=exp[0]
        piv=mac.index(iv)
        horizon=mac[piv:piv+3]   # intervention + next 2 MAIN-AGENT responses
        costs=[e.get("effective_cost_h1") for e in horizon if e.get("effective_cost_h1") is not None]
        infra=any(e.get("infrastructure_failure") for e in horizon)
        rows.append(dict(
            task_id=tid, repo=iv.get("repo",""),
            A=1 if iv.get("assignment")=="LINEDEDUP" else 0, assignment=iv.get("assignment"),
            stratum=iv.get("moderator_stratum"), dup_frac=iv.get("duplicate_line_fraction",0.0),
            dup_count=iv.get("duplicate_line_count",0), seg_chars=iv.get("segment_chars",0),
            calls_so_far=iv.get("event_ordinal",iv.get("call_index",0)),
            block_id=iv.get("block_id"), block_position=iv.get("block_position"),
            chars_removed=iv.get("characters_removed",0), actual_changed=iv.get("actual_changed",False),
            h1=iv.get("effective_cost_h1"), h3=sum(costs) if costs else None,
            h3_horizon=len(costs), truncated=len(costs)<3,
            input_tokens=iv.get("input_tokens"), cache_read=iv.get("cache_read_tokens"),
            cache_creation=iv.get("cache_creation_tokens"), output_tokens=iv.get("output_tokens"),
            infra_fail=infra))
    return rows

if __name__=="__main__":
    ev=load(sys.argv[1]); rows=join_h3(ev)
    json.dump(rows, open(sys.argv[2],"w"), indent=1)
    print(f"joined {len(rows)} interventions; truncated<3: {sum(1 for r in rows if r['truncated'])}")
