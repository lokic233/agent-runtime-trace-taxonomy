#!/usr/bin/env python3
"""prune_methods.py — context-pruning transforms applied at the shim, on the Anthropic
`messages` array, BEFORE the PlugBoard call. Each returns a NEW messages list.

SAFETY PRIORS (from TokenSaver RULER certification + ARO live findings):
  - RECENCY window: CATASTROPHIC (acc 0.88->0.16). Included ONLY as a negative control
    that the kill-switch MUST catch. Never ship.
  - Aggressive context DELETION mutates agent control flow -> can raise tokens AND drop
    resolution. So the promising arms are LOSSLESS / REFERENCE-PRESERVING:
    dedup identical observations, elide stale file-reads superseded by a later read/edit,
    bound oversized tool outputs (head+tail), collapse successful build/env logs.
  - Anthropic "context editing" (clear old tool results) is an industry-shipped pattern -> M7.

Every transform preserves message ROLES and ORDER; it only shrinks `content` of prior
TOOL-RESULT (user) turns or replaces a duplicated observation with a short pointer.
NEVER touches: the system prompt, the task/PR statement (first user msg), or assistant turns.
"""
from __future__ import annotations
import hashlib, re, copy
from typing import Any

def _block_text(b):
    if not isinstance(b,dict): return str(b)
    if "text" in b: return b.get("text","") or ""
    if b.get("type")=="tool_result":
        c=b.get("content")
        if isinstance(c,str): return c
        if isinstance(c,list): return "".join(_block_text(x) for x in c)
    return ""
def _txt(content):
    if isinstance(content,str): return content
    if isinstance(content,list):
        return "".join(_block_text(b) for b in content)
    return str(content) if content is not None else ""

def _set_obs_text(msg, new):
    """Write `new` into the observation text — the tool_result block if present, else top-level."""
    c=msg.get("content")
    if isinstance(c,list):
        for b in c:
            if isinstance(b,dict) and b.get("type")=="tool_result":
                inner=b.get("content")
                if isinstance(inner,list):
                    b["content"]=[{"type":"text","text":new}]
                else:
                    b["content"]=new
                return msg
        # no tool_result: replace first text block
        for b in c:
            if isinstance(b,dict) and "text" in b:
                b["text"]=new; return msg
    msg["content"]=new
    return msg

def _set_txt(msg, new):
    return _set_obs_text(msg,new)
    # legacy:
    c=msg.get("content")
    if isinstance(c,list):
        # replace the first text block, keep tool_result wrappers/ids
        done=False; out=[]
        for b in c:
            if isinstance(b,dict) and "text" in b and not done:
                b=dict(b); b["text"]=new; done=True
            elif isinstance(b,dict) and b.get("type")=="tool_result" and not done:
                b=dict(b)
                if isinstance(b.get("content"),str): b["content"]=new
                elif isinstance(b.get("content"),list):
                    b["content"]=[{"type":"text","text":new}]
                done=True
            out.append(b)
        if not done and out and isinstance(out[-1],dict): pass
        msg["content"]=out
    else:
        msg["content"]=new
    return msg

def _sha(s): return hashlib.sha256(s.encode("utf-8","replace")).hexdigest()[:12]

# which messages are "observations" we may shrink: user turns that are tool results / outputs,
# EXCLUDING the first user message (the task statement).
def _is_obs(i, m, n):
    if m.get("role")!="user": return False
    if i<=1: return False   # task statement protected
    c=m.get("content")
    if isinstance(c,list) and any(isinstance(b,dict) and b.get("type")=="tool_result" for b in c):
        return True
    return isinstance(c,str)  # fallback for plain-text obs layouts

def identity(messages):
    return messages

def dedup_exact_obs(messages):
    """M1: replace an observation whose text exactly repeats an earlier observation
    with a short pointer. Lossless: the content is still recoverable by reference."""
    out=copy.deepcopy(messages); seen={}
    n=len(out)
    for i,m in enumerate(out):
        if not _is_obs(i,m,n): continue
        t=_txt(m.get("content"))
        if len(t)<200: continue
        h=_sha(t)
        if h in seen:
            _set_txt(m, f"[identical to the observation at step {seen[h]}]")
        else:
            seen[h]=i
    return out

