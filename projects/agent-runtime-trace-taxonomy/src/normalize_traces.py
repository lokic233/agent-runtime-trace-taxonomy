#!/usr/bin/env python3
"""normalize_traces.py — L0 fact layer.

Convert raw SWE-agent trajectories (4 on-disk layouts) into the canonical
normalized-trace schema. Source events are preserved (hashes/raw_action_type);
absent fields are null + availability flag, NEVER zero.

Layouts handled (validated 2026-06-28):
  classic_traj      : {trajectory:[{action,observation,thought,response,state,...}], history, info}
                      flat file  trajs/<inst>.traj           (solver_C 3.5-sonnet, solver_E 32B)
                      nested     <inst>/<inst>.traj           (solver_A opus-4.7, solver_F opus-4.6)
  mini_swe_agent    : {messages:[{role,content,...}], tools, info, trajectory_format:'mini-swe-agent-1'}
                      nested     trajs/<inst>/<inst>.traj.json (solver_B live-SWE-agent opus-4.5)

BLINDING: callers pass solver_alias (solver_A..F). The real model name is NEVER
read here or written to output. capability_tier/locality come from the (private)
alias map and are the ONLY model hints exported.
"""
from __future__ import annotations
import json, hashlib, re, os
from typing import Any, Optional

SCHEMA_VERSION = "L0_v1"

NORM_TYPES = {"PLAN","SEARCH","READ","RETRIEVE","EDIT","PATCH_APPLY","TEST","EXECUTE",
              "TOOL_ERROR","ENVIRONMENT","FINISH","OTHER"}

# ---- deterministic helpers -------------------------------------------------
def _sha(s: Optional[str]) -> Optional[str]:
    if s is None: return None
    return hashlib.sha256(s.encode("utf-8", "replace")).hexdigest()[:16]

def _norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()

# Command -> canonical event type. Order matters (first match wins).
_PATTERNS = [
    ("TEST",        re.compile(r"\b(pytest|tox|unittest|py\.test|nosetests|python -m pytest|python -m unittest|\./tests?/|run_tests)\b", re.I)),
    ("PATCH_APPLY", re.compile(r"\b(git apply|patch -p|git commit|git checkout -- |apply_patch)\b", re.I)),
    ("EDIT",        re.compile(r"\b(edit|str_replace|insert|create|sed -i|tee |>>|cat\s*>\s*|apply_edit)\b", re.I)),
    ("SEARCH",      re.compile(r"\b(grep|rg|ag|find\b|search|git grep|ack|locate|fgrep|egrep)\b", re.I)),
    ("READ",        re.compile(r"\b(cat |head |tail |less |open |view |sed -n|nl |wc -l|scroll|goto|less\b|more\b)\b", re.I)),
    ("RETRIEVE",    re.compile(r"\b(retrieve|recall|memory_search|vector|embed)\b", re.I)),
    ("ENVIRONMENT", re.compile(r"\b(pip install|conda |apt-get|setup\.py|pip3|python setup|make install|export |source |cd /|docker|podman|requirements\.txt)\b", re.I)),
]

def classify_command(cmd: Optional[str], thought: Optional[str]=None) -> str:
    """Map a shell action (and/or tool name) to a canonical type. Evidence only."""
    if not cmd:
        # No command but a thought present -> planning/reasoning step
        return "PLAN" if thought else "OTHER"
    c = cmd.strip()
    # submission / finish signals
    if re.search(r"\b(submit|DISCUSSION|<<EOF.*git diff|echo.*COMPLETE)\b", c) and "diff" in c.lower():
        return "PATCH_APPLY"
    if c.lower() in ("submit","exit","finish") or c.startswith("submit"):
        return "FINISH"
    for typ, pat in _PATTERNS:
        if pat.search(c):
            return typ
    return "EXECUTE"

def _extract_paths(text: str) -> list[str]:
    if not text: return []
    # file-ish tokens: a/b/c.py, ./x/y.ext, /testbed/...
    paths = re.findall(r"(?:\.?/)?(?:[\w.\-]+/){1,}[\w.\-]+\.\w{1,6}", text)
    # dedupe preserve order, cap
    seen, out = set(), []
    for p in paths:
        p = p.strip()
        if p and p not in seen:
            seen.add(p); out.append(p)
        if len(out) >= 25: break
    return out

