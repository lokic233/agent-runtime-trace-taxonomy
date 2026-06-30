#!/bin/bash
set -uo pipefail
cd /data/users/dengcchi/prune_ab
source /usr/etc/profile.d/conda.sh 2>/dev/null || true
PY=/data/users/dengcchi/hal_work/envs/swe-agent-1.0/bin/python3.11
METHOD=$1; PORT=$2
OUT="arms/e4_${METHOD}"; GRADE="results/pruning_ab/e4/grade_${METHOD}.json"
[ -f "$GRADE" ] && { echo "[skip] $METHOD"; exit 0; }
FILTER='^('"$(python3 -c "import json;print('|'.join(json.load(open('/tmp/golden50.json'))))")"')$'
TS_PRUNE_METHOD=$METHOD PB_SHIM_PORT=$PORT PB_LEDGER=logs/e4/ledger_${METHOD}.jsonl \
  $PY scripts/prune_shim_v2.py > logs/e4/shim_${METHOD}.log 2>&1 &
SHIM=$!
sleep 4
echo "[$(date +%H:%M)] RUN $METHOD port=$PORT"
rm -rf "$OUT"
bash scripts/run_arm.sh "$METHOD" "$PORT" "$FILTER" "$OUT" 4 > logs/e4/run_${METHOD}.log 2>&1
kill $SHIM 2>/dev/null
echo "[$(date +%H:%M)] $METHOD run done"
