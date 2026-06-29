#!/usr/bin/env python3
"""extract_clean_trace_features.py — INDEPENDENT clean-room deterministic features.

Computes FULL-TRACE and PREFIX (T5/T10/T20) features from raw SWE-agent traces
via the clean-room loader+classifier (NOT the existing taxonomy code). Every
feature: observable, outcome-independent, normalized by an explicit denominator,
missing-value explicit (None, never 0), auditable via step indices.

Usage:
  python extract_clean_trace_features.py --source <path> --solver <alias> \
      --layout <classic_traj|mini|openhands> --out features.jsonl [--prefix]
"""
from __future__ import annotations
import argparse, json, os, glob, re, hashlib
from collections import Counter, defaultdict

import sys
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import clean_loader as CL
import clean_classify as CC

# ---------- deterministic helpers ----------
def _norm_ws(s): return re.sub(r"\s+", " ", (s or "")).strip()
def _h(s): return hashlib.sha1(_norm_ws(s).encode("utf-8","replace")).hexdigest()[:12]

# file-path extraction from an action string (surface heuristic, layout-agnostic)
_PATH_RE = re.compile(r"(?:^|[\s'\"=(])(/?[\w./-]+\.[A-Za-z]{1,5})\b")
def _paths(text):
    out = []
    for m in _PATH_RE.finditer(text or ""):
        p = m.group(1)
        if len(p) > 3 and "/" in p or p.endswith((".py",".txt",".cfg",".toml",".ini",".rst",".md",".json",".yaml",".yml",".c",".h",".cpp",".js")):
            out.append(p.lstrip("/"))
    return out