def _obs_is_error(obs: Optional[str]) -> Optional[str]:
    if obs is None: return None
    o = obs.lower()
    for marker in ("traceback (most recent call last)","command not found","no such file",
                   "error:","permission denied","syntaxerror","modulenotfounderror",
                   "importerror","exit code 1","returncode>1","fatal:","cannot "):
        if marker in o:
            return marker.split(":")[0].split(">")[0].strip()
    return None

def _test_result(obs: Optional[str]) -> Optional[str]:
    if obs is None: return None
    o = obs.lower()
    has_pass = "passed" in o or re.search(r"\bok\b", o)
    has_fail = "failed" in o or "error" in o or "assertionerror" in o
    if has_pass and has_fail: return "MIXED"
    if has_fail: return "FAIL"
    if has_pass: return "PASS"
    return "UNKNOWN"

# ---- per-layout step extraction -------------------------------------------
def _events_from_classic(traj: list[dict]) -> list[dict]:
    """classic_traj: trajectory[] has action/observation/thought/response/state."""
    events = []
    for i, step in enumerate(traj):
        action = step.get("action")
        thought = step.get("thought") or (step.get("response") if not action else None)
        obs = step.get("observation")
        ntype = classify_command(action, thought)
        err = _obs_is_error(obs)
        if err and ntype not in ("TEST",):
            # an erroring command is still its type, but we also flag error_type;
            # a pure tool failure with no useful type -> TOOL_ERROR
            pass
        is_test = ntype == "TEST"
        ev = {
            "event_index": i,
            "raw_action_type": _norm_ws(action)[:60] if action else ("thought" if thought else None),
            "normalized_action_type": "TOOL_ERROR" if (err and ntype=="EXECUTE") else ntype,
            "tool_name": None,
            "tool_args_hash": _sha(_norm_ws(action)) if action else None,
            "tool_output_hash": _sha(obs) if obs else None,
            "file_paths": _extract_paths((action or "") + " " + (obs or ""))[:25],
            "symbol_names": [],
            "test_command": action if is_test else None,
            "test_result": _test_result(obs) if is_test else None,
            "input_tokens": None, "output_tokens": None, "context_tokens": None,
            "error_type": err,
            "patch_delta_hash": _sha(step.get("state",{}).get("diff")) if isinstance(step.get("state"),dict) and step.get("state",{}).get("diff") else None,
            "content_available": bool(action is not None or obs is not None or thought),
        }
        events.append(ev)
    return events

def _events_from_mini(messages: list[dict]) -> list[dict]:
    """mini_swe_agent: messages[] system/user/assistant. assistant=THOUGHT+bash,
    following user msg = <returncode>/<output> observation for that action."""
    events = []
    idx = 0
    i = 0
    n = len(messages)
    while i < n:
        m = messages[i]
        role = m.get("role")
        content = m.get("content")
        if isinstance(content, list):  # some emitters chunk content
            content = " ".join(str(c.get("text", c)) if isinstance(c, dict) else str(c) for c in content)
        if role == "assistant":
            thought, action = _split_mini_action(content or "")
            # observation is the NEXT user message
            obs = None
            if i + 1 < n and messages[i+1].get("role") == "user":
                oc = messages[i+1].get("content")
                obs = oc if isinstance(oc, str) else json.dumps(oc)
            ntype = classify_command(action, thought)
            err = _obs_is_error(obs)
            is_test = ntype == "TEST"
            events.append({
                "event_index": idx,
                "raw_action_type": _norm_ws(action)[:60] if action else "assistant_thought",
                "normalized_action_type": "TOOL_ERROR" if (err and ntype=="EXECUTE") else ntype,
                "tool_name": None,
                "tool_args_hash": _sha(_norm_ws(action)) if action else None,
                "tool_output_hash": _sha(obs) if obs else None,
                "file_paths": _extract_paths((action or "") + " " + (obs or ""))[:25],
                "symbol_names": [],
                "test_command": action if is_test else None,
                "test_result": _test_result(obs) if is_test else None,
                "input_tokens": None, "output_tokens": None, "context_tokens": None,
                "error_type": err, "patch_delta_hash": None,
                "content_available": bool(content or obs),
            })
            idx += 1
            i += 2 if obs is not None else 1
        else:
            i += 1
    return events

