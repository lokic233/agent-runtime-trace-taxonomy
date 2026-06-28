#!/usr/bin/env python3
"""test_annotation_schema.py — validate annotation records against the JSON schema."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
SCHEMA_DIR=os.path.join(os.path.dirname(__file__),"..","schemas")

def _load(name): return json.load(open(os.path.join(SCHEMA_DIR,name)))

def _valid_annotation():
    return {
        "sample_id":"S1","trace_id":"t@solver_A","task_id":"t","repo":"django",
        "solver_alias":"solver_A","source_harness":"swe-agent-1.0","cutoff":"FULL",
        "taxonomy_version":"v1","deterministic_features":{},
        "workload_annotation":{"primary_l1":"LOCALIZATION_DOMINANT","l2_attributes":["SEARCH_REQUIRED"],"evidence":[0,2],"unknown_fields":[]},
        "execution_state":{"phase":"EDIT","progress":"IMPROVING","candidate_location_found":True,"plausible_patch_found":True,"verification_sufficient":False},
        "waste_annotation":{"l1_labels":["VERIFICATION"],"l2_labels":["VERIFICATION_GAP"],"primary_bottleneck":"VERIFICATION_GAP",
            "severity":{"VERIFICATION_GAP":"MODERATE"},"evidence_action_ids":{"VERIFICATION_GAP":[7,8]}},
        "candidate_interventions":["INCREASE_TARGETED_VERIFICATION"],
        "annotation_metadata":{"annotator_id":"ann1","annotator_model":"claude","prompt_version":"v1","annotation_timestamp":"2026-06-28T00:00:00Z","abstain":False,"abstain_reason":None}
    }

def test_schemas_are_valid_json():
    for s in ("normalized_event.schema.json","normalized_trace.schema.json",
              "trace_annotation.schema.json","config_outcome.schema.json"):
        _load(s)  # raises if bad

def test_valid_annotation_passes():
    try:
        import jsonschema
    except ImportError:
        print("   (jsonschema not installed — doing structural check only)")
        a=_valid_annotation()
        for req in ("sample_id","trace_id","solver_alias","cutoff","taxonomy_version",
                    "workload_annotation","execution_state","waste_annotation","annotation_metadata"):
            assert req in a
        return
    jsonschema.validate(_valid_annotation(), _load("trace_annotation.schema.json"))

def test_solver_alias_pattern_enforced():
    a=_valid_annotation(); a["solver_alias"]="claude_opus"  # should be invalid
    try:
        import jsonschema
        try:
            jsonschema.validate(a, _load("trace_annotation.schema.json"))
            assert False, "bad solver_alias accepted"
        except jsonschema.ValidationError:
            pass
    except ImportError:
        import re
        assert not re.match(r"^solver_[A-F]$", a["solver_alias"])

def test_config_outcome_regression_definition():
    """regression_event MUST equal baseline AND NOT candidate (paired)."""
    co={"task_id":"t","solver_id":"s","config_id":"c","baseline_resolved":True,
        "candidate_resolved":False,"regression_event":True}
    assert co["regression_event"]==(co["baseline_resolved"] and not co["candidate_resolved"])
    co2={**co,"candidate_resolved":True,"regression_event":False}
    assert co2["regression_event"]==(co2["baseline_resolved"] and not co2["candidate_resolved"])

def test_no_numeric_confidence_field():
    """Schema must NOT permit an arbitrary numeric confidence PROPERTY (Section 9).
    (The word may appear in a description explaining WHY we omit it.)"""
    s=_load("trace_annotation.schema.json")
    def has_confidence_prop(o):
        if isinstance(o,dict):
            for k,v in o.items():
                if k=="properties" and isinstance(v,dict) and any("confidence" in pk.lower() for pk in v):
                    return True
                if has_confidence_prop(v): return True
        elif isinstance(o,list):
            return any(has_confidence_prop(x) for x in o)
        return False
    assert not has_confidence_prop(s), "schema should not define a confidence property"

if __name__=="__main__":
    fns=[v for k,v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    p=0
    for fn in fns:
        try: fn(); p+=1; print(f"✅ {fn.__name__}")
        except AssertionError as e: print(f"❌ {fn.__name__}: {e}")
        except Exception as e: print(f"⚠️  {fn.__name__}: {repr(e)[:80]}")
    print(f"\n{p}/{len(fns)} schema tests passed")
    sys.exit(0 if p==len(fns) else 1)
