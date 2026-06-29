# Qwen Held-Out Validation — STATUS: SEALED / PENDING

Qwen2.5-Coder-32B-Instruct-AWQ remains SEALED. No held-out validation was run because:
1. Phase-2 freeze is NOT reached (selector thresholds untuned, controllers unbuilt — FREEZE_PHASE2_BEFORE_QWEN.md).
2. No Qwen AGENT TRACES EXIST. The solver is hosted (devgpu014 vLLM:8001, served as Qwen2.5-Coder-32B-Instruct-4bit)
   but was never run as an agent over SWE-bench. The trace root __QWEN32B_4BIT_TRACE_ROOT__ is a placeholder.

Frozen solver config: config/qwen32b_validation_solver.yaml (real serving values captured from the live host;
nulls documented for fields that only become concrete when the agent harness is wired to the endpoint).
Held-out task pool (task-disjoint from the dev intervention pool): manifests/qwen_validation_tasks.jsonl (80 tasks).

To run (registered, gated on Phase-2 freeze): generate Qwen traces by running SWE-agent against the hosted
endpoint under the frozen config, then evaluate DEFAULT / GLOBAL_BEST / TRACE_LENGTH_ONLY /
DETERMINISTIC_TRACE_SELECTOR / PROMPTED_8B / LORA_8B / RULES+LORA / ORACLE. No system revision after seeing
results (revision → new untouched holdout).

QWEN_TRANSFER_VERDICT: PENDING (sealed; experiment registered, not run).
