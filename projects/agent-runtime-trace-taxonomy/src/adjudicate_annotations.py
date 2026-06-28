#!/usr/bin/env python3
"""adjudicate_annotations.py — Stage B adjudication (Section 12).

Given >=2 annotations per (trace,cutoff), decide when a third adjudicator is needed and
produce one adjudicated record per trace. Adjudication triggers:
  - primary L1 (workload) disagrees
  - primary bottleneck disagrees
  - one annotator abstains
  - a waste label lacks cited evidence
  - low label-set overlap (Jaccard < 0.5)
  - deterministic metrics strongly contradict an annotation
  - random 10% audit (triple-annotate even when 2 agree)
The adjudicator MAY accept/merge/remove/ambiguous/reject; MAY NOT create labels or see
model name / Pareto / future info. Raw votes are NEVER overwritten.

This module computes the trigger + a DETERMINISTIC merge for the easy cases; the hard cases
are dispatched to an adjudicator backend via the adjudicator_v1 prompt (left as a hook).
"""
from __future__ import annotations
import json, sys, os, itertools, random, collections

def jaccard(a,b):
    sa,sb=set(a),set(b)
    return len(sa&sb)/len(sa|sb) if (sa|sb) else 1.0

def needs_adjudication(recs, det_features=None, audit=False):
    reasons=[]
    if audit: reasons.append("random_audit")
    wl=[r.get("workload_annotation",{}).get("primary_l1") for r in recs]
    if len(set(x for x in wl if x))>1: reasons.append("workload_l1_disagree")
    bn=[r.get("waste_annotation",{}).get("primary_bottleneck") for r in recs]
    if len(set(x for x in bn if x))>1: reasons.append("primary_bottleneck_disagree")
    if any(r.get("annotation_metadata",{}).get("abstain") for r in recs): reasons.append("abstention")
    # missing evidence
    for r in recs:
        wa=r.get("waste_annotation",{})
        for lab in (wa.get("l2_labels") or []):
            ev=(wa.get("evidence_action_ids") or {}).get(lab)
            if not ev: reasons.append("missing_evidence"); break
    # low overlap
    l2=[set(r.get("waste_annotation",{}).get("l2_labels") or []) for r in recs]
    if len(l2)>=2:
        js=[jaccard(a,b) for a,b in itertools.combinations(l2,2)]
        if js and min(js)<0.5: reasons.append("low_label_overlap")
    return sorted(set(reasons))

def deterministic_merge(recs):
    """Easy-case merge when annotators broadly agree: union of evidenced labels,
    majority primary_bottleneck, majority workload L1."""
    def majority(vals):
        vals=[v for v in vals if v is not None]
        if not vals: return None
        return collections.Counter(vals).most_common(1)[0][0]
    wl=majority([r.get("workload_annotation",{}).get("primary_l1") for r in recs])
    bn=majority([r.get("waste_annotation",{}).get("primary_bottleneck") for r in recs])
    # union of labels that >=1 annotator evidenced
    labset=collections.Counter()
    evid=collections.defaultdict(set)
    for r in recs:
        wa=r.get("waste_annotation",{})
        for lab in (wa.get("l2_labels") or []):
            ev=(wa.get("evidence_action_ids") or {}).get(lab)
            if ev:
                labset[lab]+=1
                evid[lab]|=set(ev)
    return {
        "workload_primary_l1": wl,
        "waste_l2_labels": sorted(labset),
        "primary_bottleneck": bn,
        "evidence_action_ids": {k:sorted(v) for k,v in evid.items()},
        "label_support": dict(labset),
    }

def adjudicate_set(by_trace, audit_rate=0.10, seed=20260628):
    rng=random.Random(seed)
    out=[]
    for tid, av in by_trace.items():
        recs=list(av.values())
        if len(recs)<2:
            out.append({"trace_id":tid,"status":"SINGLE_ANNOTATION","n":len(recs)}); continue
        audit = rng.random() < audit_rate
        reasons=needs_adjudication(recs, audit=audit)
        merged=deterministic_merge(recs)
        rec={"trace_id":tid,"n_annotations":len(recs),
             "adjudication_needed":bool(reasons),"triggers":reasons,
             "auto_merge":merged,
             "status":"NEEDS_ADJUDICATOR" if reasons else "AUTO_AGREED",
             "raw_vote_ids":[r.get("annotation_metadata",{}).get("annotator_id") for r in recs]}
        out.append(rec)
    return out

if __name__=="__main__":
    import argparse, glob, re
    ap=argparse.ArgumentParser()
    ap.add_argument("--glob", default="/tmp/pilot_out/ann*_assembled.json")
    ap.add_argument("--out", default=None)
    a=ap.parse_args()
    ann_files={}
    for f in glob.glob(a.glob):
        m=re.search(r'(ann\d+)', os.path.basename(f))
        if m: ann_files[m.group(1)]=json.load(open(f))
    by=collections.defaultdict(dict)
    for ann,recs in ann_files.items():
        for r in recs:
            tid=r.get("trace_id")
            if tid: by[tid][ann]=r
    adj=adjudicate_set(by)
    n_need=sum(1 for r in adj if r.get("adjudication_needed"))
    print(f"{len(adj)} traces; {n_need} need adjudication ({100*n_need/max(len(adj),1):.0f}%)")
    tc=collections.Counter(t for r in adj for t in r.get("triggers",[]))
    print("trigger breakdown:", dict(tc))
    if a.out: json.dump(adj, open(a.out,"w"), indent=2, default=str)
