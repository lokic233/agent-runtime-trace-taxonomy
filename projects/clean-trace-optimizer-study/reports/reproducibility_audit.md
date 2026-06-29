# Reproducibility Audit

## Artifact hashes (sha256, first 16)

| file | sha256:16 | exists |
|---|---|---|
| src/clean_loader.py | c78b15d9c418d86a | yes |
| src/clean_classify.py | 90ff305936503fd4 | yes |
| src/extract_clean_trace_features.py | 571baec40bf408d2 | yes |
| src/build_trace_inventory.py | d20fec9cc0d2fc39 | yes |
| src/build_clean_audit_sample.py | 7f770d46f34f4951 | yes |
| src/calibrate_clean_features.py | 532ff22db76a747e | yes |
| src/build_baseline_feature_table.py | 040a0eb19cc974ec | yes |
| src/run_correlation_analysis.py | a21a927ff834c4b9 | yes |
| src/skeptic_review.py | bc723af76b448e8a | yes |
| src/integrate_semantic_annotations.py | f635c7789a1b257c | yes |
| features/clean_trace_feature_spec_v1.yaml | 9c771014647e6da7 | yes |
| config/trace_sources.yaml | 34844b319b5833cb | yes |
| config/qwen32b_validation_solver.yaml | a7aba917cbe26bb9 | yes |
| config/runtime_config_registry_v1.yaml | 111213d15c7139e5 | yes |
| manifests/development_trace_inventory.jsonl | b96f01524fc49e42 | yes |
| data/baseline_trace_feature_table.parquet | c507c6bd8b446be7 | yes |

## Environment
- analysis node: cli:devvm14382 | python Python 3.12.13+meta
- libs: numpy/pandas/scipy/sklearn/statsmodels/matplotlib (statsmodels pip-installed to --user)
- raw opus traces: cli:devgpu014 (features extracted there, JSONL pulled to analysis node)

## Determinism
- seeds: sampling SEED=20260628; bootstrap np.seed=20260628; GroupKFold deterministic by task_id.
- feature extraction is pure-deterministic over raw text (hashes/regex); re-running reproduces JSONL.

## Parser consistency
- 4 layouts (classic_traj, mini-swe-agent, openhands dict, openhands list) handled by clean_loader;
  0 parser failures across 3432 traces (reports/trace_inventory.md).