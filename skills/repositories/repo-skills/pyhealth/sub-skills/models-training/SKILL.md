---
name: models-training
description: "Guides PyHealth model-family selection, dataset and vocabulary
  contracts, Trainer training/inference, device selection, checkpoints, and safe
  small-scale workflow adaptation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# PyHealth models and training

Use this route after a task dataset emits validated samples. Read [model
overview](references/model-overview.md) for family selection and [API reference](references/api-reference.md)
for current signatures.

## Workflow

1. Confirm task mode, input keys, processor output schemas, vocabulary sizes,
   label names, and a patient-safe split in [clinical-tasks](../clinical-tasks/SKILL.md)
   and [data-pipelines](../data-pipelines/SKILL.md).
2. Choose a model family that consumes those fields: classical, sequence,
   recurrent/attention, transformer, graph, image/signal, multimodal, or
   generative. Instantiate it with the task dataset where required.
3. Run `scripts/check_model_contract.py` or a one-batch CPU forward pass. Do not
   download weights or start a large run in a smoke test.
4. Construct `Trainer(model, device=..., output_path=...)`; use explicit device
   and bounded `epochs`, `steps_per_epoch`, and output paths.
5. Train with validation and a mode-appropriate `monitor`; call `evaluate` or
   `inference` and route output arrays to [evaluation](../evaluation-interpretability/SKILL.md).
6. Keep `last.ckpt`/`best.ckpt` provenance with model/task/config/device. Route
   text, image, signal, and external-weight constraints to
   [medical-code-text](../medical-code-text/SKILL.md).

CPU is the baseline; CUDA is optional and must be independently probed. Read
[workflows](references/workflows.md) and [troubleshooting](references/troubleshooting.md)
before changing a model or checkpoint.
