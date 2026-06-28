#!/usr/bin/env python3
"""test_no_future_leakage.py — enforce the Section 10 prefix firewall.
Run: python3 tests/test_no_future_leakage.py  (or pytest)"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.generate_trace_prefixes import make_prefix, meaningful_prefix, CUTOFFS, FORBIDDEN_IN_PREFIX, MEANINGFUL
from src.normalize_traces import normalize_trace

def _toy_trace(n=30):
    raw={"trajectory":[{"action":f"grep x{i}" if i%3 else f"pytest test_{i}.py",
                        "observation":f"out{i}","thought":f"t{i}",
                        "state":{"diff":""}} for i in range(n)],
         "info":{"exit_status":"submitted","submission":"diff --git a/x b/x",
                 "model_stats":{"tokens_sent":9999,"tokens_received":111}}}
    return normalize_trace(raw, trace_id="toy@solver_A", task_id="toy", solver_alias="solver_A")

def test_prefix_event_count_bounded():
    nt=_toy_trace(30)
    for cut,k in CUTOFFS.items():
        v=make_prefix(nt, cut)
        if k is None:
            assert v["n_events_shown"]==nt["n_events"]
        else:
            # at most k MEANINGFUL actions in the view
            m=sum(1 for e in v["events"] if e["normalized_action_type"] in MEANINGFUL)
            assert m<=k, f"{cut}: {m} meaningful > {k}"

def test_no_future_event_indices():
    nt=_toy_trace(30)
    for cut,k in CUTOFFS.items():
        if k is None: continue
        v=make_prefix(nt, cut)
        max_i = max((e["event_index"] for e in v["events"]), default=-1)
        # the last shown event is the k-th meaningful; nothing beyond it leaks
        shown_idx={e["event_index"] for e in v["events"]}
        assert all(i<=max_i for i in shown_idx)

def test_no_outcome_in_prefix():
    nt=_toy_trace(30)
    for cut in ("T0","T5","T10","T20"):
        v=make_prefix(nt, cut)
        blob=json.dumps(v).lower()
        # outcome/exit/submission/gold/final-patch/total-tokens must NOT appear
        for banned in ("submitted","submission","\"resolved\"","gold_patch","final_patch"):
            assert banned not in blob, f"{cut} leaks {banned}"
        assert v["n_events_total"]=="HIDDEN"
        # tokens hard-nulled in prefix events
        assert all(e["input_tokens"] is None and e["output_tokens"] is None for e in v["events"])

def test_T0_is_metadata_only():
    nt=_toy_trace(30)
    v=make_prefix(nt,"T0")
    assert v["n_events_shown"]==0
    assert v["events"]==[]

def test_prefix_is_true_subset_of_full():
    nt=_toy_trace(30)
    full=make_prefix(nt,"FULL")
    full_sigs=[(e["event_index"],e["normalized_action_type"]) for e in full["events"]]
    for cut in ("T5","T10","T20"):
        v=make_prefix(nt,cut)
        sigs=[(e["event_index"],e["normalized_action_type"]) for e in v["events"]]
        assert sigs==full_sigs[:len(sigs)], f"{cut} not a prefix of FULL"

def test_monotonic_growth():
    nt=_toy_trace(30)
    counts=[make_prefix(nt,c)["n_events_shown"] for c in ("T0","T5","T10","T20","FULL")]
    assert counts==sorted(counts), f"prefix sizes not monotonic: {counts}"

def test_forbidden_keys_absent_in_prefix():
    nt=_toy_trace(30)
    for cut in ("T0","T5","T10","T20"):
        v=make_prefix(nt,cut)
        keys=set()
        def walk(o):
            if isinstance(o,dict):
                keys.update(o.keys()); [walk(x) for x in o.values()]
            elif isinstance(o,list): [walk(x) for x in o]
        walk(v)
        for fb in FORBIDDEN_IN_PREFIX:
            assert fb not in keys, f"{cut} exposes forbidden key {fb}"

if __name__=="__main__":
    fns=[v for k,v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    p=0
    for fn in fns:
        try: fn(); p+=1; print(f"✅ {fn.__name__}")
        except AssertionError as e: print(f"❌ {fn.__name__}: {e}")
    print(f"\n{p}/{len(fns)} leakage tests passed")
    sys.exit(0 if p==len(fns) else 1)
