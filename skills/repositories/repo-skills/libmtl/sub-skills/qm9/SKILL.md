---
name: qm9
description: "Routes LibMTL's QM9 graph-regression workflow."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# qm9

Use this sub-skill for the QM9 molecular property prediction workflow.

## Covers

- The QM9 example flow.
- PyG graph loading with `NNConv`, `Set2Set`, and `torch_geometric.loader`.
- The bundled split artifact and the `target` index list.
- Regression tasks that reuse the shared LibMTL trainer.

## Does not cover

- Image benchmarks.
- Office multi-input classification.
- PAWS-X tokenization and cached features.
- Generic custom method development unless the question is specifically about
  the QM9 workflow.

## When to use this sub-skill

Choose this route when the user asks things like:

- "How do I run QM9?"
- "What does the QM9 target list mean?"
- "Where do the graph loaders come from?"
- "How is the train/val/test split handled?"
- "Why does the example need torch-geometric?"

## Read next

- `../../references/configuration.md` for shared flags and trainer kwargs.
- `../../references/troubleshooting.md` for cross-cutting install and runtime
  failures.
- `references/workflows.md` for the command pattern.
- `references/task-contracts.md` for the target list, graph model wiring, and
  scheduler override.
- `references/data-layouts.md` for the expected data and split artifacts.
- `references/troubleshooting.md` for QM9-specific failures.

## Workflow

1. Confirm the QM9 dataset root.
2. Run `scripts/check_qm9_data.py` to confirm the bundled split artifact and
   optional dataset root.
3. Confirm that `torch_geometric` and the matching sparse wheels are installed.
4. Confirm the example is run from the QM9 workflow directory or that the split
   artifact path is passed correctly.
5. Confirm CUDA availability for the trainer.

## Critical constraints

- The workflow is graph-based and uses PyG-specific loaders.
- The split artifact is part of the benchmark recipe.
- The default target list contains 11 regression indices.
- The example still uses the shared LibMTL trainer, so the usual CUDA and
  string-name rules apply.

## Exit criteria

Leave this sub-skill when the user has the graph data location, split artifact,
command pattern, and the likely PyG failure modes.
