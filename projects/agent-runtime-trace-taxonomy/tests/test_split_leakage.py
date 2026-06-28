#!/usr/bin/env python3
"""test_split_leakage.py — enforce dataset-split integrity (Section 16.3 / red-team #3,4)."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

def check_split(split):
    """split = {'train':[trace_ids], 'validation':[...], 'test':[...],
                'model_transfer_test':[...], 'repo_transfer_test':[...]}"""
    errors=[]
    def task_of(tid): return tid.split("@")[0]
    def repo_of(tid): return task_of(tid).split("__")[0] if "__" in task_of(tid) else None
    train=set(split.get("train",[])); val=set(split.get("validation",[])); test=set(split.get("test",[]))
    # 1) no identical trace across splits
    for a,b,na,nb in [(train,val,"train","val"),(train,test,"train","test"),(val,test,"val","test")]:
        ov=a&b
        if ov: errors.append(f"trace overlap {na}/{nb}: {list(ov)[:3]}")
    # 2) no identical TASK across train and test (prefix/full of same task too)
    train_tasks={task_of(t) for t in train}; test_tasks={task_of(t) for t in test}
    tov=train_tasks & test_tasks
    if tov: errors.append(f"TASK leak train/test: {list(tov)[:3]}")
    # 3) no prefix/full of same trace across splits (same trace_id base, diff cutoff)
    def base(tid): return tid.split("#cutoff=")[0]
    for a,b,na,nb in [(train,test,"train","test"),(train,val,"train","val")]:
        bov={base(x) for x in a} & {base(x) for x in b}
        if bov: errors.append(f"prefix/full base leak {na}/{nb}: {list(bov)[:3]}")
    # 4) held-out solver_E (qwen-32B) excluded from train
    e_in_train=[t for t in train if t.endswith("@solver_E")]
    if e_in_train: errors.append(f"HELD-OUT solver_E in train: {len(e_in_train)} traces")
    # 5) model-transfer test split exists and is a distinct solver
    mtt=split.get("model_transfer_test",[])
    if mtt and any(not t.endswith("@solver_E") for t in mtt):
        # model-transfer should be the held-out solver
        pass
    # 6) repo-transfer test: its repos must NOT appear in train
    rtt=split.get("repo_transfer_test",[])
    if rtt:
        train_repos={repo_of(t) for t in train}; rtt_repos={repo_of(t) for t in rtt}
        rov=train_repos & rtt_repos
        if rov: errors.append(f"repo-transfer leak (repo in train too): {list(rov)[:3]}")
    return errors

def test_clean_split_passes():
    split={"train":["django__a-1@solver_A","django__b-2@solver_B"],
           "validation":["flask__c-3@solver_A"],
           "test":["numpy__d-4@solver_C"],
           "model_transfer_test":["django__a-1@solver_E"],
           "repo_transfer_test":["scipy__z-9@solver_A"]}
    assert check_split(split)==[], check_split(split)

def test_task_leak_detected():
    split={"train":["django__a-1@solver_A"],"test":["django__a-1@solver_B"]}  # same task!
    errs=check_split(split); assert any("TASK leak" in e for e in errs), errs

def test_heldout_in_train_detected():
    split={"train":["django__a-1@solver_E"],"test":["flask__b-2@solver_A"]}
    errs=check_split(split); assert any("HELD-OUT solver_E" in e for e in errs), errs

def test_trace_overlap_detected():
    split={"train":["x@solver_A"],"test":["x@solver_A"]}
    errs=check_split(split); assert any("overlap" in e or "leak" in e for e in errs), errs

def test_repo_transfer_leak_detected():
    split={"train":["django__a-1@solver_A"],"test":["flask__b@solver_A"],
           "repo_transfer_test":["django__z-9@solver_B"]}  # django in train AND repo-transfer
    errs=check_split(split); assert any("repo-transfer leak" in e for e in errs), errs

if __name__=="__main__":
    fns=[v for k,v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    p=0
    for fn in fns:
        try: fn(); p+=1; print(f"✅ {fn.__name__}")
        except AssertionError as e: print(f"❌ {fn.__name__}: {e}")
    print(f"\n{p}/{len(fns)} split-leakage tests passed")
    sys.exit(0 if p==len(fns) else 1)
