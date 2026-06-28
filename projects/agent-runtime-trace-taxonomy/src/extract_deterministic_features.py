#!/usr/bin/env python3
"""extract_deterministic_features.py — L0.5 deterministic feature layer.

Compute reproducible, no-model metrics from a normalized trace's event stream.
These are EVIDENCE, not semantic truth. Per the prompt + TokenSaver contract:
  - low result utilization is NOT automatically UNUSED_TOOL_RESULT
  - multiple searches are NOT automatically REDUNDANT_SEARCH
  - multiple tests are NOT automatically REDUNDANT_TEST
Every value is either a real number or null (never a fabricated 0 for absent data).

Groups: RESOURCE/ROOFLINE, TOOLS, MEMORY/CONTEXT, SWE-AGENT-SPECIFIC.
Token/CPU/RSS fields are null here (the .traj files carry only aggregate model_stats,
not per-event tokens) and are backfilled from info.model_stats at the trace level.
"""
from __future__ import annotations
from typing import Any, Optional
import collections

SEARCH_TYPES = {"SEARCH"}
READ_TYPES   = {"READ"}
EDIT_TYPES   = {"EDIT"}
TEST_TYPES   = {"TEST"}
ERR_TYPES    = {"TOOL_ERROR"}
ENV_TYPES    = {"ENVIRONMENT"}

def _safe_div(a, b):
    return (a / b) if b else None

def _first_index(events, pred) -> Optional[int]:
    for e in events:
        if pred(e):
            return e["event_index"]
    return None

