#!/bin/bash
cd /data/users/dengcchi/prune_ab
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY no_proxy NO_PROXY
export MRT_FORMAL_PORT=8911
export MRT_FORMAL_DIR=/data/users/dengcchi/prune_ab/results/pruning_ab/mrt_formal
export MRT_FORMAL_SEED=20260701
export MRT_FORMAL_RUN_ID=${MRT_FORMAL_RUN_ID:-formal_run}
export MRT_FORMAL_MODE=${MRT_FORMAL_MODE:-randomize}
export MRT_FORMAL_FP=/data/users/dengcchi/prune_ab/task_fingerprints.json
export MRT_FORMAL_GIT_COMMIT=0599c553eb9cf3c9aa399726c826f63d0bd5d195
export LITELLM_LOCAL_MODEL_COST_MAP=True
exec /data/users/dengcchi/hal_work/envs/swe-agent-1.0/bin/python3.11 -u scripts/mrt_formal_shim.py