def _split_mini_action(content: str) -> tuple[Optional[str], Optional[str]]:
    """mini format: 'THOUGHT: ...\\n```bash\\n<cmd>\\n```' (or THOUGHT/ACTION markers)."""
    thought, action = None, None
    mt = re.search(r"THOUGHT:\s*(.+?)(?=```|ACTION:|$)", content, re.S | re.I)
    if mt: thought = mt.group(1).strip()
    mb = re.search(r"```(?:bash|sh)?\s*(.+?)```", content, re.S)
    if mb:
        action = mb.group(1).strip()
    else:
        ma = re.search(r"ACTION:\s*(.+)$", content, re.S | re.I)
        if ma: action = ma.group(1).strip()
    if thought is None and action is None and content:
        thought = content.strip()[:500]
    return thought, action

# ---- top-level -------------------------------------------------------------
def detect_layout(raw: dict) -> str:
    if raw.get("trajectory_format","").startswith("mini") or ("messages" in raw and "trajectory" not in raw):
        return "mini_swe_agent"
    if "trajectory" in raw and isinstance(raw["trajectory"], list):
        return "classic_traj"
    if "messages" in raw:
        return "mini_swe_agent"
    return "unknown"

def _outcome(raw: dict) -> dict:
    info = raw.get("info", {}) or {}
    exit_status = info.get("exit_status")
    submission = info.get("submission")
    # resolved is NOT in the .traj (that's in eval logs) -> null here, set by joiner
    return {
        "resolved": None,
        "exit_status": exit_status,
        "submission_present": bool(submission) if submission is not None else None,
    }

def normalize_trace(raw: dict, *, trace_id: str, task_id: str, solver_alias: str,
                    repo: Optional[str]=None, capability_tier: Optional[str]=None,
                    locality: Optional[str]=None, source_path: Optional[str]=None) -> dict:
    layout = detect_layout(raw)
    warnings = []
    if layout == "classic_traj":
        events = _events_from_classic(raw["trajectory"])
        harness = "swe-agent-1.0"
    elif layout == "mini_swe_agent":
        events = _events_from_mini(raw.get("messages", []))
        harness = "live-swe-agent(mini-swe-agent-1)"
    else:
        events = []
        harness = "unknown"
        warnings.append(f"unknown_layout:{list(raw.keys())[:6]}")

    # mark FINISH on the last event if a submission exists and it isn't already terminal
    info = raw.get("info", {}) or {}
    if events and info.get("submission") and events[-1]["normalized_action_type"] not in ("FINISH","PATCH_APPLY"):
        events[-1] = {**events[-1], "raw_action_type": (events[-1]["raw_action_type"] or "")+"|submit"}

    # stamp blinded identity onto every event
    for e in events:
        e["trace_id"] = trace_id
        e["task_id"] = task_id
        e["repo"] = repo
        e["solver_alias"] = solver_alias
        e["source_harness"] = harness
        e["timestamp_start"] = None
        e["timestamp_end"] = None
        e["_evidence"] = None

    content_avail = any(e.get("content_available") for e in events) if events else False
    return {
        "trace_id": trace_id, "task_id": task_id, "repo": repo,
        "solver_alias": solver_alias, "capability_tier": capability_tier, "locality": locality,
        "source_harness": harness, "source_path": source_path,
        "schema_version": SCHEMA_VERSION,
        "n_events": len(events), "events": events,
        "outcome": _outcome(raw),
        "deterministic_features": None,  # filled by extract_deterministic_features.py
        "content_available": content_avail,
        "parse_warnings": warnings,
    }

def load_raw(path: str) -> dict:
    with open(path) as f:
        return json.load(f)

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("path"); ap.add_argument("--alias", default="solver_X")
    ap.add_argument("--task", default=None)
    a = ap.parse_args()
    raw = load_raw(a.path)
    tid = a.task or os.path.basename(a.path).split(".")[0]
    nt = normalize_trace(raw, trace_id=tid+"@"+a.alias, task_id=tid, solver_alias=a.alias, source_path=a.path)
    print(json.dumps({k:v for k,v in nt.items() if k!="events"}, indent=2))
    print(f"... {nt['n_events']} events; types:",
          {t: sum(1 for e in nt['events'] if e['normalized_action_type']==t) for t in NORM_TYPES if any(e['normalized_action_type']==t for e in nt['events'])})
