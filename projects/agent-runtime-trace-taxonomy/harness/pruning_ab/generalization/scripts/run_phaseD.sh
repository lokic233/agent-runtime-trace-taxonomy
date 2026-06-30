#!/bin/bash
# Phase D — intelligence-tax capability scaling. Opus4.7(anchor) + Sonnet4.6 + Haiku4.5.
# Arms: C0_identity, LINEDEDUP_e4, GENTLE6K_stable, CAP1K_stable. 3 reps x 10 interesting tasks.
# NOTE: Opus C0/treatments already exist frozen; re-running Opus here is for the capability-scaling
# contrast under IDENTICAL current harness. Default keeps Opus byte-replay (TS_MODEL set explicitly).
set -uo pipefail
GEN=/home/dengcchi/agent-runtime-trace-taxonomy/projects/agent-runtime-trace-taxonomy/harness/pruning_ab/generalization
REPO_SCRIPTS=/home/dengcchi/agent-runtime-trace-taxonomy/projects/agent-runtime-trace-taxonomy/harness/pruning_ab/scripts
PM_DIR=/data/users/dengcchi/prune_ab/scripts
ANTHRO_SHIM=$REPO_SCRIPTS/prune_shim_v2.py
OUT_ROOT=/data/users/dengcchi/prune_ab/logs/xmodel_phaseD
mkdir -p "$OUT_ROOT"
FILTER='^(pylint-dev__pylint-4551|pytest-dev__pytest-6197|sympy__sympy-14248|sphinx-doc__sphinx-8638|sphinx-doc__sphinx-9658|pylint-dev__pylint-6386|astropy__astropy-14096|sympy__sympy-19040|sympy__sympy-13091|pylint-dev__pylint-8898)$'
declare -A MODELS=( [opus47]="anthropic/claude-opus-4-7" [sonnet46]="anthropic/claude-sonnet-4-6" [haiku45]="anthropic/claude-haiku-4-5" )
ARMS=(C0_identity LINEDEDUP_e4 GENTLE6K_stable CAP1K_stable)
cp "$PM_DIR/prune_methods.py" "$REPO_SCRIPTS/prune_methods.py"; trap 'rm -f "$REPO_SCRIPTS/prune_methods.py"' EXIT
PORT=8880; DRY="${DRY_RUN:-1}"
for mkey in opus47 sonnet46 haiku45; do
 MODEL=${MODELS[$mkey]}
 for rep in 1 2 3; do
  for arm in "${ARMS[@]}"; do
   PORT=$((PORT+1)); LEDGER="$OUT_ROOT/ledger_${mkey}_${arm}_rep${rep}.jsonl"; OUT="$OUT_ROOT/run_${mkey}_${arm}_rep${rep}"; DONE="$OUT_ROOT/DONE_${mkey}_${arm}_rep${rep}"
   [[ -f "$DONE" ]] && { echo "skip $mkey/$arm/rep$rep"; continue; }
   echo "=== D: $mkey/$arm/rep$rep port=$PORT $(date +%H:%M:%S) ==="
   [[ "$DRY" == "1" ]] && continue
   env PB_SHIM_PORT=$PORT PB_LEDGER="$LEDGER" TS_PRUNE_METHOD="$arm" TS_MODEL="$MODEL" python3 "$ANTHRO_SHIM" > "$OUT_ROOT/shim_${mkey}_${arm}_rep${rep}.log" 2>&1 &
   SH=$!; sleep 3
   curl -s "http://127.0.0.1:$PORT" >/dev/null 2>&1 || { echo "  SHIM DOWN"; kill $SH 2>/dev/null; continue; }
   TS_MODEL="$MODEL" timeout 7200 bash "$GEN/scripts/run_arm_xmodel.sh" "$arm" "$PORT" "$FILTER" "$OUT" 4 > "$OUT_ROOT/arm_${mkey}_${arm}_rep${rep}.log" 2>&1
   RC=$?; kill $SH 2>/dev/null; sleep 1; echo "  rc=$RC rows=$(wc -l < "$LEDGER" 2>/dev/null||echo 0)"; [[ $RC -eq 0 ]] && touch "$DONE"
  done
 done
done
echo "=== PHASE D COMPLETE $(date +%H:%M:%S) ==="
