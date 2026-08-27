---
name: explainability
description: "Configure PyTorch Geometric Explainer workflows, explanation
  algorithms, masks, thresholds, metrics, and explainability failure recovery."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Explainability

Use this sub-skill when configuring `torch_geometric.explain.Explainer`, choosing algorithms such as `GNNExplainer`, generating homogeneous or heterogeneous explanations, applying mask thresholds, evaluating explanation metrics, or recovering from explainability-specific configuration failures.

Do not use this sub-skill for training a production base model from scratch, designing generic GNN architectures, building heterogeneous graph schemas, sampling at scale, or dataset construction. Route those to sibling sub-skills when present, then return here once the model exposes a stable forward signature to explain.

## Start Here

- Read `references/explainer-api.md` when choosing `Explainer`, `GNNExplainer`, `Explanation`, `HeteroExplanation`, `ModelConfig`, mask types, threshold types, or metric APIs.
- Read `references/explanation-workflows.md` when implementing node, graph, link, or heterogeneous explanation workflows and deciding how to pass `target`, `index`, `batch`, or typed dictionaries.
- Read `references/troubleshooting.md` when errors mention `model_config`, missing mask types, invalid thresholds, unavailable masks, hetero routing, repeated backward passes, or slow explainer epochs.
- Run `scripts/tiny_explainer_smoke.py --epochs 2` to verify a CPU-only synthetic `GNNExplainer` path without downloads, GPUs, credentials, or long training.

## Common Tasks

- Wrap a trained PyG model with `Explainer(model, algorithm=GNNExplainer(...), explanation_type='model', model_config=..., node_mask_type=..., edge_mask_type=...)`.
- Match `model_config` to actual model output: `mode` is `binary_classification`, `multiclass_classification`, or `regression`; `task_level` is `node`, `edge`, or `graph`; `return_type` is `raw`, `probs`, or `log_probs`.
- Use at least one mask type: `node_mask_type='attributes'`, `'common_attributes'`, or `'object'`; `edge_mask_type='object'` or `None`.
- Explain a specific node or output row with `explanation = explainer(x, edge_index, index=node_index)` and inspect `explanation.available_explanations`, `explanation.node_mask`, and `explanation.edge_mask`.
- Evaluate classification explanations with metrics such as `fidelity(explainer, explanation)` or `unfaithfulness(explainer, explanation)` after confirming the explanation has the masks those metrics need.

## Safe Validation

```bash
python scripts/tiny_explainer_smoke.py --epochs 2
python scripts/tiny_explainer_smoke.py --epochs 1 --threshold-topk 3 --node-index 2
python scripts/tiny_explainer_smoke.py --help
```

Expected output includes available explanation mask names, node/edge mask shapes, finite mask sums, model prediction for the explained node, and `tiny_explainer_smoke: ok`.
