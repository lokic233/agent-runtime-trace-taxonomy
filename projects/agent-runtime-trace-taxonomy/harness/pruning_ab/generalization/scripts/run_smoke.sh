#!/bin/bash
# Phase B smoke orchestrator — 5 tasks x 6 arms x 3 models = 18 cells. VALIDITY ONLY.
set -uo pipefail
GEN=/home/dengcchi/agent-runtime-trace-taxonomy/projects/agent-runtime-trace-taxonomy/harness/pruning_ab/generalization
REPO_SCRIPTS=/home/dengcchi/agent-runtime-trace-taxonomy/projects/agent-runtime-trace-taxonomy/harness/pruning_ab/scripts
PM_DIR=/data/users/dengcchi/prune_ab/scripts
ANTHRO_SHIM=/data/users/dengcchi/prune_ab/scripts/prune_shim_v2.py
GPT_SHIM=/data/users/dengcchi/prune_ab/scripts/prune_shim_plugboard_openai.py
OUT_ROOT=/data/users/dengcchi/prune_ab/logs/xmodel_smoke
mkdir -p "$OUT_ROOT"
FILTER='^(scikit-learn__scikit-learn-13439|django__django-14493|astropy__astropy-12907|pylint-dev__pylint-4551|sphinx-doc__sphinx-8638)$'
ARMS=(C0_identity SHAM HYBRID1_m7_agg2 LINEDEDUP_e4 GENTLE6K_stable CAP1K_stable)
declare -A MODELS=( [sonnet46]="anthropic/claude-sonnet-4-6" [haiku45]="anthropic/claude-haiku-4-5" [gpt55]="openai/gpt-5-5" )
PORT_BASE=8810
# stage canonical PM next to the frozen anthropic shim (it imports from its own dir)
pi=0
for mkey in sonnet46 haiku45 gpt55; do
  MODEL=${MODELS[$mkey]}
  for arm in "${ARMS[@]}"; do
    PORT=$((PORT_BASE+pi)); pi=$((pi+1))
    LEDGER="$OUT_ROOT/ledger_${mkey}_${arm}.jsonl"; OUT="$OUT_ROOT/run_${mkey}_${arm}"
    DONE="$OUT_ROOT/DONE_${mkey}_${arm}"
    [[ -f "$DONE" ]] && { echo "skip done $mkey/$arm"; continue; }
    if [[ "$mkey" == "gpt55" ]]; then SHIM="$GPT_SHIM"; EXTRA="PB_PM_DIR=$PM_DIR"; else SHIM="$ANTHRO_SHIM"; EXTRA=""; fi
    echo "=== CELL $mkey/$arm port=$PORT $(date +%H:%M:%S) ==="
    env PB_SHIM_PORT=$PORT PB_LEDGER="$LEDGER" TS_PRUNE_METHOD="$arm" TS_MODEL="$MODEL" $EXTRA \
      python3 "$SHIM" > "$OUT_ROOT/shim_${mkey}_${arm}.log" 2>&1 &
    SHIM_PID=$!; sleep 3
    if ! curl -s "http://127.0.0.1:$PORT" >/dev/null 2>&1; then echo "  SHIM DOWN $mkey/$arm"; kill $SHIM_PID 2>/dev/null; continue; fi
    TS_MODEL="$MODEL" timeout 5400 bash "$GEN/scripts/run_arm_xmodel.sh" "$arm" "$PORT" "$FILTER" "$OUT" 4 \
      > "$OUT_ROOT/arm_${mkey}_${arm}.log" 2>&1
    RC=$?
    kill $SHIM_PID 2>/dev/null; sleep 1
    echo "  rc=$RC ledger_rows=$(wc -l < "$LEDGER" 2>/dev/null || echo 0)"
    [[ $RC -eq 0 ]] && touch "$DONE"
  done
done
echo "=== SMOKE COMPLETE cells=$pi $(date +%H:%M:%S) ==="
