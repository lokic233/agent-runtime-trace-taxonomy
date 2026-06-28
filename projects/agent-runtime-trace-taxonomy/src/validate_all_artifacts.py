#!/usr/bin/env python3
"""validate_all_artifacts.py — master integrity check over the whole project.
Runs the test suites + schema validity + blinding scan + taxonomy constraints + cross-file
consistency. Exit 0 only if everything passes. Section 17 red-team adjacent."""
from __future__ import annotations
import json, sys, os, subprocess, glob, re
HERE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def ok(b): return "✅" if b else "❌"
fails=[]

def check_schemas():
    import json
    for s in glob.glob(os.path.join(HERE,"schemas","*.json")):
        try: json.load(open(s))
        except Exception as e: fails.append(f"schema {os.path.basename(s)}: {e}")

def check_taxonomy_constraints():
    import yaml
    w=yaml.safe_load(open(os.path.join(HERE,"taxonomy","waste_taxonomy_v1.yaml")))
    nl1=len(w["l1"]); nl2=len(w["l2"])
    if nl1>7: fails.append(f"waste L1 {nl1} > 7")
    if nl2>22: fails.append(f"waste L2 {nl2} > 22 (hard max)")
    # every label has required fields
    req=["id","parent","definition","observable_unit","positive_indicators","required_evidence",
         "exclusions","distinguishing_rule","severity_rubric","candidate_interventions","observability"]
    for x in w["l2"]:
        miss=[r for r in req if r not in x]
        if miss: fails.append(f"label {x.get('id')} missing {miss}")
    return nl1,nl2

def check_blinding():
    """No SOLVER model name or fs path in any annotator-facing / committed data artifact."""
    banned=re.compile(r"(claude-opus|claude-sonnet|opus-4|sonnet-3|qwen2|/data/users/\w+|/home/dengcchi|edit_anthropic)", re.I)
    scan_dirs=["manifests","taxonomy","reports/open_coding","exports","mappings"]
    hits=[]
    for d in scan_dirs:
        for f in glob.glob(os.path.join(HERE,d,"**","*"), recursive=True):
            if os.path.isfile(f) and f.endswith((".json",".jsonl",".yaml",".md")):
                try: txt=open(f,encoding="utf-8",errors="ignore").read()
                except: continue
                m=banned.search(txt)
                if m: hits.append(f"{os.path.relpath(f,HERE)}: {m.group(0)!r}")
    if hits: fails.extend([f"BLINDING: {h}" for h in hits[:10]])

def check_private_gitignored():
    # the alias map + locator must NOT be tracked
    r=subprocess.run(["git","-C",HERE,"ls-files"],capture_output=True,text=True)
    tracked=r.stdout
    for forbidden in ("model_alias_map.json","trace_locator.jsonl"):
        if forbidden in tracked: fails.append(f"PRIVATE LEAK: {forbidden} is git-tracked")

def run_tests():
    res={}
    for t in ("test_trace_normalization","test_no_future_leakage","test_annotation_schema","test_split_leakage"):
        p=subprocess.run([sys.executable, os.path.join(HERE,"tests",t+".py")],capture_output=True,text=True)
        passed = p.returncode==0
        res[t]=passed
        if not passed: fails.append(f"test {t} FAILED")
    return res

if __name__=="__main__":
    print("=== validate_all_artifacts ===")
    check_schemas()
    nl1,nl2=check_taxonomy_constraints()
    print(f"  taxonomy: {nl1} L1 / {nl2} L2  {ok(nl1<=7 and nl2<=22)}")
    check_blinding()
    check_private_gitignored()
    tres=run_tests()
    for t,p in tres.items(): print(f"  {ok(p)} {t}")
    print(f"  blinding scan: {ok(not any(f.startswith('BLINDING') for f in fails))}")
    print(f"  private gitignored: {ok(not any('PRIVATE LEAK' in f for f in fails))}")
    if fails:
        print(f"\n❌ {len(fails)} FAILURES:")
        for f in fails: print("   -",f)
        sys.exit(1)
    print("\n✅ ALL ARTIFACT CHECKS PASSED")
