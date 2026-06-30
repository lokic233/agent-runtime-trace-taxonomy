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


# ============================================================================
# CACHE-STABLE PRUNING FAMILY (content-based, position-independent)
# Principle: each observation's pruned form depends ONLY on its own content,
# so it is byte-identical across every step -> the prompt prefix stays stable
# -> Anthropic prompt cache (cache_read 0.1x) is PRESERVED, not busted.
# This is the opposite of recency methods (HYBRID1/AGG3/M7) which re-prune by
# position every step and destroy the cache (cache_creation 1.25x).
# ============================================================================

def cap_all_obs(messages, cap_chars):
    """CAP: every observation > cap_chars -> head(0.6*cap) + "...[N chars elided]..." + tail(0.4*cap).
    Content-stable: same obs always yields the same capped text regardless of position."""
    import copy
    out=copy.deepcopy(messages); n=len(out)
    for i,m in enumerate(out):
        if not _is_obs(i,m,n): continue
        t=_txt(m.get("content"))
        if len(t)>cap_chars:
            head=int(cap_chars*0.6); tail=cap_chars-head
            _set_obs_text(out[i], t[:head]+f"\n...[{len(t)-cap_chars} chars elided]...\n"+t[-tail:])
    return out

def cap_2k(messages):  return cap_all_obs(messages, 2000)
def cap_1k(messages):  return cap_all_obs(messages, 1000)
def cap_800(messages): return cap_all_obs(messages, 800)
def cap_500(messages): return cap_all_obs(messages, 500)

def smart_obs_compact(messages):
    """SMART: content-stable, structure-aware compaction of each observation.
    - keep error/traceback lines (high signal)
    - collapse repeated/whitespace-heavy blocks
    - cap very long file dumps to head+tail
    Position-independent -> cache-stable. Aggressive but signal-preserving."""
    import copy, re
    out=copy.deepcopy(messages); n=len(out)
    err_markers=("error","traceback","exception","failed","assert","fatal"," E ","FAILED","Error")
    for i,m in enumerate(out):
        if not _is_obs(i,m,n): continue
        t=_txt(m.get("content"))
        if len(t)<=600: continue
        lines=t.split("\n")
        if len(lines)<=12:
            # single block: head+tail cap
            if len(t)>1200:
                _set_obs_text(out[i], t[:700]+f"\n...[{len(t)-1000} elided]...\n"+t[-300:])
            continue
        # multi-line: keep error lines + head + tail, drop the bland middle
        err_lines=[l for l in lines if any(e in l for e in err_markers)]
        head=lines[:6]; tail=lines[-4:]
        kept=head + (["...[middle elided]..."] if len(lines)>10 else []) + err_lines[:8] + tail
        new="\n".join(kept)
        if len(new)<len(t):
            _set_obs_text(out[i], new)
    return out

def dedup_content_stable(messages):
    """DEDUP-STABLE: if an observation's content has appeared VERBATIM in an EARLIER observation,
    replace with a short pointer. Pointer text depends only on the (stable) earlier hash -> cache-stable.
    (Unlike recency dedup, the pointer is deterministic from content.)"""
    import copy
    out=copy.deepcopy(messages); n=len(out); seen={}
    for i,m in enumerate(out):
        if not _is_obs(i,m,n): continue
        t=_txt(m.get("content"))
        if len(t)<200: continue
        h=_sha(t)
        if h in seen:
            _set_obs_text(out[i], f"[identical to earlier observation #{seen[h]}; {len(t)} chars]")
        else:
            seen[h]=i
    return out

def combo_cap_dedup(messages):
    """COMBO-STABLE: dedup verbatim repeats, THEN cap survivors at 1k. Both content-stable."""
    return cap_all_obs(dedup_content_stable(messages), 1000)

def combo_smart_cap(messages):
    """COMBO-SMART: structure-aware compact, then hard cap at 1.2k. Content-stable."""
    return cap_all_obs(smart_obs_compact(messages), 1200)


# register cache-stable family (functions defined above, after METHODS dict)
METHODS["CAP2K_stable"]=cap_2k
METHODS["CAP1K_stable"]=cap_1k
METHODS["CAP800_stable"]=cap_800
METHODS["CAP500_stable"]=cap_500
METHODS["SMART_stable"]=smart_obs_compact
METHODS["DEDUPS_stable"]=dedup_content_stable
METHODS["COMBOCD_stable"]=combo_cap_dedup
METHODS["COMBOSC_stable"]=combo_smart_cap


def cap_4k_gentle(messages):
    """GENTLE4K: cap only observations >4000 chars (the rare large dumps). Content-stable.
    Cuts ~7% of tokens with minimal info loss -> minimal trajectory drift. The M4-regime done right."""
    return cap_all_obs(messages, 4000)

def cap_6k_gentle(messages):
    """GENTLE6K: cap only observations >6000 chars (extreme dumps only). Content-stable. ~3% cut."""
    return cap_all_obs(messages, 6000)

def smart_gentle(messages):
    """SMARTGENTLE: structure-aware compaction but ONLY on observations >3000 chars, keeping all
    error lines + generous head/tail. Content-stable. Targets verbose dumps, spares normal obs."""
    import copy
    out=copy.deepcopy(messages); n=len(out)
    err=("error","traceback","exception","failed","assert","fatal","Error","FAILED")
    for i,m in enumerate(out):
        if not _is_obs(i,m,n): continue
        t=_txt(m.get("content"))
        if len(t)<=3000: continue  # spare normal-sized obs entirely
        lines=t.split("\n")
        if len(lines)<=20:
            _set_obs_text(out[i], t[:1800]+f"\n...[{len(t)-2400} elided]...\n"+t[-600:]); continue
        errl=[l for l in lines if any(e in l for e in err)]
        kept=lines[:12]+(["...[middle elided]..."])+errl[:10]+lines[-6:]
        nt="\n".join(kept)
        if len(nt)<len(t): _set_obs_text(out[i], nt)
    return out

