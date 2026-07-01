#!/bin/bash
# Parallel autonomous driver (user GO approved). Smoke already PASSED. Runs C->D->E30 with MAXPAR concurrency.
set -uo pipefail
GEN=/home/dengcchi/agent-runtime-trace-taxonomy/projects/agent-runtime-trace-taxonomy/harness/pruning_ab/generalization
DL=/data/users/dengcchi/prune_ab/logs/DRIVE_PARALLEL.log
MAXPAR="${MAXPAR:-6}"
log(){ echo "=== [$(date +%H:%M:%S)] $*" | tee -a "$DL"; }
log "PARALLEL DRIVER start MAXPAR=$MAXPAR"
log "STAGE 1: Phase C (parallel)"
PHASE=C MAXPAR=$MAXPAR bash "$GEN/scripts/run_phase_parallel.sh" 2>&1 | tee -a "$DL"
python3 "$GEN/analysis/analyze_cache_tax.py" 2>&1 | tee -a "$DL" || true
log "STAGE 2: Phase D (parallel)"
PHASE=D MAXPAR=$MAXPAR bash "$GEN/scripts/run_phase_parallel.sh" 2>&1 | tee -a "$DL"
python3 "$GEN/analysis/analyze_intelligence_tax.py" 2>&1 | tee -a "$DL" || true
log "STAGE 3: Phase E30 (parallel)"
PHASE=E MAXPAR=$MAXPAR TASKSET=30 bash "$GEN/scripts/run_phase_parallel.sh" 2>&1 | tee -a "$DL"
python3 "$GEN/analysis/analyze_static_policy.py" 2>&1 | tee -a "$DL" || true
python3 "$GEN/analysis/consistency_assertions.py" 2>&1 | tee -a "$DL" || true
log "ALL PHASES (C,D,E30) COMPLETE"
