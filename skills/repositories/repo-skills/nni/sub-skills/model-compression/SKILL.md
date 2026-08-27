---
name: model-compression
description: "Use NNI model compression for pruning, quantization, distillation,
  evaluator wrapping, config_list authoring, validation, speedup, and export
  caveats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Model Compression

Use this sub-skill when the task is about NNI compression for PyTorch models: choosing a pruner, quantizer, distiller, evaluator wrapper, `config_list`, calibration or training contract, mask speedup, quantization export, or compression-specific troubleshooting.

## Route by Task

- **Author or validate `config_list`**: read [API reference](references/api-reference.md#config-list-schema) and run `scripts/validate_config_list.py` on JSON before proposing code.
- **Prune a model**: use [pruning workflow](references/workflows.md#pruning-workflow) and choose `LevelPruner`, norm/filter pruners, scheduled pruners, `SlimPruner`, `TaylorPruner`, or `MovementPruner` based on the model and need for training signals.
- **Quantize a model**: use [quantization workflow](references/workflows.md#quantization-workflow) and choose QAT/PTQ/DoReFa/BNN/LSQ variants by training budget and backend target.
- **Distill a model**: use [distillation workflow](references/workflows.md#distillation-workflow) for teacher/student layerwise losses with `DynamicLayerwiseDistiller` or `Adaptive1dLayerwiseDistiller`.
- **Wrap training**: use [evaluator workflow](references/workflows.md#evaluator-workflow) to select `TorchEvaluator`, `LightningEvaluator`, `TransformersEvaluator`, or `DeepspeedTorchEvaluator`.
- **Make compression physically faster**: use [speedup and export workflow](references/workflows.md#speedup-and-export-workflow) and distinguish simulated masks/quantization from structural or backend speedup.

## Boundaries

- Use this sub-skill for compression algorithm selection, compression API wiring, evaluator contracts, safe config validation, and compression troubleshooting.
- Route HPO experiment launch, tuners, assessors, training services, and `nnictl` concerns to `../hpo-experiments/`.
- Route NAS model space, evaluator, and strategy search design to `../nas/` unless the task is specifically compression evaluator wrapping.
- Route utility-only concrete tracing or feature-engineering helpers to `../feature-engineering-and-utilities/`.

## Required Safety Checks

- Do not run training, dataset download, notebook execution, TensorRT conversion, DeepSpeed launch, or native examples unless the user explicitly asks and the environment is prepared.
- Validate `config_list` JSON with the bundled script when the task only needs schema and selection sanity checks.
- Treat `nni.compression` import errors as optional dependency issues first: compression code requires `torch`, and some evaluators/backends require Lightning, Transformers, DeepSpeed, ONNX, TensorRT, or PyCUDA.
- Keep any runnable examples in the user's project, not in this skill tree; this sub-skill provides distilled contracts and local validation only.

## References

- [Compression workflows](references/workflows.md)
- [Compression API reference](references/api-reference.md)
- [Compression troubleshooting](references/troubleshooting.md)
