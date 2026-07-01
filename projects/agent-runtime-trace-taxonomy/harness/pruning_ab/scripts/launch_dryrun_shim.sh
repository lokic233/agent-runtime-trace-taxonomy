#!/bin/bash
cd /data/users/dengcchi/prune_ab
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY no_proxy NO_PROXY
export MRT_DRY_PORT=8913
export LITELLM_LOCAL_MODEL_COST_MAP=True
exec /data/users/dengcchi/hal_work/envs/swe-agent-1.0/bin/python3.11 -u scripts/mrt_dryrun_passthrough_shim.py
