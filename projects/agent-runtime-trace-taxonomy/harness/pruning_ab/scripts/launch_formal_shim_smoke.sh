#!/bin/bash
cd /data/users/dengcchi/prune_ab
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY no_proxy NO_PROXY
export MRT_FORMAL_PORT=8911
export MRT_FORMAL_DIR=/data/users/dengcchi/prune_ab/results/pruning_ab/mrt_formal_smoke
export MRT_FORMAL_SEED=20260701 MRT_FORMAL_RUN_ID=infra_smoke MRT_FORMAL_MODE=randomize
export MRT_FORMAL_FP=/data/users/dengcchi/prune_ab/task_fingerprints.json
export MRT_FORMAL_GIT_COMMIT=$(git -C ~/agent_runtime_trace_taxonomy rev-parse HEAD 2>/dev/null)
export LITELLM_LOCAL_MODEL_COST_MAP=True
exec /data/users/dengcchi/hal_work/envs/swe-agent-1.0/bin/python3.11 -u scripts/mrt_formal_shim.py
