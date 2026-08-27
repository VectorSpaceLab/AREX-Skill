---
name: node-property-prediction
description: "Routes OGB node-property workflows for ogbn datasets and
  node-level evaluators."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Node Property Prediction

Use this subskill for the node-property family: `ogbn-*` datasets, including
heterogeneous graphs and the one-graph node-classification loaders.

## Use this subskill when

- The task names `NodePropPredDataset`, `PygNodePropPredDataset`,
  `DglNodePropPredDataset`, or `ogbn-*`.
- The task asks for node-level ROC-AUC or accuracy evaluation.
- The task mentions `ogbn-mag`, `ogbn-products`, `ogbn-arxiv`,
  `ogbn-proteins`, or `ogbn-papers100M`.

## First decisions

1. Read [`references/workflows.md`](references/workflows.md) for the family
   workflow and hetero-graph caveats.
2. Read [`references/api-reference.md`](references/api-reference.md) for the
   public class names and split/label shapes.
3. Read [`references/troubleshooting.md`](references/troubleshooting.md) when a
   split, label, or import fails.
4. If the task also asks for packaging a new dataset, jump to
   `dataset-contribution` instead of stretching this subskill.

## Main workflow

- Pick the exact `ogbn-*` dataset name.
- Load the dataset and inspect `dataset[0]` plus `get_idx_split()`.
- Decide whether the task is homogeneous or heterogeneous.
- Use the evaluator's expected input format before building metrics.
- Treat `ogbn-mag` as a heterogeneous one-graph workflow.
- Treat `ogbn-papers100M` as the large binary/raw-format workflow.

## Common routing choices

- `ogbn-arxiv` -> citation graph node classification.
- `ogbn-products` -> large-scale product graph classification.
- `ogbn-proteins` -> binary node classification with ROC-AUC.
- `ogbn-mag` -> heterogeneous graph workflow with dict-valued labels/splits.
- `ogbn-papers100M` -> large binary dataset workflow.

## Optional backend note

PyG and DGL wrappers are optional. If they are not installed, the library-
agnostic loader remains the right path for the core OGB node workflow.

## What not to do here

- Do not route graph-property or link-property tasks here just because they
  also use graphs.
- Do not assume every `ogbn-*` dataset returns the same label shape.
- Do not depend on the original checkout for final runtime guidance.

## Related references

- [`../../references/api-overview.md`](../../references/api-overview.md)
- [`../../references/dataset-catalog.md`](../../references/dataset-catalog.md)
- [`../../references/troubleshooting.md`](../../references/troubleshooting.md)
