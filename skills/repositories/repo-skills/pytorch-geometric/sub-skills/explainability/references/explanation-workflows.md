# Explanation Workflows

## Prepare a Model for Explanation

Before configuring `Explainer`, make the model's forward contract explicit:

1. Identify input style: `(x, edge_index)`, `(x, edge_index, batch)`, `(x, edge_index, edge_label_index)`, or `(x_dict, edge_index_dict, ...)`.
2. Confirm output shape: node-level `[num_nodes, classes]`, graph-level `[num_graphs, classes_or_targets]`, or edge-level `[num_edges_to_score, classes_or_scores]`.
3. Confirm output semantics: raw logits/scores, probabilities, or log-probabilities.
4. Put the model on the same device as the graph tensors.
5. For deterministic checks, call `model.eval()` and avoid dropout unless intentionally testing stochastic behavior.

If the model is not yet trained, you can still smoke-test the explainability plumbing with a tiny synthetic model. Do not interpret the masks as meaningful feature/edge explanations until the base model has learned a task.

## Homogeneous Node Classification

Use this when explaining one or more rows of a node-level model output.

```python
explainer = Explainer(
    model=model,
    algorithm=GNNExplainer(epochs=100),
    explanation_type='model',
    node_mask_type='attributes',
    edge_mask_type='object',
    model_config=dict(
        mode='multiclass_classification',
        task_level='node',
        return_type='log_probs',
    ),
)
explanation = explainer(data.x, data.edge_index, index=target_node)
```

Validation checklist:

- `explanation.node_mask.shape == data.x.shape` when `node_mask_type='attributes'`.
- `explanation.edge_mask.shape == (data.edge_index.size(1),)` when `edge_mask_type='object'`.
- `torch.isfinite(explanation.node_mask).all()` and `torch.isfinite(explanation.edge_mask).all()`.
- `target_node` is an integer or a tensor of valid output-row indices.

## Graph Classification or Regression

Graph-level models typically pool node embeddings with a `batch` vector. Pass every forward argument that the model requires:

```python
explanation = explainer(data.x, data.edge_index, batch=data.batch)
```

For graph regression:

```python
explainer = Explainer(
    model=model,
    algorithm=GNNExplainer(epochs=100),
    explanation_type='model',
    node_mask_type='attributes',
    edge_mask_type='object',
    model_config=dict(mode='regression', task_level='graph', return_type='raw'),
)
```

Do not call `fidelity` or `unfaithfulness` on regression explanations; those metrics are classification-focused.

## Phenomenon Explanations

Use `explanation_type='phenomenon'` when explaining a supplied target rather than the model's own predicted class.

```python
with torch.no_grad():
    target = model(data.x, data.edge_index).argmax(dim=-1)

explainer = Explainer(..., explanation_type='phenomenon', model_config=...)
explanation = explainer(data.x, data.edge_index, target=target, index=target_node)
```

Rules:

- `target` is required for phenomenon explanations.
- Compute model-derived targets under `torch.no_grad()` to avoid autograd reuse errors.
- For model explanations, omit `target`; passing it is ignored with a warning and can confuse later readers.

## Edge-Level or Link Explanation

For models whose `forward` scores edges or links, align `task_level='edge'` with the model signature.

```python
edge_label_index = torch.tensor([[0, 2, 3], [1, 3, 4]])
explanation = explainer(
    data.x,
    data.edge_index,
    edge_label_index=edge_label_index,
    index=torch.arange(edge_label_index.size(1)),
)
```

Validation checklist:

- `edge_label_index.shape == [2, num_scored_edges]`.
- The model returns one row per scored edge when `index` targets scored-edge outputs.
- Distinguish message-passing `edge_index` from supervision/scoring `edge_label_index`.

## Heterogeneous Explanation

Heterogeneous explanation uses typed dictionaries and returns `HeteroExplanation`.

```python
explainer = Explainer(
    model=hetero_model,
    algorithm=GNNExplainer(epochs=100),
    explanation_type='model',
    node_mask_type='attributes',
    edge_mask_type='object',
    model_config=dict(
        mode='multiclass_classification',
        task_level='node',
        return_type='raw',
    ),
)
explanation = explainer(
    hetero_data.x_dict,
    hetero_data.edge_index_dict,
    index=torch.tensor([0, 1]),
)
```

Inspect masks by type:

```python
node_masks = explanation.collect('node_mask')
edge_masks = explanation.collect('edge_mask')
```

If the hetero model only returns predictions for one node type, ensure the requested `index` addresses that output tensor, not a global node id from another type. Heterogeneous model construction and metadata debugging belong in the sibling heterogeneous-graphs sub-skill.

## Threshold and Top-k Workflows

Use thresholds to produce a compact explanation for reporting or comparison:

```python
explainer = Explainer(
    ...,
    threshold_config=('topk_hard', 10),
)
explanation = explainer(data.x, data.edge_index, index=target_node)
```

Choose thresholds deliberately:

- Use `'hard'` only when mask scores are calibrated enough for a fixed cutoff.
- Use `'topk'` when you want to preserve relative scores for the top entries.
- Use `'topk_hard'` when you need a binary selected subgraph or feature set.
- Choose `value` relative to mask size; for `value >= mask.numel()`, `topk` keeps the original whole mask and `topk_hard` converts the whole mask to ones.

## Safe Synthetic Verification Pattern

A robust tiny explanation check should:

1. Construct a small `Data(x, edge_index, y=...)` in memory.
2. Define a tiny `torch.nn.Module` using public PyG layers such as `GCNConv`.
3. Optionally train for a handful of CPU epochs if the case needs non-random predictions.
4. Configure `GNNExplainer(epochs=1..5)` for smoke checks.
5. Assert mask presence, shapes, finite values, and nonnegative sums.
6. Avoid downloads, datasets, GPUs, multiprocessing, network access, and writes outside a user-selected output path.

Use the bundled `scripts/tiny_explainer_smoke.py` as a minimal pattern for these checks.
