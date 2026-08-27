---
name: nas
description: "Use NNI neural architecture search with model spaces, mutables,
  evaluators, strategies, execution engines, fixed-architecture export, and
  optional backend troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# NNI NAS

Use this sub-skill when the task is about NNI Neural Architecture Search: defining a model space, choosing mutation primitives, selecting an evaluator and strategy, launching a `NasExperiment`, exporting a fixed architecture, or diagnosing NAS import/runtime dependency failures.

## Route Here

- The user asks to build or adapt an NNI NAS `ModelSpace`, including DARTS-style cells, `LayerChoice`, `InputChoice`, `Repeat`, `Cell`, `nni.choice`, or mutable `torch.nn` modules.
- The user asks whether to use one-shot NAS or multi-trial NAS, or asks about `Random`, `GridSearch`, `RegularizedEvolution`, `TPE`, `PolicyBasedRL`, `DARTS`, `ENAS`, `GumbelDARTS`, `RandomOneShot`, or `Proxyless`.
- The user asks for evaluator selection, `FunctionalEvaluator`, PyTorch Lightning evaluators, `Classification`, `Regression`, `Lightning`, `LightningModule`, or serialization with `nni.trace`.
- The user asks how to export, freeze, retrain, or instantiate the best architecture after a NAS search using `export_top_models`, `model_context`, or `freeze`.
- The user hits `torch`, `pytorch_lightning`, `nni.nas.nn.pytorch`, `nni.nas.evaluator`, or `nni.nas.strategy` import errors while doing NAS work.

## Reroute

- Generic HPO experiment lifecycle, `nnictl`, search spaces for tuners, experiment YAML, training services, and trial-code wiring: use `../hpo-experiments/`.
- Pruning, quantization, `config_list`, `pruner`, `quantizer`, speedup, or compression evaluators: use `../model-compression/`.
- Standalone tracing, serialization utilities, concrete trace inspection, or feature utility usage without a NAS goal: use `../feature-engineering-and-utilities/`.

## Start With These References

- `references/workflows.md` for model-space, evaluator, strategy, experiment, and fixed-architecture workflows.
- `references/api-reference.md` for key public NAS concepts and object names, including optional dependency boundaries.
- `references/troubleshooting.md` for backend imports, evaluator mismatch, benchmark data, GPU/training cost, and model-space mutation errors.
- `scripts/check_nas_optional_deps.py` to safely inspect local optional dependency/import readiness without running NAS examples.

## Default Approach

1. Confirm the task is NAS, not generic HPO or compression.
2. Separate the NAS design into model space, evaluator, strategy, execution configuration, and export/retrain plan.
3. Prefer minimal, conceptual scaffolds unless the user explicitly asks to run a search; NAS execution can be expensive and often requires `torch`, datasets, Lightning, GPUs, and long training time.
4. Warn when a chosen strategy requires optional dependencies that may not be installed; do not imply `torch` or `pytorch_lightning` are present by default.
5. For fixed-architecture handoff, export an architecture dict and show how to instantiate or freeze the final model from that dict.
