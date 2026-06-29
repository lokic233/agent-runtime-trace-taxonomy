#!/usr/bin/env python3
"""adjudication_decision.py — Section-12 trigger logic, hardened + refined on real data.

Decides which paired (a1,a2) traces need a 3rd adjudicator vote. Refinements from the
real full-annotation data (2555 votes):
  - DEFENSIVE: vote records may be non-dict (malformed) -> treated as missing.
  - SMART TRIGGER: a 'soft' bottleneck disagreement where ONE annotator says no-bottleneck
    (null) and the other names one is NOT escalated by itself (that's clean-vs-mild, the
    auto-merge keeps the named bottleneck with lower confidence). Escalate on:
      * workload primary_l1 TRUE conflict (both set, differ)
      * bottleneck TRUE conflict (both set, differ)
      * label-set Jaccard < 0.5 AND both annotators labelled >=2 (real breadth conflict,
        not one-empty)
      * an annotator abstained
      * a kept label lacks evidence
  - 10% random audit regardless.
"""
from __future__ import annotations
import json, itertools, random

def lid(x):
    if isinstance(x, str): return x
    if isinstance(x, dict):
        for k in ("id","label","name","label_id","l2"):
            if k in x and isinstance(x[k], str): return x[k]
    return None

def _label_objs(wa):
    """Collect per-label objects from any of the shapes annotators use:
      wa['l2_labels'] = [str] | [{label|l2, severity, evidence_action_ids}]
      wa['labels']    = [{l2|label, l1, severity, evidence_action_ids}]"""
    objs = []
    for key in ("l2_labels", "labels", "waste_l2", "l2"):
        v = wa.get(key) if isinstance(wa, dict) else None
        if isinstance(v, list):
            for item in v:
                if isinstance(item, dict): objs.append(item)
    return objs

def lset(v):
    """Label-id set from a list (of str or dicts), a dict, or nested under common keys."""
    if isinstance(v, dict): return {lid(k) for k in v if lid(k)}
    if isinstance(v, list): return {lid(x) for x in v if lid(x)}
    return set()

def waste_labels(wa):
    """All L2 label ids regardless of shape."""
    if not isinstance(wa, dict): return set()
    s = lset(wa.get("l2_labels"))
    for o in _label_objs(wa):
        lab = lid(o)
        if lab: s.add(lab)
    return s

def g(rec, *path):
    cur = rec
    for p in path:
        if not isinstance(cur, dict): return None
        cur = cur.get(p)
    return cur
def jac(a, b): return len(a & b) / len(a | b) if (a | b) else 1.0

def waste_evidence(wa):
    """{label_id: [action_ids]} across ALL known shapes: top-level map, per-label objects
    in l2_labels OR labels, with keys evidence_action_ids|evidence."""
    if not isinstance(wa, dict): return {}
    ev = dict(wa.get("evidence_action_ids") or {}) if isinstance(wa.get("evidence_action_ids"), dict) else {}
    for o in _label_objs(wa):
        lab = lid(o)
        ids = o.get("evidence_action_ids") or o.get("evidence")
        if lab and ids and lab not in ev:
            ev[lab] = ids
    return ev

def waste_severity(wa):
    if not isinstance(wa, dict): return {}
    sev = dict(wa.get("severity") or {}) if isinstance(wa.get("severity"), dict) else {}
    for o in _label_objs(wa):
        lab = lid(o); s = o.get("severity")
        if lab and s and lab not in sev: sev[lab] = s
    return sev

def decide(a1, a2, audit=False):
    """Return (needs_adjudication: bool, triggers: list[str])."""
    triggers = []
    if audit: triggers.append("random_audit")
    a1d = a1 if isinstance(a1, dict) else None
    a2d = a2 if isinstance(a2, dict) else None
    if a1d is None or a2d is None:
        triggers.append("malformed_or_missing_vote"); return True, triggers
    # abstention
    if g(a1d,"annotation_metadata","abstain") or g(a2d,"annotation_metadata","abstain"):
        triggers.append("abstention")
    # workload true conflict
    w1, w2 = lid(g(a1d,"workload_annotation","primary_l1")), lid(g(a2d,"workload_annotation","primary_l1"))
    if w1 and w2 and w1 != w2: triggers.append("workload_l1_conflict")
    # bottleneck true conflict (both set, differ) — NOT one-null
    b1, b2 = lid(g(a1d,"waste_annotation","primary_bottleneck")), lid(g(a2d,"waste_annotation","primary_bottleneck"))
    if b1 and b2 and b1 != b2: triggers.append("bottleneck_conflict")
    # label breadth conflict: low overlap AND both labelled (>=2 each) — real disagreement
    s1, s2 = waste_labels(g(a1d,"waste_annotation")), waste_labels(g(a2d,"waste_annotation"))
    if len(s1) >= 2 and len(s2) >= 2 and jac(s1, s2) < 0.5:
        triggers.append("label_breadth_conflict")
    # missing evidence on a label one annotator set (check ALL schema shapes)
    for ad in (a1d, a2d):
        wa = g(ad,"waste_annotation") or {}
        labs = waste_labels(wa)
        ev = waste_evidence(wa)
        if labs and not ev:
            triggers.append("missing_evidence"); break
    return (len([t for t in triggers if t != "random_audit"]) > 0 or audit), triggers

def auto_merge(a1, a2):
    """Deterministic merge for non-escalated (broadly-agreeing) pairs."""
    a1d = a1 if isinstance(a1, dict) else {}
    a2d = a2 if isinstance(a2, dict) else {}
    def majority_or_first(*vals):
        vals = [v for v in vals if v]
        return vals[0] if vals else None
    w = majority_or_first(lid(g(a1d,"workload_annotation","primary_l1")), lid(g(a2d,"workload_annotation","primary_l1")))
    b = majority_or_first(lid(g(a1d,"waste_annotation","primary_bottleneck")), lid(g(a2d,"waste_annotation","primary_bottleneck")))
    # union of labels BOTH consider OR one with evidence
    s1, s2 = waste_labels(g(a1d,"waste_annotation")), waste_labels(g(a2d,"waste_annotation"))
    inter = s1 & s2
    union = s1 | s2
    return {
        "workload_primary_l1": w,
        "primary_bottleneck": b,
        "waste_l2_labels": sorted(inter) if inter else sorted(union),  # prefer agreed; fall back to union
        "waste_l2_union": sorted(union),
        "agreement": "both" if inter == union else "partial",
    }

if __name__ == "__main__":
    import glob, collections
    base="annotations/raw_votes/full"
    rng=random.Random(20260629)
    for alias in [d.split('/')[-2] for d in glob.glob(f"{base}/*/_paired.jsonl")]:
        paired=[json.loads(l) for l in open(f"{base}/{alias}/_paired.jsonl")]
        both=[p for p in paired if p.get('a1') and p.get('a2')]
        need=0; tcount=collections.Counter()
        for p in both:
            audit = rng.random()<0.10
            n,trigs=decide(p['a1'],p['a2'],audit=audit)
            if n: need+=1
            for t in trigs: tcount[t]+=1
        print(f"{alias}: {len(both)} both-voted | adjudicate {need} ({100*need//max(len(both),1)}%) | {dict(tcount)}")
