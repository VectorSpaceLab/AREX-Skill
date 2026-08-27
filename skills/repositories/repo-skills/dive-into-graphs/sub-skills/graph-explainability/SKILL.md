---
name: graph-explainability
description: "Use DIG's xgraph stack for subgraph, edge, node, walk, and
  saliency explanations with SubgraphX, PGExplainer, GNNExplainer, GNN-LRP,
  DeepLIFT, GradCAM, FlowX, and explanation metrics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Graph Explainability

Use this sub-skill for DIG workflows that explain a trained GNN or evaluate explanation metrics.

## Include

- `dig.xgraph.dataset`: `BA_LRP`, `MarginalSubgraphDataset`, `MoleculeDataset`, `SentiGraphDataset`, `SynGraphDataset`.
- `dig.xgraph.method`: `DeepLIFT`, `FlowX`, `GNNExplainer`, `GNN_GI`, `GNN_LRP`, `GradCAM`, `PGExplainer`, `SubgraphX`, `MCTS`.
- `dig.xgraph.evaluation`: `XCollector`, `ExplanationProcessor`, `control_sparsity`.
- `dig.xgraph.models`: `GCN_2l`, `GIN_2l`, `load_model`, and the checkpoint compatibility helpers in `dig.xgraph.utils.compatibility`.
- Benchmark-style xgraph workflows using the bundled `benchmarks/xgraph` source evidence.

## Exclude

- Training new base GNNs from scratch: use the SSL or model-specific sub-skill that owns the model.
- 2D/3D molecular generation, OOD datasets, augmentation, fairness, or large-scale loaders: route elsewhere.

## Start Here

- Read `references/api-reference.md` for the explainers, metrics, and compatibility helpers.
- Read `references/workflows.md` for node, graph, and benchmark workflows.
- Read `references/troubleshooting.md` for checkpoint, mask, and model-config issues.
- Run `scripts/xgraph_metric_smoke.py` for a safe CPU-only metric smoke check.

## Core Workflows

- **Node or graph explanation**: build a trained model, choose an explainer, and request an explanation for a node, graph, or edge target.
- **Subgraph explanations**: use `SubgraphX`/`MCTS` when the question is which subgraph matters most.
- **Edge-mask metrics**: use `ExplanationProcessor` with `XCollector` and `control_sparsity` to compute fidelity and sparsity.
- **Checkpoint compatibility**: adapt saved model state dicts with `compatible_state_dict` when PyG versions change.

## Quick Validation

```bash
python scripts/xgraph_metric_smoke.py --help
python scripts/xgraph_metric_smoke.py
```
