#!/bin/bash
# Phase 3+4: A/A (C0x5) + SHAMx5 + HYBRID1x5 on 10 interesting tasks. Task-tagged + graded. Resumable.
set -uo pipefail
cd /data/users/dengcchi/prune_ab
source /usr/etc/profile.d/conda.sh 2>/dev/null || true
PY=/data/users/dengcchi/hal_work/envs/swe-agent-1.0/bin/python3.11
FILTER='^('"$(python3 -c "import json;print('|'.join(json.load(open('/tmp/interesting10.json'))))")"')$'
mkdir -p logs/phase34 results/pruning_ab/phase34

run_one () {
  local METHOD=$1 REP=$2 PORT=$3
  local TAG="${METHOD}_rep${REP}"
  local OUT="arms/phase34_${TAG}"
  local GRADE="results/pruning_ab/phase34/grade_${TAG}.json"
  if [ -f "$GRADE" ]; then echo "[skip] $TAG already graded"; return; fi
  while :; do
    L=$(cut -d' ' -f1 /proc/loadavg|cut -d. -f1); R=$(ps aux 2>/dev/null|grep -c '[s]weagent run-batch')
    [ "$L" -lt 250 ] && [ "$R" -lt 3 ] && break
    sleep 30
  done
  TS_PRUNE_METHOD=$METHOD PB_SHIM_PORT=$PORT PB_LEDGER=logs/phase34/ledger_${TAG}.jsonl \
    $PY scripts/prune_shim_v2.py > logs/phase34/shim_${TAG}.log 2>&1 &
  local SHIM=$!
  sleep 4
  echo "[$(date +%H:%M)] RUN $TAG (port $PORT)"
  rm -rf "$OUT"
  bash scripts/run_arm.sh "$METHOD" "$PORT" "$FILTER" "$OUT" 3 > logs/phase34/run_${TAG}.log 2>&1 || echo "  run rc=$?"
  kill $SHIM 2>/dev/null
  echo "[$(date +%H:%M)] GRADE $TAG"
  bash scripts/grade_tagged.sh "$OUT" "$TAG" > logs/phase34/grade_${TAG}.log 2>&1 || echo "  grade rc=$?"
  local n=$(python3 -c "import json,os;f='$GRADE';print(len(json.load(open(f)).get('resolved_ids',[])) if os.path.exists(f) else 'FAIL')" 2>/dev/null)
  echo "[$(date +%H:%M)] DONE $TAG resolved=$n"
}

PORT=8801
for METHOD in C0_identity SHAM HYBRID1_m7_agg2; do
  for REP in 1 2 3 4 5; do
    run_one "$METHOD" "$REP" "$PORT"
    PORT=$((PORT+1)); [ $PORT -gt 8830 ] && PORT=8801
  done
done
echo "=== PHASE34 COMPLETE $(date) ==="
