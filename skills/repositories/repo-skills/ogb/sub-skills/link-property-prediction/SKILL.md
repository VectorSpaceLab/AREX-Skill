---
name: link-property-prediction
description: "Routes OGB link-prediction workflows for ogbl datasets, ranking
  metrics, and KG completion."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Link Property Prediction

Use this subskill for the link-property family: `ogbl-*` datasets, ranking
metrics, and knowledge-graph completion workflows.

## Use this subskill when

- The task names `LinkPropPredDataset`, `PygLinkPropPredDataset`,
  `DglLinkPropPredDataset`, or `ogbl-*`.
- The task asks for `hits@K`, `mrr`, or link-level `rocauc` evaluation.
- The task mentions `ogbl-collab`, `ogbl-ppa`, `ogbl-citation2`,
  `ogbl-ddi`, `ogbl-biokg`, `ogbl-wikikg2`, or `ogbl-vessel`.

## First decisions

1. Read [`references/workflows.md`](references/workflows.md) for the link
   prediction flow and metric-specific shapes.
2. Read [`references/api-reference.md`](references/api-reference.md) for the
   public class names, split structure, and evaluator inputs.
3. Read [`references/troubleshooting.md`](references/troubleshooting.md) when
   ranking shapes or top-k arrays fail validation.

## Main workflow

- Pick the exact `ogbl-*` dataset name.
- Load the dataset and inspect `get_edge_split()`.
- Decide whether the task uses hits@K, MRR, or ROC-AUC.
- Keep the positive and negative score shapes aligned before calling the
  evaluator.
- For knowledge-graph completion, pay attention to the rank-based inputs rather
  than treating the task like ordinary binary edge classification.

## Common routing choices

- `ogbl-collab` / `ogbl-ppa` -> graph link prediction baselines.
- `ogbl-citation2` -> citation ranking with MRR-style evaluation.
- `ogbl-biokg` / `ogbl-wikikg2` -> knowledge-graph completion.
- `ogbl-ddi` -> edge prediction with hits@20.
- `ogbl-vessel` -> ROC-AUC with the external contribution workflow.

## Optional backend note

PyG and DGL wrappers are optional. If they are not installed, the core OGB link
workflow still works through the library-agnostic loader.

## What not to do here

- Do not treat link prediction as a node-classification task.
- Do not feed score tensors with the wrong rank into the evaluator.
- Do not depend on the original checkout for final runtime guidance.

## Related references

- [`../../references/api-overview.md`](../../references/api-overview.md)
- [`../../references/dataset-catalog.md`](../../references/dataset-catalog.md)
- [`../../references/troubleshooting.md`](../../references/troubleshooting.md)
