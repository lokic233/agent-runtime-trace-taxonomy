#!/bin/bash
# Phase 6: held-out validation. C0 + SHAM + HYBRID1 on 167 held-out tasks. Task-tagged + graded. Resumable.
set -uo pipefail
cd /data/users/dengcchi/prune_ab
source /usr/etc/profile.d/conda.sh 2>/dev/null || true
PY=/data/users/dengcchi/hal_work/envs/swe-agent-1.0/bin/python3.11
FILTER='^('"$(python3 -c "import json;print('|'.join(json.load(open('heldout_tasks.json'))))")"')$'
mkdir -p logs/phase6 results/pruning_ab/phase6

run_cell () {
  local METHOD=$1 PORT=$2
  local TAG="heldout_${METHOD}"
  local OUT="arms/phase6_${TAG}"
  local GRADE="results/pruning_ab/phase6/grade_${TAG}.json"
  if [ -f "$GRADE" ]; then echo "[skip] $TAG already graded"; return; fi
  while :; do
    L=$(cut -d' ' -f1 /proc/loadavg|cut -d. -f1); R=$(ps aux 2>/dev/null|grep -c '[s]weagent run-batch')
    [ "$L" -lt 250 ] && [ "$R" -lt 3 ] && break
    sleep 30
  done
  TS_PRUNE_METHOD=$METHOD PB_SHIM_PORT=$PORT PB_LEDGER=logs/phase6/ledger_${TAG}.jsonl \
    $PY scripts/prune_shim_v2.py > logs/phase6/shim_${TAG}.log 2>&1 &
  local SHIM=$!
  sleep 4
  echo "[$(date +%H:%M)] RUN $TAG (port $PORT) on 167 held-out tasks"
  rm -rf "$OUT"
  bash scripts/run_arm.sh "$METHOD" "$PORT" "$FILTER" "$OUT" 6 > logs/phase6/run_${TAG}.log 2>&1 || echo "  run rc=$?"
  kill $SHIM 2>/dev/null
  echo "[$(date +%H:%M)] GRADE $TAG"
  bash scripts/grade_tagged_p6.sh "$OUT" "$TAG" > logs/phase6/grade_${TAG}.log 2>&1 || echo "  grade rc=$?"
  local n=$(python3 -c "import json,os;f='$GRADE';print(len(json.load(open(f)).get('resolved_ids',[])) if os.path.exists(f) else 'FAIL')" 2>/dev/null)
  echo "[$(date +%H:%M)] DONE $TAG resolved=$n"
}

# C0 first (baseline), then HYBRID1, then SHAM (the minimal frozen suite)
run_cell C0_identity 8841
run_cell HYBRID1_m7_agg2 8842
run_cell SHAM 8843
echo "=== PHASE 6 COMPLETE $(date) ==="
