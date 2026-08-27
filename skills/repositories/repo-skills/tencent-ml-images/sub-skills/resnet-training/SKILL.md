---
name: resnet-training
description: "Guides Tencent ML-Images TensorFlow 1.x ResNet graph, pretraining,
  finetuning, flags, and training troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# ResNet Training

Use this sub-skill when the task is about the Tencent ML-Images ResNet model,
ML-Images multi-label pretraining, ImageNet finetuning, training flags,
checkpoint restore, or training/runtime diagnostics.

## Read first

- Read [references/training-workflows.md](references/training-workflows.md) for
  pretraining and finetuning recipes, required split directories, and safe
  command construction.
- Read [references/model-reference.md](references/model-reference.md) for the
  ResNet wrapper, supported depths, tensor shapes, data formats, loss behavior,
  and preprocessing facts.
- Read [references/cli-flags.md](references/cli-flags.md) when converting a
  shell example or user request into concrete flags.
- Read [references/troubleshooting.md](references/troubleshooting.md) before
  debugging TensorFlow 1.x, source syntax, checkpoint, GPU, or missing-data
  failures.

## Bundled helpers

- `scripts/build_train_command.py` prints a safe `train.py` command template for
  ML-Images pretraining. It does not run training.
- `scripts/build_finetune_command.py` prints a safe `finetune.py` command
  template for ImageNet finetuning. It does not run training and calls out
  legacy example-script misspellings.
- `scripts/resnet_graph_smoke.py` checks whether a user's local Tencent
  ML-Images checkout and TensorFlow 1.x runtime can import `flags` and
  `models.resnet` and build a small graph.

## Route by task

- **Need TFRecords or data layout first**: route to
  [../data-preparation/SKILL.md](../data-preparation/SKILL.md). Training reads
  split directories; it does not create TFRecords itself.
- **Build a pretraining command**: use `scripts/build_train_command.py`, then
  verify the data root has `train/` and `val/` shards and the class count is
  `11166`.
- **Build a finetuning command**: use `scripts/build_finetune_command.py`, then
  verify ImageNet-style scalar-label TFRecords, `class_num=1000`, and a
  compatible checkpoint.
- **Inspect the model graph**: read `references/model-reference.md`, then run
  `scripts/resnet_graph_smoke.py --repo-root <checkout>` inside a TensorFlow 1.x
  environment if a local checkout is available.
- **Diagnose failures**: start with `references/troubleshooting.md`. Many issues
  are legacy TensorFlow/Python compatibility rather than user data mistakes.

## Do not overclaim

- The public code is single-node and practical training is GPU/long-running.
  Do not present a CPU smoke or command render as evidence that full ML-Images
  pretraining was reproduced.
- The README notes that the authors' real ML-Images training used an internal
  distributed framework that is not released. The generated skill can guide the
  public single-node code only.
- Benchmark numbers and checkpoint links are provenance facts from the public
  README. Do not claim they were remeasured unless a separate experiment did so.
