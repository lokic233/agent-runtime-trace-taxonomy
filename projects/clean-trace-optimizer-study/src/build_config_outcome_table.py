#!/usr/bin/env python3
"""build_config_outcome_table.py — assemble development_config_outcomes.jsonl from PAIRED runs.
STATUS: PENDING. No paired runs executed (requires re-running SWE-agent x tasks x configs vs a live
solver). Schema fixed (Section 18). Rows written ONLY with provenance=EMPIRICAL from real runs.
This script intentionally produces NO synthetic rows."""
if __name__=="__main__":
    print("PENDING: no paired config outcomes. Run paired SWE-agent experiments first "
          "(manifests/development_intervention_tasks.jsonl + config/runtime_config_registry_v1.yaml).")
