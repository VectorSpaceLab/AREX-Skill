# Shared API Overview

Read this before routing a mixed task. Detailed constructor notes belong to
[graph-layers](../sub-skills/graph-layers/SKILL.md); task data and metrics belong
to the point-cloud, OGB, and PPI routes.

## Package surfaces

| Surface | Use |
|---|---|
| `gcn_lib.sparse` | Sparse node features, static/dynamic graph convolutions, GENConv, KNN, residual/plain/dense blocks, and OGB/PPI-style graphs. |
| `gcn_lib.dense` | Dense point-cloud features with shape `(B,C,N,1)`, batched KNN, Edge/MR graph convolution, and dense dynamic blocks. |
| `eff_gcn_modules.rev` | Additive coupling, invertible checkpoint wrapper, shared dropout, and reversible GCN/GAT/GEN blocks. |
| `utils.ckpt_util` | Historical checkpoint save/load conventions; always verify the owning workflow's expected state-dict keys. |
| `utils.data_util` | Point-cloud augmentation, graph partition helpers, PartNet data class, and OGB atom/bond feature encoders. |
| `utils.metrics` / `utils.loss` | Average meters, PSNR helper, and smoothed cross-entropy; PPI and OGB tasks may use their own evaluator semantics. |

## Layout and output contracts

- Sparse graph layers take `x` with shape `(N,C)` and `edge_index` with shape
  `(2,E)`. Dynamic sparse paths can take a node-level `batch` vector and return
  `(features, batch)` from their block wrappers.
- Dense point-cloud layers take `(B,C,N,1)` and dense neighbor indices with
  shape `(2,B,N,K)`. Dense classification pools to one logit vector per cloud;
  segmentation preserves the point axis.
- `GENConv` aggregates messages and then applies an MLP to a residual sum. Its
  aggregation family includes ordinary `add`/`mean`/`max` and learned or fixed
  softmax/power variants, subject to the installed source/API version.
- Reversible coupling requires channel divisibility by `group` and a valid
  deterministic inverse. Extra tensor arguments are chunked along the selected
  split dimension by `GroupAdditiveCoupling`; verify their intended shape.

## Cross-cutting selection

- Choose dense versus sparse from point count, equal-size batching, and memory;
  do not flatten one layout into the other without changing the model contract.
- Choose OGB partitioning for large node graphs only when the task's data and
  evaluator support it; graph-batched molecular tasks use different pooling and
  feature encoders.
- PPI is a PyG multilabel node task with micro-F1 conventions, not OGB proteins.
- Use the owning reference for flags. Historical README defaults and current
  parser defaults can differ.
