# FREEZE_PHASE2_BEFORE_QWEN.md — seal-before-unseal

## STATUS: NOT YET REACHED in this window. Qwen REMAINS SEALED.

Phase-2 freeze (the gate that unseals Qwen) requires ALL of these FROZEN:
  [x] feature definitions                  (FREEZE_PHASE1.md, FROZEN_V1)
  [x] detector thresholds                  (calibrated, FROZEN_V1)
  [x] correlation models                   (FROZEN_V1)
  [x] intervention configs (SPECS)         (runtime_config_registry_v1.yaml, implemented:false)
  [ ] selector rules (paired-tuned thresholds)        -> PENDING paired outcomes
  [ ] controller prompt (prompted 8B)                 -> NOT BUILT this window
  [ ] LoRA checkpoint                                  -> NOT TRAINED this window
  [x] risk-budget mapping (LOW/MED/HIGH)   (selector spec)
  [x] task inclusion criteria              (dataset_split.json; qwen tasks disjoint from dev pool)
  [x] outcome metrics                      (frozen)
  [ ] evaluation scripts (paired)          -> stubs only (PENDING)

## Qwen solver CONFIG is frozen (config/qwen32b_validation_solver.yaml). No Qwen agent trace exists yet
## (solver hosted on devgpu014 vLLM:8001, never run as an agent). __QWEN32B_4BIT_TRACE_ROOT__ not inspected.

## To reach Phase-2 freeze (future work, in order):
1. Implement the 3 intervention configs against the live SWE-agent runtime (registry implemented:true).
2. Run development paired experiments (80 tasks x 4 configs x >=1 dev solver) -> development_config_outcomes.jsonl.
3. Run interaction analysis -> tune + FREEZE selector thresholds; build prompted-8B + LoRA controllers.
4. Commit THIS file with commit SHA, artifact hashes, exact Qwen solver config, exact eval protocol,
   unseal timestamp. ONLY THEN generate Qwen traces (run SWE-agent vs hosted Qwen under frozen config)
   and access them.

unseal_timestamp: null  (SEALED)
