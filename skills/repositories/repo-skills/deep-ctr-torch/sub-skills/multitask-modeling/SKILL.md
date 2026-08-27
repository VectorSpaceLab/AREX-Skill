---
name: multitask-modeling
description: "Use DeepCTR-Torch SharedBottom, ESMM, MMOE, and PLE multi-task
  models with aligned labels, losses, metrics, and predictions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# multitask-modeling

Use this sub-skill when the task needs one DeepCTR-Torch model to optimize more than one target with the implemented multi-task classes: `SharedBottom`, `ESMM`, `MMOE`, or `PLE`.

## Route map

- Build `SparseFeat`, `DenseFeat`, `VarLenSparseFeat`, feature names, and `model_input` dictionaries with `../feature-column-inputs/SKILL.md` first.
- Use `references/mtl-models-and-training.md` for model selection, label matrix construction, compile/fit/predict flow, ByteRec-style two-target recipes, and metric handling.
- Use `references/api-reference.md` for exact constructor signatures, supported task types, loss strings, output shape, and parameter notes.
- Use `references/troubleshooting.md` before changing model code when target shape, task order, loss list, ESMM semantics, flattened metrics, or tiny batch behavior looks wrong.
- Run `scripts/mmoe_multitask_smoke.py --help` or the default smoke command to verify that a local installation can train an MMOE on inline two-label data and return predictions shaped `(n_samples, 2)`.
- Route single-output CTR/ranking models, single-target target arrays, persistence, and callbacks to `../single-task-modeling/SKILL.md` and shared training references.

## Operating rules

1. Multi-task labels are a two-dimensional NumPy-like matrix shaped `(n_samples, num_tasks)`. Column `i` must be the label for `task_names[i]`.
2. `model.predict(model_input, batch_size)` returns a NumPy array shaped `(n_samples, num_tasks)`. Prediction column `i` belongs to `task_names[i]`; evaluate each task column explicitly.
3. `task_types` length must equal `len(task_names)`. Supported values are `"binary"` and `"regression"` for `SharedBottom`, `MMOE`, and `PLE`; `ESMM` accepts two binary tasks only.
4. Compile multi-task models with a loss list of the same length and order as `task_names`, for example `['binary_crossentropy', 'binary_crossentropy']` or `['binary_crossentropy', 'mse']`.
5. Do not claim support for arbitrary custom task graphs: this package exposes the four fixed multi-task architectures above.
