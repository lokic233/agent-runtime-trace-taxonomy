#!/bin/bash
# Consolidated paid-phase launcher: C (cache tax) -> D (intelligence tax) -> E (static policy, 30 then 50).
# GATED: requires explicit GO=1. Runs phases sequentially; each writes its own DONE markers (resumable).
# Per mission priority order. Analysis is run after each phase. NEVER touches canonical Opus artifacts.
set -uo pipefail
GEN=/home/dengcchi/agent-runtime-trace-taxonomy/projects/agent-runtime-trace-taxonomy/harness/pruning_ab/generalization
if [[ "${GO:-0}" != "1" ]]; then echo "REFUSING: set GO=1 to launch PAID phases. (This is the money gate.)"; exit 1; fi
PHASE="${PHASE:-all}"
log(){ echo "=== [$(date +%H:%M:%S)] $* ==="; }

run_phase(){ # <name> <script> <extra-env>
  local name="$1" script="$2"; shift 2
  log "PHASE $name START"
  DRY_RUN=0 "$@" bash "$GEN/scripts/$script" 2>&1
  log "PHASE $name END rc=$?"
}

if [[ "$PHASE" == "all" || "$PHASE" == "C" ]]; then
  run_phase C run_phaseC.sh
  DRY_RUN=0 python3 "$GEN/analysis/analyze_cache_tax.py" || true
fi
if [[ "$PHASE" == "all" || "$PHASE" == "D" ]]; then
  run_phase D run_phaseD.sh
  DRY_RUN=0 python3 "$GEN/analysis/analyze_intelligence_tax.py" || true
fi
if [[ "$PHASE" == "all" || "$PHASE" == "E" ]]; then
  TASKSET=30 run_phase E30 run_phaseE.sh
  DRY_RUN=0 python3 "$GEN/analysis/analyze_static_policy.py" || true
  # Phase E 30->50 expansion is a SEPARATE gated step (PHASE=E50) after the first 30 validate.
fi
log "PAID PHASES ($PHASE) COMPLETE"