METHODS["GENTLE4K_stable"]=cap_4k_gentle
METHODS["GENTLE6K_stable"]=cap_6k_gentle
METHODS["SMARTGENTLE_stable"]=smart_gentle


# ============================================================================
# EXPERIMENT 4: RETRIEVAL-AWARE + LINE-LEVEL cache-stable pruning
# Grounded in SWE-Pruner (line-level, keep whole relevant lines -> no syntax break)
# + Headroom/tokensave (retrievable refs -> info deferred not lost -> less drift)
# + our cache finding (content-based -> cache-stable). Regression-ALLOW framing.
# ============================================================================

def line_level_dedup(messages):
    """LINEDEDUP: within each observation, drop LINES that appeared verbatim in an EARLIER
    observation (cross-obs line dedup). Keeps whole lines (syntax intact, SWE-Pruner style).
    Content-stable: a line's keep/drop depends only on whether its exact text was seen before.
    Drift-safe: deduped lines were already shown, so no NEW info is lost."""
    import copy
    out=copy.deepcopy(messages); n=len(out)
    seen_lines=set()
    for i,m in enumerate(out):
        if not _is_obs(i,m,n):
            # still register assistant/non-obs lines as 'seen' for dedup reference
            continue
        t=_txt(m.get("content"))
        if len(t)<300: 
            for ln in t.split("\n"): seen_lines.add(ln.strip())
            continue
        kept=[]; dropped=0
        for ln in t.split("\n"):
            key=ln.strip()
            if len(key)>=12 and key in seen_lines:
                dropped+=1
            else:
                kept.append(ln); seen_lines.add(key)
        if dropped>3:
            new="\n".join(kept)+f"\n[{dropped} duplicate lines elided]"
            _set_obs_text(out[i], new)
    return out

def blank_line_squeeze(messages):
    """SQUEEZE: collapse runs of blank lines + trailing whitespace in observations. LOSSLESS.
    Content-stable, zero info loss -> zero drift. The 'free' baseline win."""
    import copy, re
    out=copy.deepcopy(messages); n=len(out)
    for i,m in enumerate(out):
        if not _is_obs(i,m,n): continue
        t=_txt(m.get("content"))
        if len(t)<200: continue
        sq=re.sub(r'[ \t]+\n','\n',t)        # trailing whitespace
        sq=re.sub(r'\n{3,}','\n\n',sq)        # 3+ blank lines -> 1
        if len(sq)<len(t): _set_obs_text(out[i], sq)
    return out

def retrieval_ref_large(messages):
    """RETRIEVREF: replace observations >5k chars with a STRUCTURED retrievable summary:
    keep first 30 + last 15 lines + a line-count header so the agent knows it can re-read.
    Content-stable (depends only on the obs). Mimics Headroom: 'if you need it, re-read the file'.
    Regression-ALLOW: large dumps rarely need full body; the ref tells the agent what/where."""
    import copy
    out=copy.deepcopy(messages); n=len(out)
    for i,m in enumerate(out):
        if not _is_obs(i,m,n): continue
        t=_txt(m.get("content"))
        if len(t)<=5000: continue
        lines=t.split("\n")
        if len(lines)<50: 
            _set_obs_text(out[i], t[:3000]+f"\n[... {len(t)-3500} chars elided; re-run the command to see full output ...]\n"+t[-500:])
            continue
        head="\n".join(lines[:30]); tail="\n".join(lines[-15:])
        _set_obs_text(out[i], f"{head}\n[... {len(lines)-45} lines elided ({len(t)} chars total); re-read file/re-run to see full ...]\n{tail}")
    return out

def keep_signal_lines(messages):
    """SIGNAL: line-level skim (SWE-Pruner style). In observations >2k chars, keep only HIGH-SIGNAL
    lines: errors/tracebacks, def/class/import, file paths, diffs (+/-), assertions, line-number refs.
    Drop bland prose/separators. Keeps WHOLE lines (syntax intact). Content-stable. Regression-ALLOW."""
    import copy, re
    out=copy.deepcopy(messages); n=len(out)
    sig=re.compile(r'(error|traceback|exception|fail|assert|def |class |import |return |raise |^\+|^-|\.py[:\"]|line \d+|=== |\bE\b|warning|FAILED|PASSED|\bdef\b)', re.I)
    for i,m in enumerate(out):
        if not _is_obs(i,m,n): continue
        t=_txt(m.get("content"))
        if len(t)<=2000: continue
        lines=t.split("\n")
        if len(lines)<20: continue
        kept=[]; run_drop=0
        for ln in lines:
            if sig.search(ln) or len(ln.strip())==0 and run_drop==0:
                kept.append(ln); run_drop=0
            else:
                run_drop+=1
                if run_drop==1: kept.append("  ...")
        new="\n".join(kept)
        if len(new)<len(t)*0.85: _set_obs_text(out[i], new)
    return out

def combo_squeeze_signal(messages):
    """COMBO-SS: lossless squeeze + signal-line skim on large obs. Stacks the two safest wins."""
    return keep_signal_lines(blank_line_squeeze(messages))

METHODS["LINEDEDUP_e4"]=line_level_dedup
METHODS["SQUEEZE_e4"]=blank_line_squeeze
METHODS["RETRIEVREF_e4"]=retrieval_ref_large
METHODS["SIGNAL_e4"]=keep_signal_lines
METHODS["COMBOSS_e4"]=combo_squeeze_signal
