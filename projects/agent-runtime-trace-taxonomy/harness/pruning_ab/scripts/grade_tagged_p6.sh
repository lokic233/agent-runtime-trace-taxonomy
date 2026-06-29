#!/bin/bash
set -uo pipefail
source /usr/etc/profile.d/conda.sh 2>/dev/null || true
conda activate /data/users/dengcchi/hal_work/envs/hal 2>/dev/null || true
export DOCKER_HOST="unix:///run/user/$(id -u)/podman/podman.sock"
cd /data/users/dengcchi/prune_ab
OUT="$1"; TAG="$2"; PREDS="$OUT/all_preds.jsonl"
python3 - "$OUT" "$PREDS" <<'PY'
import sys,json,glob,os
rd,out=sys.argv[1],sys.argv[2]; rows=[]
for f in sorted(glob.glob(os.path.join(rd,"*","*.pred"))):
    d=json.load(open(f)); iid=d.get("instance_id") or os.path.basename(f).replace(".pred","")
    rows.append({"instance_id":iid,"model_patch":d.get("model_patch",""),"model_name_or_path":"prune_ab"})
open(out,"w").write("\n".join(json.dumps(r) for r in rows))
print(f"{len(rows)} preds")
PY
python3 -m swebench.harness.run_evaluation --dataset_name princeton-nlp/SWE-bench_Verified \
  --split test --predictions_path "$PREDS" --max_workers 6 --run_id "p6_$TAG" --cache_level instance 2>&1 | tail -15
R="prune_ab.p6_$TAG.json"
[ -f "$R" ] && cp "$R" "results/pruning_ab/phase6/grade_$TAG.json" && echo "captured grade_$TAG"
