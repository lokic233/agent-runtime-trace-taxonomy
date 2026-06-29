# qwen_validation_plan_v1.md — PRE-REGISTERED (Lane D + F)
## Solver: config/qwen32b_validation_solver.yaml (Qwen2.5-Coder-32B-Instruct-AWQ, vLLM 0.22, H100, frozen at Phase-2).
## SEAL: no Qwen trace generated or inspected until FREEZE_PHASE2_BEFORE_QWEN.md commit.
## Holdout: 60-100 held-out tasks x {DEFAULT + frozen candidate configs}. Prefer solver x task (and x repo) novelty:
##   no task that influenced feature design / thresholds / prompt / LoRA may appear. Since clean features were
##   designed on A/B/C/E/G/H over the SAME 500 SWE-bench Verified tasks, true task-novelty requires either
##   (a) a DISJOINT task set for Qwen, or (b) accept task-overlap and rely on SOLVER novelty (Qwen unseen) +
##   report the weaker transfer claim honestly. Decision recorded at Phase-2.
## Evaluate: DEFAULT, GLOBAL_BEST, TRACE_LENGTH_ONLY, DETERMINISTIC_TRACE_SELECTOR, PROMPTED_LOCAL_8B,
##   LORA_LOCAL_8B, RULES+LORA, ORACLE. No system revision after seeing Qwen results (revision => new holdout).
## STATUS: SEALED / PENDING (no Qwen agent traces exist yet; solver hosted, not yet run as an agent).
