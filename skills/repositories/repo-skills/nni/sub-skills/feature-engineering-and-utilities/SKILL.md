---
name: feature-engineering-and-utilities
description: "Use NNI feature selectors and standalone utilities for tabular
  feature selection, trace serialization, concrete tracing, graph inspection,
  profiling, and optional dependency diagnosis."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Feature Engineering and Utilities

Use this sub-skill when the task is about NNI feature-engineering selectors or standalone utility modules rather than launching an experiment, designing NAS, or compressing a model.

## Route Here

- The user asks how to choose or use `GBDTSelector`, `FeatureGradientSelector`, or the base `FeatureSelector` for tabular feature selection.
- The user asks for input/output expectations around selector `fit`, `get_selected_features`, `transform`, `get_support`, grouped features, LightGBM feature importance, or gradient-based feature selection.
- The user asks how to use `nni.trace`, `nni.dump`, `nni.load`, `is_traceable`, or `nni.common.serializer` for traceable objects and configuration transfer.
- The user asks about `concrete_trace`, `ConcreteTracer`, `flop_count`, `counter_pass`, `build_graph`, or `build_module_graph` as standalone utilities.
- The user asks to diagnose missing `torch`, `lightgbm`, `sklearn`, `pandas`, or utility import failures without running examples or training.

## Reroute

- HPO experiment lifecycle, trial code, search spaces, tuners, assessors, training services, `Experiment`, or `nnictl`: use `../hpo-experiments/`.
- NAS model spaces, mutables, evaluators, strategies, `NasExperiment`, export, or fixed-architecture workflows: use `../nas/`.
- Pruning, quantization, distillation, `config_list`, pruner, quantizer, compression evaluator, speedup, or export workflows: use `../model-compression/`.

## Start With These References

- `references/workflows.md` for selector choice, serializer/trace usage, concrete trace, graph, and profiler workflows.
- `references/api-reference.md` for public import paths, core arguments, return values, and optional dependency boundaries.
- `references/troubleshooting.md` for LightGBM/sklearn/torch import failures, selector fit errors, serializer object path issues, and dynamic control-flow tracing caveats.
- `scripts/check_optional_utilities.py` to safely inspect local optional utility readiness without downloads, training, examples, or destructive writes.

## Default Approach

1. Confirm whether the task is tabular feature selection, trace serialization, concrete tracing, graph/profiler inspection, or dependency diagnosis.
2. Use `scripts/check_optional_utilities.py --json` before recommending a selector or concrete tracing path when optional dependencies are uncertain.
3. Keep feature engineering examples small and in-memory; do not run dataset downloads or repository examples unless the user explicitly asks.
4. Treat concrete tracing and profiling as PyTorch-only utilities that need representative dummy inputs and may flatten dynamic Python control flow.
5. Keep utility guidance separate from NAS and compression unless the user explicitly needs those workflows to consume traceable objects or traced graphs.
