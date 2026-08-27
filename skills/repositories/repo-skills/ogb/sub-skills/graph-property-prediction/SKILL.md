---
name: graph-property-prediction
description: "Routes OGB graph-property workflows for ogbg datasets, molecular
  graphs, and code2 conversion."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Graph Property Prediction

Use this subskill for the graph-property family: `ogbg-*` datasets, molecular
classification/regression, `ogbg-code2`, `ogbg-ppa`, and SMILES-to-graph
conversion.

## Use this subskill when

- The task names `GraphPropPredDataset`, `PygGraphPropPredDataset`,
  `DglGraphPropPredDataset`, or `ogbg-*`.
- The task asks for graph-level evaluation metrics such as ROC-AUC, average
  precision, RMSE, accuracy, or code2 F1.
- The task mentions `smiles2graph`, `py2graph`, molecular datasets, or code to
  graph conversion.
- The task needs the PyG or DGL graph-property wrappers and the corresponding
  backend packages are installed.

## First decisions

1. Read [`references/workflows.md`](references/workflows.md) for the graph
   property task flow and dataset-specific gotchas.
2. Read [`references/api-reference.md`](references/api-reference.md) for the
   public class names, input/output shapes, and metric names.
3. Read [`references/troubleshooting.md`](references/troubleshooting.md) when a
   loader, evaluator, or conversion helper fails.
4. If you need a tiny sanity check for code2-style AST conversion, run
   [`scripts/py2graph-smoke.py`](scripts/py2graph-smoke.py).

## Main workflow

- Pick the dataset name from the exact `ogbg-*` catalog.
- Decide whether you need the library-agnostic loader or the PyG/DGL wrapper.
- Load the dataset and inspect `get_idx_split()`.
- Read the evaluator's expected input format before computing metrics.
- For molecular datasets, convert external molecules with `smiles2graph` rather
  than hand-assembling graph dictionaries.
- For `ogbg-code2`, treat the evaluator input as token sequences, not numeric
  labels.

## Common routing choices

- `ogbg-mol*` -> graph classification/regression with molecule graphs.
- `ogbg-ppa` -> graph classification with accuracy.
- `ogbg-code2` -> code-to-graph conversion and F1-style sequence evaluation.
- `smiles2graph` -> molecule-to-graph helper backed by rdkit.

## Optional backend note

PyG and DGL wrappers are optional. If the current environment does not have the
matching backend packages, route the task to the library-agnostic loader or ask
for the optional dependency rather than assuming the graph-property skill is
broken.

## What not to do here

- Do not route node/link/LSC dataset questions into this subskill just because
  they are graph-shaped.
- Do not tell the user to run the original repository's training scripts as the
  runtime answer.
- Do not depend on the original checkout for the final skill content.

## Related references

- [`../../references/api-overview.md`](../../references/api-overview.md)
- [`../../references/dataset-catalog.md`](../../references/dataset-catalog.md)
- [`../../references/troubleshooting.md`](../../references/troubleshooting.md)
- [`../../scripts/smiles2graph-smoke.py`](../../scripts/smiles2graph-smoke.py)
