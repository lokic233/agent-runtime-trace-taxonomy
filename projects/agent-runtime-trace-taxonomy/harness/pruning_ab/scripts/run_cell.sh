#!/bin/bash
# run_cell.sh <METHOD> <REP> <PORT> — one self-contained cell: shim -> run -> grade
set -uo pipefail
cd /data/users/dengcchi/prune_ab
source /usr/etc/profile.d/conda.sh 2>/dev/null || true
PY=/data/users/dengcchi/hal_work/envs/swe-agent-1.0/bin/python3.11
METHOD=$1; REP=$2; PORT=$3
TAG="${METHOD}_rep${REP}"; OUT="arms/phase34_${TAG}"
GRADE="results/pruning_ab/phase34/grade_${TAG}.json"
[ -f "$GRADE" ] && { echo "[skip] $TAG already graded"; exit 0; }
FILTER='^('"$(python3 -c "import json;print('|'.join(json.load(open('interesting10.json'))))")"')$'
TS_PRUNE_METHOD=$METHOD PB_SHIM_PORT=$PORT PB_LEDGER=logs/phase34/ledger_${TAG}.jsonl \
  $PY scripts/prune_shim_v2.py > logs/phase34/shim_${TAG}.log 2>&1 &
SHIM=$!
sleep 4
echo "[$(date +%H:%M)] RUN $TAG port=$PORT"
rm -rf "$OUT"
bash scripts/run_arm.sh "$METHOD" "$PORT" "$FILTER" "$OUT" 4 > logs/phase34/run_${TAG}.log 2>&1
kill $SHIM 2>/dev/null
echo "[$(date +%H:%M)] GRADE $TAG"
bash scripts/grade_tagged.sh "$OUT" "$TAG" > logs/phase34/grade_${TAG}.log 2>&1
n=$(python3 -c "import json,os;f='$GRADE';print(len(json.load(open(f)).get('resolved_ids',[])) if os.path.exists(f) else 'FAIL')" 2>/dev/null)
echo "[$(date +%H:%M)] DONE $TAG resolved=$n"
