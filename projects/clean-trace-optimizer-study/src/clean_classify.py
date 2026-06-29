#!/usr/bin/env python3
"""clean_classify.py — INDEPENDENT clean-room action classifier.

Maps a raw action string (from the ALLOWED normalize_traces loader) to a small
set of canonical clean-room action classes, using ONLY observable surface form.
This is written from scratch for the clean lane; it does not import or reuse the
existing taxonomy's classifier or thresholds.

Classes: SEARCH, READ, EDIT, TEST, EXEC_OTHER, ENV, SUBMIT, OTHER
Returns (cls, evidence_str).
"""
from __future__ import annotations
import re
from typing import Optional, Tuple

# OpenHands / structured tool names (solver_G/H) come through as tool_name.
_TOOLNAME = {
    "str_replace_editor": "EDITOR_TOOL",   # could be view OR edit; resolve via args
    "file_editor": "EDITOR_TOOL",
    "execute_bash": "BASH",
    "execute_ipython_cell": "BASH",
    "finish": "SUBMIT",
}

# SWE-agent native ACI verbs (leading token).
_NATIVE = {
    "create": "EDIT", "edit": "EDIT", "insert": "EDIT", "append": "EDIT",
    "str_replace": "EDIT", "submit": "SUBMIT", "exit": "SUBMIT",
    "exit_forfeit": "SUBMIT", "exit_cost": "SUBMIT", "exit_command_timeout": "SUBMIT",
    "open": "READ", "goto": "READ", "scroll_up": "READ", "scroll_down": "READ", "scroll": "READ",
    "search_file": "SEARCH", "search_dir": "SEARCH", "find_file": "SEARCH",
}

_RE_TEST  = re.compile(r"\b(pytest|tox|py\.test|nosetests|unittest|run_tests?|python -m pytest|python -m unittest)\b", re.I)
_RE_ENV   = re.compile(r"(pip install|pip3 install|conda install|conda create|apt-get|python setup\.py|setup\.py (install|build|develop)|make install|\bmake\b|cmake|\./configure|build_ext|export [A-Z_]+=|virtualenv|\bpoetry (install|add)\b)", re.I)
_RE_SEARCH= re.compile(r"\b(grep|rg|ag|git grep|ack|egrep|fgrep|locate)\b|(?<![\w-])find\b", re.I)
_RE_WRITE = re.compile(r"(<<\s*['\"]?[A-Za-z_]+|cat\s*>|\btee\b|\bsed -i\b|>>?\s*[\w./-]+\.\w{1,6}\b)")
_RE_READ  = re.compile(r"^\s*(cat|head|tail|less|more|view|nl|sed -n|wc\b|ls\b|tree\b)", re.I)
_RE_GITDIFF = re.compile(r"\b(git diff|git apply|git status|git log|patch -p)\b", re.I)

def classify(raw_action_type: Optional[str], tool_name: Optional[str],
             args_text: Optional[str] = None) -> Tuple[str, str]:
    """Surface-only classification. args_text = best-effort raw args (may be the
    raw_action_type tail). Returns (class, short_evidence)."""
    rat = (raw_action_type or "").strip()
    tn  = (tool_name or "").strip().lower()
    text = (args_text or rat or "")

    # 1) structured tool name (OpenHands)
    if tn in _TOOLNAME:
        kind = _TOOLNAME[tn]
        if kind == "SUBMIT": return "SUBMIT", f"tool={tn}"
        if kind == "EDITOR_TOOL":
            # view vs edit: look for a 'command' field or 'view'/'str_replace'/'create'
            low = text.lower()
            if re.search(r"\b(view|read)\b", low) and not re.search(r"\b(str_replace|create|insert|write|edit|old_str|new_str)\b", low):
                return "READ", f"tool={tn}/view"
            if re.search(r"\b(str_replace|create|insert|write|edit|old_str|new_str)\b", low):
                return "EDIT", f"tool={tn}/edit"
            return "READ", f"tool={tn}/ambiguous->read"  # conservative: viewing dominates editor calls
        if kind == "BASH":
            # fall through to command-content classification on the bash payload
            text = text or rat
            rat = text

    # 2) SWE-agent native verb on the leading token
    lead = rat.split()[0].lower() if rat.split() else ""
    if lead in _NATIVE:
        return _NATIVE[lead], f"native:{lead}"

    # 2b) editor ACI as a raw string: "str_replace_editor <subcmd> ..." / "file_editor <subcmd> ..."
    #     (SWE-agent-1.0 / SWE-agent-LM emit the editor tool + subcommand as one action string)
    if lead in ("str_replace_editor", "file_editor", "edit_file"):
        sub = (rat.split()[1].lower() if len(rat.split()) > 1 else "")
        if sub in ("view", "open", "read"):
            return "READ", f"editor:{sub}"
        if sub in ("str_replace", "create", "insert", "append", "write", "edit"):
            return "EDIT", f"editor:{sub}"
        # unknown editor subcmd: treat as READ (viewing is the safe default; editor calls w/o
        # explicit write keyword are usually navigation)
        return "READ", f"editor:ambiguous->read"

    # 3) command-content precedence (write-to-file BEFORE test/env, since heredoc edits look like exec)
    if _RE_TEST.search(text):
        # a test invocation, even if it also writes — TEST wins for verification semantics
        return "TEST", "re:test"
    if _RE_WRITE.search(text):
        return "EDIT", "re:write"
    if _RE_ENV.search(text):
        return "ENV", "re:env"
    if _RE_SEARCH.search(text):
        return "SEARCH", "re:search"
    if _RE_READ.search(text):
        return "READ", "re:read"
    if _RE_GITDIFF.search(text):
        return "EXEC_OTHER", "re:gitdiff"
    if not rat:
        return "OTHER", "empty"
    return "EXEC_OTHER", "fallthrough"
