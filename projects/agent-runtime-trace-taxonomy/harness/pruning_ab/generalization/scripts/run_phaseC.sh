#!/bin/bash
# Phase C — cache-tax mechanism transport. Models: Sonnet 4.6, Haiku 4.5. Arms: C0_identity, SHAM, HYBRID1_m7_agg2.
# 5 reps x 10 interesting tasks x arm x model. Primary estimand: cache_creation_fraction.
# Arm order counterbalanced per rep to avoid cache-warming order confounds. Resume via DONE markers.
set -uo pipefail
GEN=/home/dengcchi/agent-runtime-trace-taxonomy/projects/agent-runtime-trace-taxonomy/harness/pruning_ab/generalization
REPO_SCRIPTS=/home/dengcchi/agent-runtime-trace-taxonomy/projects/agent-runtime-trace-taxonomy/harness/pruning_ab/scripts
PM_DIR=/data/users/dengcchi/prune_ab/scripts
ANTHRO_SHIM=/data/users/dengcchi/prune_ab/scripts/prune_shim_v2.py
OUT_ROOT=/data/users/dengcchi/prune_ab/logs/xmodel_phaseC
mkdir -p "$OUT_ROOT"
FILTER='^(pylint-dev__pylint-4551|pytest-dev__pytest-6197|sympy__sympy-14248|sphinx-doc__sphinx-8638|sphinx-doc__sphinx-9658|pylint-dev__pylint-6386|astropy__astropy-14096|sympy__sympy-19040|sympy__sympy-13091|pylint-dev__pylint-8898)$'
declare -A MODELS=( [sonnet46]="anthropic/claude-sonnet-4-6" [haiku45]="anthropic/claude-haiku-4-5" )
ARMS=(C0_identity SHAM HYBRID1_m7_agg2)
# PM co-located with live shims in /data/users/dengcchi/prune_ab/scripts (no staging/trap needed)
PORT=8840; DRY="${DRY_RUN:-1}"
for mkey in sonnet46 haiku45; do
 MODEL=${MODELS[$mkey]}
 for rep in 1 2 3 4 5; do
  # counterbalance: rotate arm order by rep
  case $((rep % 3)) in 0) ORDER=(C0_identity SHAM HYBRID1_m7_agg2);; 1) ORDER=(SHAM HYBRID1_m7_agg2 C0_identity);; 2) ORDER=(HYBRID1_m7_agg2 C0_identity SHAM);; esac
  for arm in "${ORDER[@]}"; do
   PORT=$((PORT+1)); LEDGER="$OUT_ROOT/ledger_${mkey}_${arm}_rep${rep}.jsonl"; OUT="$OUT_ROOT/run_${mkey}_${arm}_rep${rep}"; DONE="$OUT_ROOT/DONE_${mkey}_${arm}_rep${rep}"
   [[ -f "$DONE" ]] && { echo "skip $mkey/$arm/rep$rep"; continue; }
   echo "=== C: $mkey/$arm/rep$rep port=$PORT $(date +%H:%M:%S) ==="
   [[ "$DRY" == "1" ]] && continue
   env PB_SHIM_PORT=$PORT PB_LEDGER="$LEDGER" TS_PRUNE_METHOD="$arm" TS_MODEL="$MODEL" python3 "$ANTHRO_SHIM" > "$OUT_ROOT/shim_${mkey}_${arm}_rep${rep}.log" 2>&1 &
   SH=$!; sleep 3
   curl -s "http://127.0.0.1:$PORT" >/dev/null 2>&1 || { echo "  SHIM DOWN"; kill $SH 2>/dev/null; continue; }
   TS_MODEL="$MODEL" timeout 7200 bash "$GEN/scripts/run_arm_xmodel.sh" "$arm" "$PORT" "$FILTER" "$OUT" 4 > "$OUT_ROOT/arm_${mkey}_${arm}_rep${rep}.log" 2>&1
   RC=$?; kill $SH 2>/dev/null; sleep 1; echo "  rc=$RC rows=$(wc -l < "$LEDGER" 2>/dev/null||echo 0)"; [[ $RC -eq 0 ]] && touch "$DONE"
  done
 done
done
echo "=== PHASE C COMPLETE $(date +%H:%M:%S) ==="
