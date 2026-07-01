#!/bin/bash
# run_arm_xmodel.sh — cross-model generalization variant of run_arm.sh.
# Parameterizes the model string (the canonical run_arm.sh hardcodes anthropic/claude-opus-4-7).
# DEFAULT model == claude-opus-4-7 => byte-compatible Opus replay (set TS_MODEL to override).
# Usage: TS_MODEL=anthropic/claude-sonnet-4-6 run_arm_xmodel.sh <method> <port> <filter_regex> <out_dir> <nworkers>
set -uo pipefail
source /usr/etc/profile.d/conda.sh 2>/dev/null || source /etc/profile.d/conda.sh 2>/dev/null || true
conda activate /data/users/dengcchi/hal_work/envs/swe-agent-1.0
for v in http_proxy https_proxy HTTP_PROXY HTTPS_PROXY no_proxy NO_PROXY all_proxy ALL_PROXY; do unset $v; done
export MSWEA_DOCKER_EXECUTABLE=podman
export DOCKER_HOST="unix:///run/user/$(id -u)/podman/podman.sock"
export PYTHONPATH="/data/users/dengcchi/hal_work/pyhooks:${PYTHONPATH:-}"
cd /data/users/dengcchi/hal_work/hal-harness/agents/SWE-agent-v1.0
METHOD="$1"; PORT="$2"; FILTER="$3"; OUT="$4"; NW="${5:-4}"
MODEL="${TS_MODEL:-anthropic/claude-opus-4-7}"   # <-- parameterized; default preserves Opus replay
CALL_LIMIT="${TS_CALL_LIMIT:-75}"
TEMP="${TS_TEMP:-0.0}"
# optional litellm model registry (for models not in litellm's default cost map, e.g. gpt-5-5).
# Empty for Anthropic -> no change to the frozen Opus/Sonnet/Haiku path.
REGISTRY_FLAG=""
if [[ -n "${TS_LITELLM_REGISTRY:-}" ]]; then
  REGISTRY_FLAG="--agent.model.litellm_model_registry=${TS_LITELLM_REGISTRY}"
fi
# optional parse function override (gpt path may need thought_action if function-calling unsupported)
PARSE_FLAG=""
if [[ -n "${TS_PARSE_FUNC:-}" ]]; then
  PARSE_FLAG="--agent.tools.parse_function.type=${TS_PARSE_FUNC}"
fi
export ANTHROPIC_API_KEY="shim" ANTHROPIC_BASE_URL="http://127.0.0.1:$PORT"
CONFIG="config/benchmarks/250225_anthropic_filemap_simple_review.yaml"
mkdir -p "$OUT"
echo "=== ARM $METHOD model=$MODEL port=$PORT out=$OUT nw=$NW call_limit=$CALL_LIMIT temp=$TEMP ==="
sweagent run-batch \
  --instances.type=swe_bench --instances.subset=verified --instances.split=test \
  --instances.evaluate=False --instances.deployment.container_runtime=podman \
  --instances.deployment.docker_args='--memory=10g' \
  --instances.filter="$FILTER" \
  --config="$CONFIG" \
  --agent.model.name="$MODEL" \
  --agent.model.api_base="http://127.0.0.1:$PORT" --agent.model.api_key="shim" \
  --agent.model.per_instance_cost_limit=0 --agent.model.per_instance_call_limit="$CALL_LIMIT" \
  --agent.model.temperature="$TEMP" --num_workers="$NW" \
  $REGISTRY_FLAG $PARSE_FLAG \
  --output_dir="$OUT"
_SWEA_RC=$?
echo "=== ARM $METHOD EXIT rc=$_SWEA_RC ==="
exit $_SWEA_RC
