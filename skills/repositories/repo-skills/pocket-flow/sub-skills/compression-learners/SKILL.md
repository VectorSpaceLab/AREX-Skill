---
name: compression-learners
description: "Select and configure PocketFlow full-precision, distillation,
  pruning, sparsification, quantization, and RL compression learners."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# PocketFlow Compression Learners

Use this sub-skill when the user asks how to choose or configure a PocketFlow learner for full-precision baselines, model compression, distillation, pruning, sparsification, quantization, or reinforcement-learning-based hyperparameter search.

## Route first

- For `path.conf`, Python/TensorFlow setup, command preview, local/docker/seven launch modes, or AutoML text adapters, read [execution-config](../execution-config/SKILL.md).
- For adding a dataset or `ModelHelper`, read [custom-models-data](../custom-models-data/SKILL.md).
- For checkpoint export, TensorFlow Lite conversion, and inference benchmarks after training, read [deployment-conversion](../deployment-conversion/SKILL.md).

## Quick learner selection

1. Start with a full-precision baseline (`full-prec`) when no pretrained checkpoint exists or the user needs an accuracy reference.
2. Use [learner-catalog](references/learner-catalog.md) to map the requested compression method to the exact learner id and key flags.
3. Add `--enbl_dst` only when a teacher/original model path is available and the task benefits from distillation.
4. For automated layer-wise ratios or bit widths, read [rl-and-automl](references/rl-and-automl.md) before increasing rollout counts; RL search is expensive.
5. Generate a safe command preview with [build_learner_command.py](scripts/build_learner_command.py) and then route launch details to [execution-config](../execution-config/SKILL.md).
6. Treat full training/performance cases as long-running, data-dependent, and usually GPU-dependent. Do not run them without explicit user approval and available data/model paths.

## Main references

- [Learner catalog](references/learner-catalog.md) - learner ids, classes, algorithms, and important flags.
- [Workflows](references/workflows.md) - practical command patterns for baseline, pruning, sparsification, quantization, distillation, and evaluation.
- [RL and AutoML](references/rl-and-automl.md) - DDPG search, rollout counts, reward types, and AutoML bridge boundaries.
- [Troubleshooting](references/troubleshooting.md) - invalid learner ids, TensorFlow/contrib failures, missing checkpoints, data paths, GPU/runtime problems, and unstable hyperparameters.

## Boundaries and verification status

The generated skill verified TensorFlow 1.10 importability, `tf.contrib.lite`, learner id mapping, and source-level flag facts. It did not run full compression training or reproduce performance tables because those require datasets, checkpoints, long training, and often GPUs.

When users ask for real training, make the prerequisites explicit:

- A compatible TensorFlow 1.x environment.
- Dataset paths in `path.conf`.
- A selected run script/model helper.
- GPU/multi-GPU readiness when using the official launcher.
- Pretrained checkpoints for warm-start, distillation, or evaluation workflows.
