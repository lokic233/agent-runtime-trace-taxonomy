#!/bin/bash
cd /data/users/dengcchi/prune_ab
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY no_proxy NO_PROXY
export MRT_RESCUE_PORT=8910
export MRT_RESCUE_EVENTLOG=/data/users/dengcchi/prune_ab/results/pruning_ab/mrt_rescue/events.jsonl
export MRT_RESCUE_SEED=20260701
export LITELLM_LOCAL_MODEL_COST_MAP=True
exec /data/users/dengcchi/hal_work/envs/swe-agent-1.0/bin/python3.11 -u scripts/mrt_rescue_shim.py
