#!/bin/bash
# Phase E — frozen static-policy transport. Models: Sonnet4.6, Haiku4.5, gpt-5-5.
# Arms: C0_identity, LINEDEDUP_e4, GENTLE6K_stable, CAP1K_stable. 30 preregistered golden tasks (->50 after gate).
# Anthropic via frozen prune_shim_v2; gpt-5-5 via prune_shim_plugboard_openai. 1 rep (deployment-level), no tuning.
set -uo pipefail
GEN=/home/dengcchi/agent-runtime-trace-taxonomy/projects/agent-runtime-trace-taxonomy/harness/pruning_ab/generalization
REPO_SCRIPTS=/home/dengcchi/agent-runtime-trace-taxonomy/projects/agent-runtime-trace-taxonomy/harness/pruning_ab/scripts
PM_DIR=/data/users/dengcchi/prune_ab/scripts
ANTHRO_SHIM=$REPO_SCRIPTS/prune_shim_v2.py
GPT_SHIM=$GEN/scripts/prune_shim_plugboard_openai.py
OUT_ROOT=/data/users/dengcchi/prune_ab/logs/xmodel_phaseE
mkdir -p "$OUT_ROOT"
TASKSET="${TASKSET:-30}"   # 30 or 50
FILTER=$(python3 -c "
import json
d=json.load(open('$GEN/../../results/pruning_ab/generalization/phaseE_task_split.json')) if False else None
import json; j=json.load(open('/home/dengcchi/agent-runtime-trace-taxonomy/projects/agent-runtime-trace-taxonomy/results/pruning_ab/generalization/phaseE_task_split.json'))
ids = j['phaseE_first30'] if '$TASKSET'=='30' else j['golden50']
print('^('+'|'.join(ids)+')\$')
")
declare -A MODELS=( [sonnet46]="anthropic/claude-sonnet-4-6" [haiku45]="anthropic/claude-haiku-4-5" [gpt55]="gpt-5-5" )
ARMS=(C0_identity LINEDEDUP_e4 GENTLE6K_stable CAP1K_stable)
cp "$PM_DIR/prune_methods.py" "$REPO_SCRIPTS/prune_methods.py"; trap 'rm -f "$REPO_SCRIPTS/prune_methods.py"' EXIT
PORT=8920; DRY="${DRY_RUN:-1}"
for mkey in sonnet46 haiku45 gpt55; do
 MODEL=${MODELS[$mkey]}
 for arm in "${ARMS[@]}"; do
  PORT=$((PORT+1)); LEDGER="$OUT_ROOT/ledger_${mkey}_${arm}_t${TASKSET}.jsonl"; OUT="$OUT_ROOT/run_${mkey}_${arm}_t${TASKSET}"; DONE="$OUT_ROOT/DONE_${mkey}_${arm}_t${TASKSET}"
  [[ -f "$DONE" ]] && { echo "skip $mkey/$arm"; continue; }
  if [[ "$mkey" == "gpt55" ]]; then SHIM="$GPT_SHIM"; EXTRA="PB_PM_DIR=$PM_DIR"; else SHIM="$ANTHRO_SHIM"; EXTRA=""; fi
  echo "=== E: $mkey/$arm/t$TASKSET port=$PORT $(date +%H:%M:%S) ==="
  [[ "$DRY" == "1" ]] && continue
  env PB_SHIM_PORT=$PORT PB_LEDGER="$LEDGER" TS_PRUNE_METHOD="$arm" TS_MODEL="$MODEL" $EXTRA python3 "$SHIM" > "$OUT_ROOT/shim_${mkey}_${arm}_t${TASKSET}.log" 2>&1 &
  SH=$!; sleep 3
  curl -s "http://127.0.0.1:$PORT" >/dev/null 2>&1 || { echo "  SHIM DOWN"; kill $SH 2>/dev/null; continue; }
  TS_MODEL="$MODEL" timeout 14400 bash "$GEN/scripts/run_arm_xmodel.sh" "$arm" "$PORT" "$FILTER" "$OUT" 6 > "$OUT_ROOT/arm_${mkey}_${arm}_t${TASKSET}.log" 2>&1
  RC=$?; kill $SH 2>/dev/null; sleep 1; echo "  rc=$RC rows=$(wc -l < "$LEDGER" 2>/dev/null||echo 0)"; [[ $RC -eq 0 ]] && touch "$DONE"
 done
done
echo "=== PHASE E COMPLETE (taskset=$TASKSET) $(date +%H:%M:%S) ==="
