#!/usr/bin/env python3
"""clean_loader.py — INDEPENDENT clean-room raw-trace loader.

Reads the 4 on-disk SWE-agent trajectory layouts and yields a flat list of
STEP dicts with full surface text, so the clean lane never depends on the
existing project's hashed/normalized events.

Each step: {i, action_text, observation_text, thought, raw_tool, source_layout}
Only the agent's *actions* become steps (system/user-context messages are folded
into the preceding step's observation where relevant).
"""
from __future__ import annotations
import json, re
from typing import Any

def _oh_extract_action(content: str):
    """OpenHands: assistant content may embed <function=NAME><parameter=command>...</parameter></function>."""
    if not isinstance(content, str): 
        # content can be a list of blocks
        if isinstance(content, list):
            content = " ".join(str(b.get("text","")) if isinstance(b,dict) else str(b) for b in content)
        else:
            content = str(content)
    m = re.search(r"<function=([a-zA-Z_]+)>(.*?)</function>", content, re.S)
    if not m:
        return None, None, content.strip()  # no action -> pure thought
    tool = m.group(1)
    body = m.group(2)
    # gather all <parameter=..>val</parameter>; prefer command/file_text/path
    params = dict(re.findall(r"<parameter=([a-zA-Z_]+)>(.*?)</parameter>", body, re.S))
    cmd = params.get("command") or params.get("code") or ""
    # for editor: synthesize an action string from the params
    extra = " ".join(f"{k}={v[:60]}" for k,v in params.items() if k not in ("command","code"))
    action_text = (cmd + " " + extra).strip() or tool
    thought = content.split("<function=")[0].strip()
    return tool, action_text, thought

def load_steps(raw: Any) -> list[dict]:
    steps: list[dict] = []
    # ---- classic_traj: dict with trajectory[] of {action,observation,thought} ----
    if isinstance(raw, dict) and isinstance(raw.get("trajectory"), list) and raw["trajectory"] and \
       isinstance(raw["trajectory"][0], dict) and "action" in raw["trajectory"][0]:
        for i, t in enumerate(raw["trajectory"]):
            steps.append({
                "i": i,
                "action_text": str(t.get("action") or "").strip(),
                "observation_text": str(t.get("observation") or "").strip(),
                "thought": str(t.get("thought") or "").strip(),
                "raw_tool": None,
                "source_layout": "classic_traj",
            })
        return steps
    # ---- messages[] layouts (mini-swe-agent B, OpenHands G/H) ----
    msgs = None
    if isinstance(raw, dict) and isinstance(raw.get("messages"), list):
        msgs = raw["messages"]
    elif isinstance(raw, list):
        msgs = raw
    if msgs is not None:
        # is it OpenHands (<function=) or mini (THOUGHT + ```bash```)?
        asst = " ".join(str(m.get("content","")) for m in msgs if isinstance(m,dict) and m.get("role")=="assistant")
        is_oh = "<function=" in asst
        i = 0
        pending_obs = ""
        for m in msgs:
            if not isinstance(m, dict): continue
            role = m.get("role")
            content = m.get("content","")
            if role == "assistant":
                if is_oh:
                    tool, action, thought = _oh_extract_action(content)
                else:
                    # mini-swe-agent: action in ```bash ... ``` fenced block
                    ctext = content if isinstance(content,str) else json.dumps(content)
                    mb = re.search(r"```(?:bash|sh)?\s*(.*?)```", ctext, re.S)
                    action = (mb.group(1).strip() if mb else "")
                    tool = None
                    thought = (ctext.split("```")[0].strip() if mb else ctext.strip())
                steps.append({
                    "i": i, "action_text": action or "", "observation_text": "",
                    "thought": thought or "", "raw_tool": tool, "source_layout": "openhands" if is_oh else "mini",
                })
                i += 1
            elif role in ("user","tool"):
                # observation belongs to the most recent assistant step
                ctext = content if isinstance(content,str) else json.dumps(content)
                if steps:
                    steps[-1]["observation_text"] = (steps[-1]["observation_text"] + "\n" + ctext).strip()[:20000]
        return steps
    return steps

def load_file(path: str) -> list[dict]:
    with open(path) as fh:
        raw = json.load(fh)
    return load_steps(raw)
