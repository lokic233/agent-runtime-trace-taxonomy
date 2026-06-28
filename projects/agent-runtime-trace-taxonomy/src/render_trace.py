#!/usr/bin/env python3
"""render_trace.py — produce a BLINDED, human/LLM-readable view of a trace for annotation.

Reads the private locator (trace_id -> path+node) to find the raw file, normalizes it,
and renders a compact blinded transcript: per-event index, normalized type, the action
text, and a truncated observation. NO model name, NO file path leaks into the output.

Cutoff support (Section 10 firewall): FULL | T0 | T5 | T10 | T20.
For a prefix cutoff Tk, ONLY the first k meaningful events are shown AND every
outcome/late signal is withheld (enforced by generate_trace_prefixes.py; this renderer
also refuses to print outcome for any cutoff).
"""
from __future__ import annotations
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from normalize_traces import normalize_trace, load_raw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCATOR = os.path.join(HERE, "private", "trace_locator.jsonl")

def _locator_map(path=LOCATOR):
    m={}
    if os.path.exists(path):
        for l in open(path):
            r=json.loads(l); m[r["trace_id"]]=r
    return m

CUTOFFS={"T0":0,"T5":5,"T10":10,"T20":20,"FULL":None}

def render(trace_id: str, alias: str, cutoff: str="FULL", max_obs_chars=600, max_act_chars=400) -> dict:
    loc=_locator_map().get(trace_id)
    if not loc:
        raise KeyError(f"no locator for {trace_id}; build manifest first")
    raw=load_raw(loc["source_path"])
    task_id=trace_id.split("@")[0]
    nt=normalize_trace(raw, trace_id=trace_id, task_id=task_id, solver_alias=alias)
    k=CUTOFFS.get(cutoff, None)
    events=nt["events"] if k is None else nt["events"][:k]
    # also pull raw action/observation text for the shown events (blinded)
    # we re-walk the raw to get the human text without re-leaking identity
    shown=[]
    for e in events:
        shown.append({
            "i": e["event_index"],
            "type": e["normalized_action_type"],
            "files": e["file_paths"][:6],
            "error": e["error_type"],
            "test_result": e["test_result"],
        })
    # task prompt (the PR/issue text) — needed for workload labeling; blinded already
    issue=_issue_text(raw)
    out={
        "trace_id": trace_id, "task_id": task_id, "repo": (task_id.split("__")[0] if "__" in task_id else None),
        "solver_alias": alias, "cutoff": cutoff,
        "n_events_shown": len(shown), "n_events_total_hidden": (None if k is None else "HIDDEN"),
        "issue_text": issue[:2000] if issue else None,
        "events": shown,
        "transcript": _transcript(raw, nt, k, max_act_chars, max_obs_chars),
    }
    # FIREWALL: never include outcome/resolved/final patch for ANY cutoff in the render.
    # (FULL annotation reads outcome from a separate controlled channel, not here.)
    return out

def _issue_text(raw):
    # classic: history[1] user content has <pr_description> / issue; mini: messages[1]
    msgs=raw.get("history") or raw.get("messages") or []
    for m in msgs[:4]:
        c=m.get("content")
        if isinstance(c,str) and ("<pr_description>" in c or "issue" in c.lower() or "PR description" in c):
            return c
    # fallback: first user message
    for m in msgs:
        if m.get("role")=="user":
            return m.get("content") if isinstance(m.get("content"),str) else None
    return None

def _transcript(raw, nt, k, max_act, max_obs):
    """Compact blinded transcript of action/observation pairs."""
    lines=[]
    traj=raw.get("trajectory")
    if traj:  # classic
        for i,step in enumerate(traj):
            if k is not None and i>=k: break
            act=str(step.get("action") or "").strip()[:max_act]
            obs=str(step.get("observation") or "").strip()
            obs=(obs[:max_obs]+" …[truncated]") if len(obs)>max_obs else obs
            th=str(step.get("thought") or "").strip()[:200]
            lines.append(f"[{i}] {nt['events'][i]['normalized_action_type'] if i<len(nt['events']) else '?'}")
            if th: lines.append(f"    think: {th}")
            if act: lines.append(f"    act:   {act}")
            if obs: lines.append(f"    obs:   {obs}")
    else:  # mini messages
        idx=0
        msgs=raw.get("messages",[])
        i=0
        while i<len(msgs):
            m=msgs[i]
            if m.get("role")=="assistant":
                if k is not None and idx>=k: break
                c=m.get("content") or ""
                c=c if isinstance(c,str) else json.dumps(c)
                lines.append(f"[{idx}] {nt['events'][idx]['normalized_action_type'] if idx<len(nt['events']) else '?'}")
                lines.append(f"    act:   {c.strip()[:max_act]}")
                if i+1<len(msgs) and msgs[i+1].get("role")=="user":
                    o=msgs[i+1].get("content") or ""
                    o=o if isinstance(o,str) else json.dumps(o)
                    o=(o[:max_obs]+" …[truncated]") if len(o)>max_obs else o
                    lines.append(f"    obs:   {o.strip()}")
                    i+=1
                idx+=1
            i+=1
    return "\n".join(lines)

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("trace_id"); ap.add_argument("--alias",required=True); ap.add_argument("--cutoff",default="FULL")
    a=ap.parse_args()
    r=render(a.trace_id, a.alias, a.cutoff)
    # quick blinding self-check on the rendered blob
    blob=json.dumps(r).lower()
    for banned in ("claude","opus","sonnet","qwen","gemini","anthropic","/data/","/home/"):
        assert banned not in blob, f"LEAK: {banned}"
    print(r["transcript"][:1500])
    print("\n--- issue (head) ---\n", (r["issue_text"] or "")[:300])