def obs_cap(messages, cap):
    """M3/M4: bound any single observation to `cap` chars, keeping HEAD+TAIL
    (the informative ends) with a marker. SWE-agent already truncates at 100k;
    this is a tighter bound."""
    out=copy.deepcopy(messages); n=len(out)
    head=int(cap*0.6); tail=cap-head
    for i,m in enumerate(out):
        if not _is_obs(i,m,n): continue
        t=_txt(m.get("content"))
        if len(t)>cap:
            _set_txt(m, t[:head]+f"\n…[{len(t)-cap} chars elided; head+tail kept]…\n"+t[-tail:])
    return out

def stale_read_elide(messages):
    """M2: if an observation is a file READ whose path is later read again or edited,
    elide the earlier (stale) view — the agent has a fresher one. Keeps the LAST view."""
    out=copy.deepcopy(messages); n=len(out)
    # find file path mentioned per obs (best-effort from preceding assistant action text)
    paths=[None]*n
    pat=re.compile(r"(?:cat|open|view|sed -n|head|tail|str_replace_editor[^\n]*?)\s+([/\w.\-]+\.\w{1,6})")
    for i,m in enumerate(out):
        prev=_txt(out[i-1].get("content")) if i>0 else ""
        mm=pat.search(prev)
        if mm and _is_obs(i,m,n): paths[i]=mm.group(1)
    # last index each path appears
    last={}
    for i,p in enumerate(paths):
        if p: last[p]=i
    for i,m in enumerate(out):
        p=paths[i]
        if p and last.get(p,i)>i:  # a later view exists
            t=_txt(m.get("content"))
            if len(t)>200:
                _set_txt(m, f"[stale view of {p}; superseded by a later read/edit at step {last[p]}]")
    return out

def search_result_head(messages, k=20):
    """M5: for a search/grep observation with many result lines, keep first k lines + a count."""
    out=copy.deepcopy(messages); n=len(out)
    for i,m in enumerate(out):
        if not _is_obs(i,m,n): continue
        prev=_txt(out[i-1].get("content")) if i>0 else ""
        if not re.search(r"\b(grep|rg|find|search|ag|git grep)\b", prev): continue
        t=_txt(m.get("content")); lines=t.splitlines()
        if len(lines)>k+5:
            _set_txt(m, "\n".join(lines[:k])+f"\n…[{len(lines)-k} more result lines elided]")
    return out

def env_log_collapse(messages):
    """M6: collapse a successful build/install/env observation (no error markers,
    returncode 0-ish) to a one-line summary. Failed builds kept verbatim."""
    out=copy.deepcopy(messages); n=len(out)
    for i,m in enumerate(out):
        if not _is_obs(i,m,n): continue
        prev=_txt(out[i-1].get("content")) if i>0 else ""
        if not re.search(r"(pip install|setup\.py|build_ext|make\b|conda |apt-get|cmake)", prev): continue
        t=_txt(m.get("content"))
        if len(t)<400: continue
        low=t.lower()
        if any(e in low for e in ("error","traceback","failed","fatal","exit code 1","returncode>0")):
            continue  # keep failures
        _set_txt(m, f"[build/env step succeeded; {len(t)} chars of log elided]")
    return out

def old_tool_obs_elide(messages, keep_recent_actions=8):
    """M7: Anthropic context-editing pattern — clear tool observations older than the
    last `keep_recent_actions` agent actions, UNLESS the file is touched again later.
    Conservative: only elides genuinely old + non-referenced observations."""
    out=copy.deepcopy(messages); n=len(out)
    # index observations
    obs_idx=[i for i,m in enumerate(out) if _is_obs(i,m,n)]
    cutoff = obs_idx[-keep_recent_actions] if len(obs_idx)>keep_recent_actions else (obs_idx[0] if obs_idx else n)
    for i in obs_idx:
        if i>=cutoff: continue
        t=_txt(out[i].get("content"))
        if len(t)>300:
            _set_txt(out[i], f"[earlier tool observation cleared (context editing); {len(t)} chars]")
    return out

