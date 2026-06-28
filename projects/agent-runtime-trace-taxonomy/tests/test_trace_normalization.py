#!/usr/bin/env python3
"""Tests for L0 trace normalization. Run: python3 -m pytest tests/test_trace_normalization.py -q
   (also runnable plainly: python3 tests/test_trace_normalization.py)"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.normalize_traces import (classify_command as C, normalize_trace, detect_layout,
                                   NORM_TYPES, _split_mini_action, _extract_paths)

def test_classifier_precedence():
    assert C("find /testbed -name '*.py'") == "SEARCH"
    assert C("grep -r foo /x") == "SEARCH"
    assert C("cat <<EOF > /testbed/edit_file.py") == "EDIT"      # write, not exec
    assert C("cat <<EOF > /testbed/test_x.py") == "EDIT"          # writing a test file == EDIT
    assert C("create reproduce.py") == "EDIT"                     # SWE-agent native
    assert C("edit 1:5") == "EDIT"
    assert C("open astropy/x.py") == "READ"
    assert C("python setup.py build_ext --inplace") == "ENVIRONMENT"
    assert C("pip install cython") == "ENVIRONMENT"
    assert C("python -m pytest tests/") == "TEST"
    assert C("python reproduce.py") == "EXECUTE"
    assert C("submit") == "FINISH"
    assert C("git apply p.diff") == "PATCH_APPLY"
    assert C("cat foo.py") == "READ"
    assert C("python /x/edit_file.py view 1 50") == "EXECUTE"     # 'view' mid-cmd != READ
    assert C(None, thought="let me think") == "PLAN"
    assert C(None) == "OTHER"

def test_honest_nulls():
    """Absent fields must be null, never 0. (Section 5 + TokenSaver contract.)"""
    raw = {"trajectory": [{"action": "grep foo", "observation": "x", "thought": None, "state": {}}],
           "info": {"exit_status": "submitted", "submission": "diff"}}
    nt = normalize_trace(raw, trace_id="t@solver_A", task_id="t", solver_alias="solver_A")
    e = nt["events"][0]
    assert e["input_tokens"] is None        # NOT 0
    assert e["output_tokens"] is None
    assert e["context_tokens"] is None
    assert e["test_result"] is None         # not a test step
    assert e["content_available"] is True

def test_blinding_no_model_name():
    """solver_alias must be the ONLY identity; no real model name leaks into events."""
    raw = {"trajectory": [{"action": "grep x", "observation": "y"}], "info": {}}
    nt = normalize_trace(raw, trace_id="t@solver_E", task_id="t", solver_alias="solver_E")
    blob = json.dumps(nt).lower()
    for banned in ("claude","qwen","opus","sonnet","gpt","gemini","anthropic"):
        assert banned not in blob, f"model identity leaked: {banned}"
    assert all(e["solver_alias"] == "solver_E" for e in nt["events"])

def test_layout_detection():
    assert detect_layout({"trajectory_format": "mini-swe-agent-1", "messages": []}) == "mini_swe_agent"
    assert detect_layout({"trajectory": [], "history": []}) == "classic_traj"
    assert detect_layout({"messages": []}) == "mini_swe_agent"

def test_mini_action_split():
    th, ac = _split_mini_action("THOUGHT: find the bug\n```bash\ngrep -r foo /x\n```")
    assert "find the bug" in th
    assert ac.strip() == "grep -r foo /x"

def test_event_indices_contiguous():
    raw = {"trajectory": [{"action": f"echo {i}"} for i in range(5)], "info": {}}
    nt = normalize_trace(raw, trace_id="t@solver_A", task_id="t", solver_alias="solver_A")
    assert [e["event_index"] for e in nt["events"]] == [0,1,2,3,4]

def test_all_types_valid():
    raw = {"trajectory": [{"action": a} for a in
           ["grep x","cat f","edit 1:2","pytest","pip install y","python r.py","submit","find ."]], "info": {}}
    nt = normalize_trace(raw, trace_id="t@solver_A", task_id="t", solver_alias="solver_A")
    for e in nt["events"]:
        assert e["normalized_action_type"] in NORM_TYPES

def test_path_extraction():
    p = _extract_paths("editing astropy/table/table.py and ./tests/test_x.py")
    assert "astropy/table/table.py" in p

if __name__ == "__main__":
    fns = [v for k,v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        try:
            fn(); passed += 1; print(f"✅ {fn.__name__}")
        except AssertionError as e:
            print(f"❌ {fn.__name__}: {e}")
    print(f"\n{passed}/{len(fns)} tests passed")
    sys.exit(0 if passed == len(fns) else 1)
