#!/bin/bash
set -uo pipefail
source /usr/etc/profile.d/conda.sh 2>/dev/null || source /etc/profile.d/conda.sh 2>/dev/null || true
conda activate /data/users/dengcchi/hal_work/envs/hal 2>/dev/null || conda activate /data/users/dengcchi/hal_work/envs/swe-agent-1.0
export DOCKER_HOST="unix:///run/user/$(id -u)/podman/podman.sock"
export https_proxy=http://fwdproxy:8080 http_proxy=http://fwdproxy:8080
ARMS=/data/users/dengcchi/hal_work/hal-harness/agents/SWE-agent-v1.0/arms
METHOD="$1"; RUN_DIR="$ARMS/full_$METHOD"
PREDS="$RUN_DIR/all_preds.jsonl"
# collect preds
python3 - "$RUN_DIR" "$PREDS" <<'PY'
import sys, json, glob, os
rd, out = sys.argv[1], sys.argv[2]
rows=[]
for f in sorted(glob.glob(os.path.join(rd,"*","*.pred"))):
    d=json.load(open(f))
    iid=d.get("instance_id") or os.path.basename(f).replace(".pred","")
    rows.append({"instance_id":iid,"model_patch":d.get("model_patch",""),"model_name_or_path":"prune_ab"})
with open(out,"w") as fo:
    for r in rows: fo.write(json.dumps(r)+"\n")
print(f"collected {len(rows)} predictions -> {out}")
PY
echo "=== running swebench evaluation for $METHOD ==="
python3 -m swebench.harness.run_evaluation \
  --dataset_name princeton-nlp/SWE-bench_Verified \
  --split test \
  --predictions_path "$PREDS" \
  --max_workers 4 \
  --run_id "prune_${METHOD}" \
  --cache_level instance
echo "=== GRADE $METHOD EXIT rc=$? ==="
# find the report
mkdir -p /data/users/dengcchi/prune_ab/results/pruning_ab
REPORT="prune_ab.prune_${METHOD}.json"
if [ -n "$REPORT" ]; then
  cp "$REPORT" "/data/users/dengcchi/prune_ab/results/pruning_ab/grade_${METHOD}.json"
  echo "grade report -> results/pruning_ab/grade_${METHOD}.json"
  python3 -c "import json;d=json.load(open('$REPORT'));print('resolved:',len(d.get('resolved_ids',d.get('resolved',[]))))"
fi
