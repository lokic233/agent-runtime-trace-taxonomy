#!/usr/bin/env python3
"""Build Study-2 task fingerprints from ACTUAL trajectories (robust — SWE-agent post-processes the
problem statement, so we cannot reconstruct the fingerprint from the raw dataset field).
Scans a directory of *.traj files, extracts each task's first user message, computes
sha256(first_user_msg[:2000])[:16], and writes {fp: task_id}.
Usage: build_fingerprints_from_trajs.py <traj_dir> <out_fingerprints.json> [--merge existing.json]
"""
import json, sys, hashlib, glob, os

def first_user_text(tj):
    hist = tj.get("history") or tj.get("trajectory") or []
    for m in hist:
        if m.get("role") == "user":
            c = m.get("content")
            if isinstance(c, list):
                return " ".join(x.get("text","") for x in c if isinstance(x, dict) and isinstance(x.get("text"), str))
            return c if isinstance(c, str) else str(c)
    return None

def main():
    traj_dir, out = sys.argv[1], sys.argv[2]
    fp = {}
    if "--merge" in sys.argv:
        mp = sys.argv[sys.argv.index("--merge")+1]
        if os.path.exists(mp): fp = json.load(open(mp))
    n=0
    for tjf in glob.glob(os.path.join(traj_dir, "**", "*.traj"), recursive=True):
        tid = os.path.basename(tjf).replace(".traj","")
        try:
            tj = json.load(open(tjf))
            t = first_user_text(tj)
            if not t: continue
            h = hashlib.sha256(t[:2000].encode()).hexdigest()[:16]
            fp[h] = tid; n+=1
        except Exception as e:
            print(f"skip {tid}: {e}", file=sys.stderr)
    json.dump(fp, open(out,"w"), indent=1)
    print(f"wrote {len(fp)} fingerprints ({n} from this dir) -> {out}")

if __name__=="__main__": main()
