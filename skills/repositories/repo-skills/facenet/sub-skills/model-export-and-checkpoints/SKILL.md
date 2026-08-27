---
name: model-export-and-checkpoints
description: "Load Facenet checkpoint directories or frozen graphs, inspect
  variables, and export frozen models."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Facenet Model Export and Checkpoints

Use this sub-skill when the task is about loading a Facenet model, inspecting checkpoint files, choosing between `.meta`/checkpoint directories and `.pb` frozen graphs, or exporting a frozen graph.

## When to read

- The user asks how to load a trained Facenet model path.
- A workflow fails because a model directory has missing or multiple `.meta` files.
- The user needs to freeze a checkpoint into a GraphDef `.pb` file.
- Tensor names such as `input:0`, `embeddings:0`, `phase_train:0`, or `label_batch` are missing or mismatched.
- The user wants to list checkpoint variables or understand which file in a model directory is used.

## Core behaviors

- `facenet.load_model(model, input_map=None)` loads either a frozen `.pb` graph or a checkpoint directory.
- `facenet.get_model_filenames(model_dir)` expects one `.meta` file and a checkpoint state or `model-*.ckpt-*` file.
- `facenet.list_variables(filename)` lists variable names in a checkpoint file.
- `src/freeze_graph.py` imports a checkpoint graph, restores weights, converts variables to constants, and writes a frozen `.pb` graph.

## Workflow

1. Determine whether the user has a checkpoint directory or a frozen graph.
2. Read [`references/model-files.md`](references/model-files.md) for path formats and tensor-name expectations.
3. Use [`scripts/inspect_model_dir.py`](scripts/inspect_model_dir.py) to summarize `.meta` and checkpoint files.
4. Build a freeze command with [`scripts/build_freeze_graph_command.py`](scripts/build_freeze_graph_command.py) when exporting a `.pb` graph.
5. If the model path is invalid, check checkpoint selection, tensor names, and `tf.train.get_checkpoint_state()` behavior before changing workflows.

## Common model-file conventions

- Checkpoint directory: one `.meta` plus checkpoint files such as `model-<name>.ckpt-<step>`.
- Frozen graph: single `.pb` file accepted directly by `facenet.load_model()`.
- Source workflows often expect the graph tensors `input:0`, `embeddings:0`, and `phase_train:0`.
- `freeze_graph.py` also preserves `label_batch` and `Logits`-related nodes when exporting.

## Export checklist

Before freezing, confirm the model directory has the intended graph/checkpoint pair, choose a new `.pb` output path, and preserve the original checkpoint directory. After export, inspect the graph's input/output tensor names before passing it to comparison, classifier, or LFW evaluation.

## Route onward

- For face comparison and classifier workflows, continue with [`../embeddings-and-classification/SKILL.md`](../embeddings-and-classification/SKILL.md).
- For training, continue with [`../training/SKILL.md`](../training/SKILL.md).
- For LFW evaluation, continue with [`../evaluation/SKILL.md`](../evaluation/SKILL.md).

## Troubleshooting

Read [`references/troubleshooting.md`](references/troubleshooting.md) for missing `.meta` files, bad checkpoint paths, tensor-name mismatches, and `freeze_graph` output errors.