def recency_window(messages, window=6):
    """C_NEG: NEGATIVE CONTROL. Keep system + task + only the last `window` turns;
    replace all middle turns with a stub. TokenSaver proved this destroys accuracy
    (0.88->0.16). The kill-switch MUST flag this. NEVER SHIP."""
    out=copy.deepcopy(messages); n=len(out)
    if n<=window+2: return out
    protect_head=2  # system + task
    keep_tail=set(range(n-window,n))
    new=[]
    elided=0
    for i,m in enumerate(out):
        if i<protect_head or i in keep_tail:
            new.append(m)
        else:
            if m.get("role")=="user":
                new.append({"role":"user","content":"[earlier turn dropped by recency window]"})
            else:
                new.append(m)  # keep assistant actions (dropping them breaks tool pairing)
            elided+=1
    return new


def recency_keep_task(messages, window=12):
    """AGG1: keep system + task + last `window` user/assistant PAIRS; elide middle observations
    (replace with "[earlier observation cleared]") but keep ALL assistant turns (preserves tool-call
    pairing). Less extreme than CNEG which drops entire turns."""
    import copy
    out=copy.deepcopy(messages); n=len(out)
    protect_head=2
    # find observation indices (user w/ tool_result)
    obs_idx=[i for i,m in enumerate(out) if _is_obs(i,m,n)]
    if len(obs_idx)<=window: return out
    cutoff_idx=obs_idx[-window]
    for i in obs_idx:
        if i>=cutoff_idx: continue
        t=_txt(out[i].get("content"))
        if len(t)>200:
            _set_obs_text(out[i], f"[earlier observation cleared; {len(t)} chars]")
    return out

def recency_keep_task_8(messages):
    """AGG2: same as AGG1 but window=8 (more aggressive)."""
    return recency_keep_task(messages, window=8)

def recency_keep_task_4(messages):
    """AGG3: window=4 (very aggressive, likely regresses some)."""
    return recency_keep_task(messages, window=4)

def m7_plus_cap5k(messages):
    """COMBO1: M7 (old-obs-elide) + M4 (obs-cap-5k) — compound safe methods."""
    return obs_cap(old_tool_obs_elide(messages), 5000)

def m7_plus_dedup(messages):
    """COMBO2: M7 (old-obs-elide) + M1 (dedup exact obs) — compound."""
    return dedup_exact_obs(old_tool_obs_elide(messages))



def summarize_old_obs(messages, keep_recent=6):
    """SUM1: for observations older than last `keep_recent` actions, replace long content with
    a 1-line summary (first 100 chars + last 50 chars + char count). Preserves SOME info vs full elide."""
    import copy
    out=copy.deepcopy(messages); n=len(out)
    obs_idx=[i for i,m in enumerate(out) if _is_obs(i,m,n)]
    cutoff=obs_idx[-keep_recent] if len(obs_idx)>keep_recent else (obs_idx[0] if obs_idx else n)
    for i in obs_idx:
        if i>=cutoff: continue
        t=_txt(out[i].get("content"))
        if len(t)>300:
            summary=t[:100]+"..."+t[-50:]+f" [{len(t)} chars total]"
            _set_obs_text(out[i], summary)
    return out

def tool_result_compress(messages):
    """COMP1: for ALL tool_result observations, if >2000 chars, keep first 1000 + last 500 + count.
    Less aggressive than M4(5k) but applies to ALL observations not just oversized ones."""
    import copy
    out=copy.deepcopy(messages); n=len(out)
    for i,m in enumerate(out):
        if not _is_obs(i,m,n): continue
        t=_txt(m.get("content"))
        if len(t)>2000:
            _set_obs_text(out[i], t[:1000]+"\n...["+str(len(t)-1500)+" chars compressed]...\n"+t[-500:])
    return out