# search query token-set (for near-dup detection)
def _query_sig(text):
    # strip the search verb, keep the pattern tokens
    t = re.sub(r"^\s*(grep|rg|ag|find|search_file|search_dir|find_file|git grep|egrep|fgrep)\b", "", text or "", flags=re.I)
    toks = sorted(set(re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", t.lower())))
    return tuple(toks)

def _obs_filehits(obs):
    """candidate files referenced in an observation (search results / listings)."""
    return set(_paths(obs))

def _is_empty_result(obs):
    o = (obs or "").strip().lower()
    if not o: return True
    return bool(re.search(r"(no matches|not found|no such file|0 results|nothing|no files? found|command not found)", o))

def _is_error_obs(obs):
    o = (obs or "")
    if not o.strip(): return False
    # STRONG, low-false-positive signals only. Warnings / incidental "error:" substrings excluded.
    # 1) explicit non-zero return/exit code markers (SWE-agent / OpenHands wrappers)
    if re.search(r"(<returncode>\s*[1-9]\d*\s*</returncode>|exit code:\s*[1-9]\d*|returncode=\s*[1-9])", o, re.I):
        return True
    # 2) a real Python traceback
    if "Traceback (most recent call last)" in o:
        return True
    # 3) shell hard-failures at line start
    if re.search(r"(^|\n)\s*(bash:|/bin/sh:|.*: command not found|.*: No such file or directory|fatal:)", o):
        return True
    # 4) explicit error lines at line start (not mid-text), e.g. "SyntaxError:", "ImportError:", "E   "
    if re.search(r"(^|\n)\s*([A-Z][a-zA-Z]*Error|Exception|ERROR)\b\s*:", o):
        return True
    if re.search(r"(^|\n)E\s{2,}\w", o):  # pytest failure marker lines
        return True
    return False

def _is_oversized(obs, thresh=8000):
    return obs is not None and len(obs) >= thresh

def _is_truncated(obs):
    return bool(re.search(r"(\.\.\.\s*\(?truncated|output truncated|\[truncated\]|too long|lines? omitted|<response clipped>)", obs or "", re.I))

# ---------- per-trace feature computation ----------
def compute_features(steps, prefix_k=None):
    """steps: list from clean_loader. prefix_k: if set, only use first k action-steps."""
    # classify each step
    cls_steps = []
    for s in steps:
        a = s["action_text"]
        if not a and not s["thought"]:
            continue
        cls, ev = CC.classify(a, s.get("raw_tool"), a)
        cls_steps.append({**s, "cls": cls, "ev": ev})
    if prefix_k is not None:
        # prefix over ACTION steps (those with a non-empty action)
        act_idx = [i for i,s in enumerate(cls_steps) if s["action_text"]]
        if len(act_idx) > prefix_k:
            cutoff = act_idx[prefix_k-1]
            cls_steps = cls_steps[:cutoff+1]

    n_steps = len(cls_steps)
    actions = [s for s in cls_steps if s["action_text"]]
    n_act = len(actions)
    by = Counter(s["cls"] for s in actions)
    F = {}
    F["n_steps"] = n_steps
    F["n_actions"] = n_act
    F["cls_counts"] = dict(by)

    searches = [s for s in actions if s["cls"]=="SEARCH"]
    reads    = [s for s in actions if s["cls"]=="READ"]
    edits    = [s for s in actions if s["cls"]=="EDIT"]
    tests    = [s for s in actions if s["cls"]=="TEST"]
    envs     = [s for s in actions if s["cls"]=="ENV"]
    errors   = [s for s in actions if _is_error_obs(s["observation_text"])]

    # ===== 9.1 SEARCH information gain =====
    F["search_call_count"] = len(searches)
    if searches:
        sigs = [_query_sig(s["action_text"]) for s in searches]
        exact_rep = 0; seen=set()
        for sig in sigs:
            if sig in seen: exact_rep += 1
            seen.add(sig)
        F["exact_repeated_search_count"] = exact_rep
        # candidate-set expansion: running union of files seen in search results
        cand=set(); no_expand=0; empty=0; same_result=0; prev_hits=None
        for s in searches:
            hits=_obs_filehits(s["observation_text"])
            if _is_empty_result(s["observation_text"]): empty+=1
            new = hits - cand
            if not new: no_expand += 1
            if prev_hits is not None and hits==prev_hits and hits: same_result += 1
            prev_hits=hits; cand |= hits
        F["empty_result_search_count"] = empty
        F["same_result_search_count"] = same_result
        F["searches_without_candidate_set_expansion"] = no_expand
        F["search_no_new_evidence_rate"] = round(no_expand/len(searches), 4)  # PRIMARY
        F["candidate_files_discovered"] = len(cand)
    else:
        for k in ["exact_repeated_search_count","empty_result_search_count","same_result_search_count",
                  "searches_without_candidate_set_expansion","candidate_files_discovered"]:
            F[k]=None
        F["search_no_new_evidence_rate"]=None   # missing, NOT 0 (no exposure)

    # ===== 9.2 File reading & context =====
    F["read_call_count"] = len(reads)
    read_targets = []
    for s in reads:
        ps=_paths(s["action_text"]) or _paths(s["observation_text"][:200])
        read_targets.append(ps[0] if ps else None)
    uniq_read = set(p for p in read_targets if p)
    F["unique_files_read"] = len(uniq_read) if reads else None
    if reads:
        seen=set(); reread=0
        for p in read_targets:
            if p and p in seen: reread+=1
            if p: seen.add(p)
        F["exact_file_reread_count"]=reread
        # oversized-then-narrow: an oversized/truncated read followed later by a read of same file
        oversized=[i for i,s in enumerate(reads) if _is_oversized(s["observation_text"]) or _is_truncated(s["observation_text"])]
        F["oversized_read_count"]=len(oversized)
        F["truncated_read_count"]=sum(1 for s in reads if _is_truncated(s["observation_text"]))
        otn=0
        for i in oversized:
            tp=read_targets[i]
            if tp and tp in read_targets[i+1:]:
                otn+=1
        F["oversized_then_narrow_read_count"]=otn
        F["oversized_then_narrow_read_rate"]=round(otn/len(reads),4)
        F["redundant_reread_rate"]=round(reread/len(reads),4)
    else:
        for k in ["exact_file_reread_count","oversized_read_count","truncated_read_count",
                  "oversized_then_narrow_read_count","oversized_then_narrow_read_rate","redundant_reread_rate"]:
            F[k]=None

    # ===== 9.3 Patch behavior =====
    F["edit_count"]=len(edits)
    edit_targets=[]
    for s in edits:
        ps=_paths(s["action_text"])
        edit_targets.append(ps[0] if ps else None)
    F["unique_files_modified"]=len(set(p for p in edit_targets if p)) if edits else None
    # detect edit-tool MECHANICAL FAILURE (old_str not matched / no replacement) — a DISTINCT behavior
    # from reasoning churn. Surfaced by inspection (Skywork/SWE-agent-LM 'No replacement was performed').
    def _edit_failed(obs):
        return bool(re.search(r"(No replacement was performed|did not appear verbatim|"
                              r"multiple occurrences|_split_string|future feature annotations|"
                              r"No edit was made|Parameter .* is required)", obs or "", re.I))
    def _edit_applied(obs):
        if _edit_failed(obs): return False
        return bool(re.search(r"(has been edited|File created|edited\.|successfully|"
                              r"result of running .*cat -n)", obs or "", re.I)) or len(obs or "")>0
    if edits:
        n_failed = sum(1 for s in edits if _edit_failed(s["observation_text"]))
        F["edit_mechanical_failure_count"]=n_failed
        F["edit_mechanical_failure_rate"]=round(n_failed/len(edits),4)
        # churn computed over APPLIED edits only (exclude mechanical-failure retries)
        no_evidence_reedit=0; same_file_reedit=0
        last_edit_pos={}
        applied_edits=0
        for pos,s in enumerate(actions):
            if s["cls"]!="EDIT": continue
            if _edit_failed(s["observation_text"]):
                continue  # mechanical failure: not a real edit, skip for churn
            applied_edits+=1
            ps=_paths(s["action_text"]); tgt=ps[0] if ps else None
            if tgt in last_edit_pos:
                same_file_reedit+=1
                between=actions[last_edit_pos[tgt]+1:pos]
                gained=any(b["cls"] in ("TEST","SEARCH","READ") for b in between)
                gained = gained or any(_is_error_obs(b["observation_text"]) for b in between)
                if not gained: no_evidence_reedit+=1
            if tgt: last_edit_pos[tgt]=pos
        F["applied_edit_count"]=applied_edits
        F["same_file_reedit_count"]=same_file_reedit
        F["no_evidence_reedit_count"]=no_evidence_reedit
        # denominator = applied edits (>=2 needed); None if too few applied edits
        F["no_evidence_patch_churn_rate"]=round(no_evidence_reedit/applied_edits,4) if applied_edits>=2 else None  # PRIMARY
    else:
        for k in ["edit_mechanical_failure_count","edit_mechanical_failure_rate","applied_edit_count",
                  "same_file_reedit_count","no_evidence_reedit_count","no_evidence_patch_churn_rate"]:
            F[k]=None

    # ===== 9.4 Verification =====
    F["has_production_edit"]= bool(edits)
    F["test_count"]=len(tests)
    if edits:
        last_edit_pos_global=max(i for i,s in enumerate(actions) if s["cls"]=="EDIT")
        tests_after=[i for i,s in enumerate(actions) if s["cls"]=="TEST" and i>last_edit_pos_global]
        F["test_after_last_edit"]=len(tests_after)
        # POST_EDIT_TEST_GAP: steps from last edit to next test (None if no test after)
        if tests_after:
            F["post_edit_test_gap"]=tests_after[0]-last_edit_pos_global
        else:
            F["post_edit_test_gap"]=None   # no post-edit test -> gap undefined (NOT 0)
        F["no_test_after_edit"]= (len(tests_after)==0)
    else:
        F["test_after_last_edit"]=None
        F["post_edit_test_gap"]=None
        F["no_test_after_edit"]=None
    # identical test re-run w/o state change between
    if tests:
        sigs=[_h(s["action_text"]) for s in tests]
        rep=0; seen=set()
        for i,s in enumerate([a for a in actions if a["cls"]=="TEST"]):
            sg=_h(s["action_text"])
            if sg in seen: rep+=1
            seen.add(sg)
        F["identical_test_rerun_count"]=rep
    else:
        F["identical_test_rerun_count"]=None

    # ===== 9.5 Stagnation & progress =====
    # result-hash novelty over the full action stream
    if n_act:
        res_hashes=[_h(s["observation_text"][:2000]) for s in actions]
        seen=set(); novel=0
        for h in res_hashes:
            if h not in seen: novel+=1
            seen.add(h)
        F["new_result_hash_rate"]=round(novel/n_act,4)
        # longest streak of consecutive actions producing NO new result hash AND no new file
        seen_h=set(); seen_f=set(); streak=0; longest=0; in_streak=0; tot_in_streak=0
        for s in actions:
            h=_h(s["observation_text"][:2000])
            fs=set(_paths(s["action_text"]))|_obs_filehits(s["observation_text"])
            new = (h not in seen_h) or bool(fs-seen_f)
            if new:
                longest=max(longest,streak); streak=0
            else:
                streak+=1; tot_in_streak+=1
            seen_h.add(h); seen_f|=fs
        longest=max(longest,streak)
        F["longest_no_new_evidence_streak"]=longest
        F["fraction_actions_in_no_new_evidence_streaks"]=round(tot_in_streak/n_act,4)  # PRIMARY (stagnation_fraction)
        # repeated action signature rate
        asigs=[_h(s["action_text"]) for s in actions]
        c=Counter(asigs); rep_sig=sum(v-1 for v in c.values() if v>1)
        F["repeated_action_signature_rate"]=round(rep_sig/n_act,4)
    else:
        for k in ["new_result_hash_rate","longest_no_new_evidence_streak",
                  "fraction_actions_in_no_new_evidence_streaks","repeated_action_signature_rate"]:
            F[k]=None

    # ===== 9.6 Tooling & environment =====
    if n_act:
        F["tool_error_count"]=len(errors)
        F["tool_error_rate"]=round(len(errors)/n_act,4)  # PRIMARY
        # consecutive error max
        cmax=0; cur=0
        for s in actions:
            if _is_error_obs(s["observation_text"]): cur+=1; cmax=max(cmax,cur)
            else: cur=0
        F["consecutive_tool_error_max"]=cmax
        # same failed call retried
        fail_sigs=Counter(_h(s["action_text"]) for s in actions if _is_error_obs(s["observation_text"]))
        F["same_failed_call_retry_count"]=sum(v-1 for v in fail_sigs.values() if v>1)
        F["environment_setup_event_count"]=len(envs)
        F["environment_setup_rate"]=round(len(envs)/n_act,4)
    else:
        for k in ["tool_error_count","tool_error_rate","consecutive_tool_error_max",
                  "same_failed_call_retry_count","environment_setup_event_count","environment_setup_rate"]:
            F[k]=None

    return F

def process_one(path, solver, prefixes=False):
    try:
        steps = CL.load_file(path)
    except Exception as e:
        return {"source_path": path, "solver_alias": solver, "parse_status": f"ERROR:{type(e).__name__}",
                "content_available": False}
    if not steps:
        return {"source_path": path, "solver_alias": solver, "parse_status": "EMPTY", "content_available": False}
    task_id = os.path.basename(path).split(".")[0]
    row = {"trace_id": f"{task_id}@{solver}", "task_id": task_id, "solver_alias": solver,
           "source_path": path, "parse_status": "OK", "content_available": True,
           "full": compute_features(steps)}
    if prefixes:
        row["prefix"] = {f"T{k}": compute_features(steps, prefix_k=k) for k in (5,10,20)}
    return row

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--solver", required=True)
    ap.add_argument("--glob", default=None, help="glob pattern under source")
    ap.add_argument("--out", required=True)
    ap.add_argument("--prefix", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    pats = [a.glob] if a.glob else ["*.traj","*/*.traj","*/*.traj.json","*.json"]
    files=[]
    for p in pats:
        files += glob.glob(os.path.join(a.source, p))
    files = sorted(set(f for f in files if not f.endswith(".pred")))
    if a.limit: files=files[:a.limit]
    n=0
    with open(a.out,"w") as out:
        for f in files:
            row = process_one(f, a.solver, prefixes=a.prefix)
            out.write(json.dumps(row)+"\n"); n+=1
    print(f"wrote {n} rows -> {a.out}")

if __name__ == "__main__":
    main()
