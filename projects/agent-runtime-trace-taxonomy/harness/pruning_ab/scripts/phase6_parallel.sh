#!/bin/bash
# Phase 6 PARALLEL: C0 + HYBRID1 + SHAM concurrently on 167 held-out tasks. Each high-worker. Resumable.
set -uo pipefail
cd /data/users/dengcchi/prune_ab
source /usr/etc/profile.d/conda.sh 2>/dev/null || true
PY=/data/users/dengcchi/hal_work/envs/swe-agent-1.0/bin/python3.11
FILTER='^('"$(python3 -c "import json;print('|'.join(json.load(open('heldout_tasks.json'))))")"')$'
mkdir -p logs/phase6 results/pruning_ab/phase6

run_arm_p6 () {
  local METHOD=$1 PORT=$2
  local TAG="heldout_${METHOD}"; local OUT="arms/phase6_${TAG}"
  local GRADE="results/pruning_ab/phase6/grade_${TAG}.json"
  [ -f "$GRADE" ] && { echo "[skip] $TAG graded"; return; }
  TS_PRUNE_METHOD=$METHOD PB_SHIM_PORT=$PORT PB_LEDGER=logs/phase6/ledger_${TAG}.jsonl \
    $PY scripts/prune_shim_v2.py > logs/phase6/shim_${TAG}.log 2>&1 &
  local SHIM=$!
  sleep 4
  echo "[$(date +%H:%M)] RUN $TAG (port $PORT, 167 tasks, 10 workers)"
  rm -rf "$OUT"
  bash scripts/run_arm.sh "$METHOD" "$PORT" "$FILTER" "$OUT" 10 > logs/phase6/run_${TAG}.log 2>&1
  kill $SHIM 2>/dev/null
  echo "[$(date +%H:%M)] GRADE $TAG"
  bash scripts/grade_tagged_p6.sh "$OUT" "$TAG" > logs/phase6/grade_${TAG}.log 2>&1
  echo "[$(date +%H:%M)] DONE $TAG" >> logs/phase6_parallel.log
}

# launch all 3 arms CONCURRENTLY
run_arm_p6 C0_identity 8841 &
sleep 10
run_arm_p6 HYBRID1_m7_agg2 8842 &
sleep 10
run_arm_p6 SHAM 8843 &
wait
echo "[$(date +%H:%M)] PHASE6 PARALLEL COMPLETE" >> logs/phase6_parallel.log