def hybrid_m7_agg2(messages):
    """HYBRID1: M7 for VERY old observations (>12 steps) + AGG2-style obs-clear for medium-old (8-12).
    Graduated: recent=full, medium=summarized, old=cleared."""
    import copy
    out=copy.deepcopy(messages); n=len(out)
    obs_idx=[i for i,m in enumerate(out) if _is_obs(i,m,n)]
    if len(obs_idx)<=12: return out
    recent_cut=obs_idx[-8]; medium_cut=obs_idx[-12]
    for i in obs_idx:
        if i>=recent_cut: continue  # keep recent
        t=_txt(out[i].get("content"))
        if len(t)<=200: continue
        if i<medium_cut:  # very old -> full clear
            _set_obs_text(out[i], f"[old observation cleared; {len(t)} chars]")
        else:  # medium -> summarize (first 100 + last 50)
            _set_obs_text(out[i], t[:100]+"..."+t[-50:]+f" [{len(t)}c]")
    return out

def dedup_similar_obs(messages, threshold=0.9):
    """DEDUP2: if an observation is >90% character-overlap with a previous one (not just exact),
    replace with pointer. Catches near-duplicates (same file, minor diff)."""
    import copy
    out=copy.deepcopy(messages); n=len(out)
    seen=[]  # (index, text) of prior observations
    for i,m in enumerate(out):
        if not _is_obs(i,m,n): continue
        t=_txt(m.get("content"))
        if len(t)<200: continue
        # check overlap with any prior
        for pi,pt in seen:
            if abs(len(t)-len(pt))>len(t)*0.15: continue  # length too different
            # character-level overlap (cheap: shared prefix + suffix / total)
            common=0
            for ci in range(min(len(t),len(pt))):
                if t[ci]==pt[ci]: common+=1
                else: break
            for ci in range(1,min(len(t),len(pt))//2):
                if t[-ci]==pt[-ci]: common+=1
                else: break
            if common/max(len(t),1)>threshold:
                _set_obs_text(out[i], f"[~identical to observation at step {pi}; {len(t)} chars]")
                break
        else:
            seen.append((i,t))
    return out

def progressive_compression(messages):
    """PROG1: compress more as history grows. Recent 4 obs = full; next 4 = head+tail 2k;
    next 4 = head+tail 500; older = 1-line summary. Mirrors how a human reads context."""
    import copy
    out=copy.deepcopy(messages); n=len(out)
    obs_idx=[i for i,m in enumerate(out) if _is_obs(i,m,n)]
    total=len(obs_idx)
    for ri,i in enumerate(reversed(obs_idx)):  # ri=0 is most recent
        t=_txt(out[i].get("content"))
        if len(t)<=200: continue
        if ri<4: continue  # keep recent 4 full
        elif ri<8: # moderate compression
            if len(t)>2000:
                _set_obs_text(out[i], t[:1000]+"\n...[compressed]...\n"+t[-500:])
        elif ri<12: # heavier
            if len(t)>500:
                _set_obs_text(out[i], t[:250]+"...["+str(len(t))+"c]..."+t[-100:])
        else: # old -> 1-line
            _set_obs_text(out[i], t[:80]+"... ["+str(len(t))+"c total, old]")
    return out



def recency_brutal_2(messages):
    """BRUTAL1: keep system + task + only last 2 observation turns. Everything else = 1-line stub.
    WILL regress — tests how much saving you get for a known regression cost."""
    return recency_keep_task(messages, window=2)

def recency_brutal_1(messages):
    """BRUTAL2: keep only the LAST observation. Maximum aggression. High regression expected."""
    return recency_keep_task(messages, window=1)

def nuke_all_obs(messages):
    """NUKE: replace ALL observations with "[observation cleared]". Pure pathological control —
    the agent flies blind after every action. Establishes the MAXIMUM possible saving."""
    import copy
    out = copy.deepcopy(messages); n = len(out)
    for i, m in enumerate(out):
        if _is_obs(i, m, n):
            t = _txt(m.get("content"))
            if len(t) > 50:
                _set_obs_text(out[i], "[observation cleared]")
    return out

def keep_errors_only(messages):
    """ERR_ONLY: clear ALL observations EXCEPT those containing error/traceback markers.
    Hypothesis: the agent only truly needs error feedback; success confirmations are redundant."""
    import copy
    out = copy.deepcopy(messages); n = len(out)
    error_markers = ("error", "traceback", "failed", "exception", "fatal", "no such file", "permission denied")
    for i, m in enumerate(out):
        if not _is_obs(i, m, n): continue
        t = _txt(m.get("content")).lower()
        if not any(e in t for e in error_markers):
            if len(_txt(m.get("content"))) > 200:
                _set_obs_text(out[i], "[success observation cleared; errors preserved]")
    return out

def summarize_all_obs(messages):
    """SUM_ALL: every observation > 500 chars → first 150 + last 80 chars + count. Applies to ALL
    observations (not just old ones like SUM1). Aggressive but preserves some signal."""
    import copy
    out = copy.deepcopy(messages); n = len(out)
    for i, m in enumerate(out):
        if not _is_obs(i, m, n): continue
        t = _txt(m.get("content"))
        if len(t) > 500:
            _set_obs_text(out[i], t[:150] + "..." + t[-80:] + f" [{len(t)}c]")
    return out

def half_context(messages):
    """HALF: keep only the SECOND HALF of all observations (drop the first half of each).
    Tests whether the agent mostly needs the END of tool output (where results/errors are)."""
    import copy
    out = copy.deepcopy(messages); n = len(out)
    for i, m in enumerate(out):
        if not _is_obs(i, m, n): continue
        t = _txt(m.get("content"))
        if len(t) > 400:
            _set_obs_text(out[i], t[len(t)//2:])
    return out

METHODS={
 "C0_identity": identity,
 "M1_dedup_exact": dedup_exact_obs,
 "M2_stale_read_elide": stale_read_elide,
 "M3_obs_cap_10k": lambda m: obs_cap(m,10000),
 "M4_obs_cap_5k": lambda m: obs_cap(m,5000),
 "M5_search_head": search_result_head,
 "M6_env_log_collapse": env_log_collapse,
 "M7_old_obs_elide": old_tool_obs_elide,
 "CNEG_recency": recency_window,
 "AGG1_recency_obs_12": recency_keep_task,
 "AGG2_recency_obs_8": recency_keep_task_8,
 "AGG3_recency_obs_4": recency_keep_task_4,
 "COMBO1_m7_cap5k": m7_plus_cap5k,
 "COMBO2_m7_dedup": m7_plus_dedup,
 "SUM1_summarize_old": summarize_old_obs,
 "COMP1_tool_compress": tool_result_compress,
 "HYBRID1_m7_agg2": hybrid_m7_agg2,
 "DEDUP2_similar_obs": dedup_similar_obs,
 "PROG1_progressive": progressive_compression,
 "BRUTAL1_window_2": recency_brutal_2,
 "BRUTAL2_window_1": recency_brutal_1,
 "NUKE_all_obs": nuke_all_obs,
 "ERR_ONLY_keep_errors": keep_errors_only,
 "SUM_ALL_summarize": summarize_all_obs,
 "HALF_context": half_context,
}

def apply_method(method, messages):
    fn=METHODS.get(method)
    if fn is None: return messages
    try:
        return fn(messages)
    except Exception:
        return messages  # never break the agent on a prune bug

if __name__=="__main__":
    import json,sys
    # self-test on a synthetic messages array
    msgs=[{"role":"system","content":"sys"},{"role":"user","content":"TASK: fix bug"},
          {"role":"assistant","content":"cat /testbed/a.py"},{"role":"user","content":"X"*5000},
          {"role":"assistant","content":"cat /testbed/a.py"},{"role":"user","content":"X"*5000},
          {"role":"assistant","content":"grep foo"},{"role":"user","content":"\n".join(f"hit{i}" for i in range(60))}]
    for name in METHODS:
        out=apply_method(name,msgs)
        before=sum(len(_txt(m.get('content'))) for m in msgs)
        after=sum(len(_txt(m.get('content'))) for m in out)
        print(f"{name:22s} chars {before}->{after} ({100*(before-after)//max(before,1)}% cut) msgs {len(msgs)}->{len(out)}")
