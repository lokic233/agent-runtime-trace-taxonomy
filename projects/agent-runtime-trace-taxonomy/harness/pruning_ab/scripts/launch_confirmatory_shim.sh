#!/bin/bash
cd /data/users/dengcchi/prune_ab
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY no_proxy NO_PROXY
export MRT_CONF_PORT=8912
export MRT_CONF_DIR=/data/users/dengcchi/prune_ab/results/pruning_ab/mrt_confirmatory
export MRT_CONF_SEED=20260702
export MRT_CONF_RUN_ID=confirmatory_locked
export MRT_CONF_MODE=randomize
export MRT_CONF_STUDY_ID=study2
export MRT_CONF_FP=/data/users/dengcchi/prune_ab/task_fingerprints_study2.json
export MRT_CONF_GIT_COMMIT=$(git -C /home/dengcchi/agent_runtime_trace_taxonomy rev-parse HEAD)
export LITELLM_LOCAL_MODEL_COST_MAP=True
exec /data/users/dengcchi/hal_work/envs/swe-agent-1.0/bin/python3.11 -u scripts/mrt_confirmatory_shim.py
