#!/usr/bin/env python3
"""generate_trace_prefixes.py — Section 10 prefix/full-trace firewall.

Produce cutoff VIEWS of a normalized trace for online-control annotation:
  T0   = task metadata only (no events)
  T5   = first 5 normalized MEANINGFUL actions
  T10  = first 10
  T20  = first 20
  FULL = entire trace
A prefix view MUST NOT leak any future signal:
  - no events at index >= k
  - no final success/outcome (resolved)
  - no final patch / submission text
  - no total/final token use
  - no later test results
Meaningful actions exclude pure PLAN/OTHER filler so 'first 5 actions' means 5 real steps.

The generated prefix is what an annotator sees; test_no_future_leakage.py enforces the firewall.
"""
from __future__ import annotations
import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))

CUTOFFS = {"T0":0,"T5":5,"T10":10,"T20":20,"FULL":None}
MEANINGFUL = {"SEARCH","READ","RETRIEVE","EDIT","PATCH_APPLY","TEST","EXECUTE","TOOL_ERROR","ENVIRONMENT"}

def meaningful_prefix(events, k):
    """Return events up to (and including) the k-th MEANINGFUL action, plus any
    leading filler before it. k=0 -> empty (T0 = metadata only)."""
    if k is None:
        return list(events)
    if k <= 0:
        return []
    out=[]; count=0
    for e in events:
        if e["normalized_action_type"] in MEANINGFUL:
            count+=1
            out.append(e)
            if count>=k:
                break
        else:
            # leading/intervening filler (PLAN/OTHER) rides along only if we haven't hit k
            out.append(e)
    return out

def make_prefix(norm_trace: dict, cutoff: str) -> dict:
    """Build a leakage-safe view. STRIPS outcome and any post-cutoff signal."""
    if cutoff not in CUTOFFS:
        raise ValueError(f"bad cutoff {cutoff}")
    k = CUTOFFS[cutoff]
    events = meaningful_prefix(norm_trace["events"], k)
    # firewall: strip per-event fields that could encode the future in a prefix.
    # (token fields are null in our data anyway; we hard-null them for safety in prefixes.)
    safe_events=[]
    for e in events:
        e2=dict(e)
        if cutoff != "FULL":
            e2["input_tokens"]=e2["output_tokens"]=e2["context_tokens"]=None
        safe_events.append(e2)
    view = {
        "trace_id": norm_trace["trace_id"], "task_id": norm_trace["task_id"],
        "repo": norm_trace["repo"], "solver_alias": norm_trace["solver_alias"],
        "capability_tier": norm_trace.get("capability_tier"),
        "source_harness": norm_trace["source_harness"], "cutoff": cutoff,
        "n_events_shown": len(safe_events),
        "events": safe_events,
    }
    if cutoff == "FULL":
        # FULL views MAY carry outcome (post-hoc analysis), but for ONLINE-CONTROL annotation we
        # still hand outcome via a SEPARATE controlled channel, not in the view. Default: omit.
        view["n_events_total"] = norm_trace["n_events"]
    else:
        # PREFIX: explicitly NO outcome, NO totals, NO later signal.
        view["n_events_total"] = "HIDDEN"
        view["_firewall"] = "prefix: outcome/final-patch/total-tokens/later-tests withheld"
    return view

# fields that MUST NEVER appear in a prefix view (enforced by the leakage test)
FORBIDDEN_IN_PREFIX = ("resolved","exit_status","submission","gold_patch","final_patch",
                       "total_tokens","n_events_total_int")

if __name__=="__main__":
    import argparse
    sys.path.insert(0, os.path.dirname(__file__))
    from render_trace import _locator_map
    from normalize_traces import normalize_trace, load_raw
    ap=argparse.ArgumentParser()
    ap.add_argument("trace_id"); ap.add_argument("--alias",required=True)
    ap.add_argument("--cutoff",default="T5")
    a=ap.parse_args()
    loc=_locator_map()[a.trace_id]
    raw=load_raw(loc["source_path"])
    nt=normalize_trace(raw, trace_id=a.trace_id, task_id=a.trace_id.split("@")[0], solver_alias=a.alias)
    v=make_prefix(nt, a.cutoff)
    print(json.dumps({k:val for k,val in v.items() if k!="events"}, indent=2))
    print(f"... {v['n_events_shown']} events shown (cutoff {a.cutoff})")
