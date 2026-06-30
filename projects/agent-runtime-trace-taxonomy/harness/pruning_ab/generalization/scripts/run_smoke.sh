#!/bin/bash
# Phase B smoke orchestrator — 5 tasks x 6 arms x 3 models. VALIDITY ONLY (no scientific claims).
# Per (model, arm): launch the right shim with a per-cell ledger, run run_arm_xmodel on the 5-task filter,
# tear down. Anthropic (Sonnet/Haiku) -> frozen prune_shim_v2.py; gpt-5-5 -> prune_shim_plugboard_openai.py.
# DRY_RUN=1 prints the plan + validates plumbing without launching paid agent runs.
set -uo pipefail
GEN=/home/dengcchi/agent-runtime-trace-taxonomy/projects/agent-runtime-trace-taxonomy/harness/pruning_ab/generalization
PM_DIR=/data/users/dengcchi/prune_ab/scripts            # canonical live PM (functions == frozen)
ANTHRO_SHIM=/home/dengcchi/agent-runtime-trace-taxonomy/projects/agent-runtime-trace-taxonomy/harness/pruning_ab/scripts/prune_shim_v2.py
GPT_SHIM=$GEN/scripts/prune_shim_plugboard_openai.py
OUT_ROOT=/data/users/dengcchi/prune_ab/logs/xmodel_smoke
mkdir -p "$OUT_ROOT"
# 5 smoke tasks (pre-treatment selection)
FILTER='^(scikit-learn__scikit-learn-13439|django__django-14493|astropy__astropy-12907|pylint-dev__pylint-4551|sphinx-doc__sphinx-8638)$'
ARMS=(C0_identity SHAM HYBRID1_m7_agg2 LINEDEDUP_e4 GENTLE6K_stable CAP1K_stable)
DRY_RUN="${DRY_RUN:-1}"
declare -A MODELS=( [sonnet46]="anthropic/claude-sonnet-4-6" [haiku45]="anthropic/claude-haiku-4-5" [gpt55]="gpt-5-5" )
PORT_BASE=8760
echo "=== PHASE B SMOKE (DRY_RUN=$DRY_RUN) ==="
echo "tasks(5): scikit-13439 django-14493 astropy-12907 pylint-4551 sphinx-8638"
echo "arms(6): ${ARMS[*]}"
pi=0
for mkey in sonnet46 haiku45 gpt55; do
  MODEL=${MODELS[$mkey]}
  for arm in "${ARMS[@]}"; do
    PORT=$((PORT_BASE+pi)); pi=$((pi+1))
    LEDGER="$OUT_ROOT/ledger_${mkey}_${arm}.jsonl"
    OUT="$OUT_ROOT/run_${mkey}_${arm}"
    if [[ "$mkey" == "gpt55" ]]; then SHIM="$GPT_SHIM"; else SHIM="$ANTHRO_SHIM"; fi
    echo "--- cell: model=$MODEL arm=$arm port=$PORT shim=$(basename $SHIM) ledger=$(basename $LEDGER)"
    if [[ "$DRY_RUN" == "1" ]]; then continue; fi
    # launch shim
    PB_SHIM_PORT=$PORT PB_LEDGER="$LEDGER" TS_PRUNE_METHOD="$arm" TS_MODEL="$MODEL" PB_PM_DIR="$PM_DIR" \
      python3 "$SHIM" > "$OUT_ROOT/shim_${mkey}_${arm}.log" 2>&1 &
    SHIM_PID=$!; sleep 3
    # health check
    curl -s "http://127.0.0.1:$PORT" >/dev/null 2>&1 || { echo "  SHIM DOWN"; kill $SHIM_PID 2>/dev/null; continue; }
    # run the arm
    TS_MODEL="$MODEL" bash "$GEN/scripts/run_arm_xmodel.sh" "$arm" "$PORT" "$FILTER" "$OUT" 4 \
      > "$OUT_ROOT/arm_${mkey}_${arm}.log" 2>&1
    kill $SHIM_PID 2>/dev/null
  done
done
echo "=== SMOKE PLAN COMPLETE (DRY_RUN=$DRY_RUN) — cells=$pi ==="