def extract_features(nt: dict, model_stats: Optional[dict]=None) -> dict:
    events = nt.get("events", [])
    n = len(events)
    types = [e["normalized_action_type"] for e in events]
    tc = collections.Counter(types)

    # ---- TOOLS ----
    tool_calls = sum(1 for t in types if t not in ("PLAN","OTHER","FINISH"))
    tool_errors = tc.get("TOOL_ERROR", 0)
    # exact duplicate calls: identical tool_args_hash among action-bearing events
    arg_hashes = [e["tool_args_hash"] for e in events if e["tool_args_hash"]]
    hash_counts = collections.Counter(arg_hashes)
    exact_dup_calls = sum(c - 1 for c in hash_counts.values() if c > 1)
    # retry: an error event followed later by the same arg hash
    err_hashes = [e["tool_args_hash"] for e in events if e["normalized_action_type"]=="TOOL_ERROR" and e["tool_args_hash"]]
    retried = sum(1 for h in err_hashes if hash_counts.get(h,0) > 1)
    # tool churn: type switches between consecutive action events
    action_types = [t for t in types if t not in ("PLAN","OTHER")]
    churn = sum(1 for i in range(1,len(action_types)) if action_types[i]!=action_types[i-1])

    # ---- FILES (SWE-agent-specific) ----
    def files_of(pred):
        s = []
        for e in events:
            if pred(e):
                s += e.get("file_paths", [])
        return s
    searched_files = files_of(lambda e: e["normalized_action_type"] in SEARCH_TYPES)
    read_files     = files_of(lambda e: e["normalized_action_type"] in READ_TYPES)
    edited_files   = files_of(lambda e: e["normalized_action_type"] in EDIT_TYPES)
    read_counts = collections.Counter(read_files)

    # ---- patch churn: edits to the same file region repeatedly ----
    edit_events = [e for e in events if e["normalized_action_type"] in EDIT_TYPES]
    patch_attempts = len(edit_events)
    # reversion proxy: the cumulative diff (state.diff hash) returns to an EARLIER
    # value after having changed — i.e., the working tree rolled back. We track the
    # ordered sequence of DISTINCT diff states and count how often a state recurs
    # after a change (a true revert), NOT mere repetition of an unchanged diff.
    diff_seq = [e["patch_delta_hash"] for e in events if e["patch_delta_hash"]]
    patch_reversions = None
    if diff_seq:
        collapsed = [h for i, h in enumerate(diff_seq) if i == 0 or h != diff_seq[i-1]]  # drop consecutive repeats
        seen, reverts = set(), 0
        for h in collapsed:
            if h in seen:
                reverts += 1   # a diff-state we'd already left and came back to
            seen.add(h)
        patch_reversions = reverts

    # ---- tests ----
    test_events = [e for e in events if e["normalized_action_type"] in TEST_TYPES]
    test_cmds = collections.Counter(e["tool_args_hash"] for e in test_events if e["tool_args_hash"])
    unchanged_repeated_tests = sum(c-1 for c in test_cmds.values() if c>1)

    # ---- milestone steps (SWE-agent-specific) ----
    first_search = _first_index(events, lambda e: e["normalized_action_type"] in SEARCH_TYPES)
    first_edit   = _first_index(events, lambda e: e["normalized_action_type"] in EDIT_TYPES)  # first plausible-patch proxy
    first_test   = _first_index(events, lambda e: e["normalized_action_type"] in TEST_TYPES)
    first_passing_test = _first_index(events, lambda e: e["normalized_action_type"] in TEST_TYPES and e.get("test_result")=="PASS")

    # ---- stagnation: longest run with no NEW file touched & no new arg hash ----
    longest_no_new = 0; cur = 0; seen_hashes=set(); seen_files=set()
    for e in events:
        new = False
        if e["tool_args_hash"] and e["tool_args_hash"] not in seen_hashes:
            seen_hashes.add(e["tool_args_hash"]); new = True
        for f in e.get("file_paths", []):
            if f not in seen_files:
                seen_files.add(f); new = True
        if new:
            cur = 0
        else:
            cur += 1; longest_no_new = max(longest_no_new, cur)

    # ---- error clustering: TOOL_ERROR runs (tool failure loop signal) ----
    longest_err_run = 0; cur_err = 0
    for t in types:
        if t == "TOOL_ERROR":
            cur_err += 1; longest_err_run = max(longest_err_run, cur_err)
        else:
            cur_err = 0

    # ---- termination ----
    term = nt.get("outcome", {}).get("exit_status")

    # ---- ROOFLINE (trace-level, from model_stats if present; else null) ----
    ms = model_stats or {}
    total_tokens = None
    if "tokens_sent" in ms or "tokens_received" in ms:
        total_tokens = (ms.get("tokens_sent") or 0) + (ms.get("tokens_received") or 0)
    feat = {
        # RESOURCE / ROOFLINE (per-event tokens unavailable in .traj -> null)
        "prefill_tokens": ms.get("tokens_sent"),
        "decode_tokens": ms.get("tokens_received"),
        "total_tokens": total_tokens,
        "api_calls": ms.get("api_calls"),
        "cost_estimate_usd": ms.get("instance_cost"),
        "wall_time_s": None, "cpu_time_s": None, "peak_rss_bytes": None,
        "energy_estimate": None, "parallelism_depth": None,

        # TOOLS
        "tool_call_count": tool_calls,
        "tool_error_count": tool_errors,
        "tool_error_rate": _safe_div(tool_errors, tool_calls),
        "exact_duplicate_call_count": exact_dup_calls,
        "exact_duplicate_call_rate": _safe_div(exact_dup_calls, tool_calls),
        "retry_count": retried,
        "tool_churn": churn,
        "tool_churn_rate": _safe_div(churn, max(len(action_types)-1,0) or None),
        # semantic/near-dup & result-utilization need content -> LOW observability, null at L0
        "semantic_near_duplicate_call_rate": None,
        "result_utilization": None,
        "unused_result_count": None,

        # MEMORY / CONTEXT — SWE-agent has no memory layer -> null (honest)
        "retrieval_utilization": None, "recall_miss_candidate_rate": None,
        "redundant_retrieval": None, "redundant_write": None,
        "memory_write_yield": None, "memory_token_overhead": None,
        "context_compaction_events": None,

        # SWE-AGENT-SPECIFIC
        "n_events": n,
        "event_type_counts": dict(tc),
        "unique_files_searched": len(set(searched_files)),
        "unique_files_read": len(set(read_files)),
        "duplicate_file_reads": sum(c-1 for c in read_counts.values() if c>1),
        "repeated_region_reads": None,  # needs line-range parse -> deferred, null
        "search_call_count": tc.get("SEARCH",0),
        "files_modified": len(set(edited_files)),
        "patch_attempts": patch_attempts,
        "patch_reversions": patch_reversions,
        "patch_churn": _safe_div(patch_attempts, len(set(edited_files)) or None),
        "targeted_test_count": len(test_events),
        "unchanged_repeated_tests": unchanged_repeated_tests,
        "environment_setup_events": tc.get("ENVIRONMENT",0),
        "longest_tool_error_run": longest_err_run,
        "first_search_step": first_search,
        "first_edit_step": first_edit,           # first plausible-patch proxy
        "first_test_step": first_test,
        "first_passing_test_step": first_passing_test,  # first improving-test proxy (lexical)
        "longest_no_new_evidence_streak": longest_no_new,
        "termination_reason": term,

        # provenance of what's deterministic vs deferred
        "_null_reason": {
            "result_utilization": "needs span content + lexical compare (TokenSaver layer); LOW observability at L0",
            "memory_*": "SWE-agent has no memory/retrieval layer",
            "wall/cpu/rss": "not present in .traj; would come from TokenSaver OTel spans",
            "repeated_region_reads": "needs line-range parse (deferred to L1)",
        },
    }
    return feat

if __name__ == "__main__":
    import argparse, json, os, sys
    sys.path.insert(0, os.path.dirname(__file__))
    from normalize_traces import normalize_trace, load_raw
    ap = argparse.ArgumentParser(); ap.add_argument("path"); ap.add_argument("--alias",default="solver_X")
    a = ap.parse_args()
    raw = load_raw(a.path); tid = os.path.basename(a.path).split(".")[0]
    nt = normalize_trace(raw, trace_id=tid+"@"+a.alias, task_id=tid, solver_alias=a.alias, source_path=a.path)
    feat = extract_features(nt, model_stats=(raw.get("info",{}) or {}).get("model_stats"))
    print(json.dumps(feat, indent=2, default=str))
