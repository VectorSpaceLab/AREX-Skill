# Explainer API Reference

## Core Imports

```python
import torch
from torch_geometric.explain import Explainer, GNNExplainer
from torch_geometric.explain import Explanation, HeteroExplanation
from torch_geometric.explain import fidelity, unfaithfulness, groundtruth_metrics
```

`Explainer` in PyG 2.9.0 has the constructor shape:

```python
Explainer(
    model,
    algorithm,
    explanation_type,
    model_config,
    node_mask_type=None,
    edge_mask_type=None,
    threshold_config=None,
)
```

`GNNExplainer` accepts `epochs=100`, `lr=0.01`, and additional keyword arguments. Keep `epochs` tiny for smoke checks and raise it only for real analysis.

## Configuration Contracts

`explanation_type` controls the objective:

- `'model'`: explain the model prediction. Do not pass `target`; the explainer infers labels from the model output.
- `'phenomenon'`: explain a supplied label or target. You must pass `target=` when calling the explainer.

`model_config` must describe the actual model output:

```python
model_config = dict(
    mode='multiclass_classification',
    task_level='node',
    return_type='log_probs',
)
```

Valid `mode` values are `binary_classification`, `multiclass_classification`, and `regression`. Valid `task_level` values are `node`, `edge`, and `graph`. Valid `return_type` values are `raw`, `probs`, and `log_probs`; regression models use `raw`, and binary classification supports only `raw` or `probs`.

## Mask Types

At least one of `node_mask_type` or `edge_mask_type` must be set.

Node mask choices:

- `None`: no node mask.
- `'object'`: one importance value per node, with shape `[num_nodes, 1]`.
- `'common_attributes'`: one feature importance vector shared across nodes, with shape `[1, num_features]`.
- `'attributes'`: one importance value per node feature, with shape `[num_nodes, num_features]`.

Edge mask choices:

- `None`: no edge mask.
- `'object'`: one importance value per edge, with shape `[num_edges]`.

Do not set `edge_mask_type='attributes'` or `edge_mask_type='common_attributes'`; PyG validates edge masks as `None` or `'object'` only.

## Calling the Explainer

Homogeneous node classification:

```python
explainer = Explainer(
    model=model,
    algorithm=GNNExplainer(epochs=50),
    explanation_type='model',
    node_mask_type='attributes',
    edge_mask_type='object',
    model_config=dict(
        mode='multiclass_classification',
        task_level='node',
        return_type='log_probs',
    ),
)
explanation = explainer(data.x, data.edge_index, index=10)
```

Graph-level models usually need `batch=` if their forward method pools by graph:

```python
explanation = explainer(data.x, data.edge_index, batch=data.batch)
```

Edge-level models usually need `edge_label_index=` if the forward method scores selected links:

```python
explanation = explainer(
    data.x,
    data.edge_index,
    index=torch.arange(edge_label_index.size(1)),
    edge_label_index=edge_label_index,
)
```

Heterogeneous models use dictionaries:

```python
explanation = explainer(
    hetero_data.x_dict,
    hetero_data.edge_index_dict,
    index=torch.tensor([1, 3]),
)
```

The result is `Explanation` for homogeneous tensor inputs and `HeteroExplanation` for dictionary inputs.

## Explanation Objects

Useful fields and methods:

- `explanation.available_explanations`: mask names present, such as `['node_mask', 'edge_mask']`.
- `explanation.node_mask`: homogeneous node mask when requested.
- `explanation.edge_mask`: homogeneous edge mask when requested.
- `hetero_explanation.collect('node_mask')`: node masks by node type.
- `hetero_explanation.collect('edge_mask')`: edge masks by edge type.
- `explanation.validate()` or `explanation.validate_masks()`: check mask dimensions.
- `explanation.get_explanation_subgraph()`: keep nodes/edges with nonzero attribution.
- `explanation.get_complement_subgraph()`: remove attributed nodes/edges.

Visualization helpers exist, but they may require optional plotting or graph visualization packages. For robust automation, prefer numeric assertions on mask shapes, finiteness, and selected top-k indices.

## Thresholds

`threshold_config` can be omitted or supplied as a tuple/dict accepted by PyG's config casting:

```python
threshold_config=('topk_hard', 5)
# or
threshold_config=dict(threshold_type='hard', value=0.5)
```

Threshold types:

- `'hard'`: values above `value` become `1`, others become `0`; `value` must be between `0` and `1`.
- `'topk'`: keeps the top `value` mask entries with original scores; `value` must be a positive integer.
- `'topk_hard'`: keeps the top `value` entries and sets them to `1`; `value` must be a positive integer.

Thresholding is global over each flattened mask. If top-k is at least the mask size, `'topk'` returns the original mask and `'topk_hard'` returns an all-ones mask. On heterogeneous explanations, thresholding applies per typed mask store.

## Metrics

Classification metrics:

```python
from torch_geometric.explain import fidelity, unfaithfulness

pos_fidelity, neg_fidelity = fidelity(explainer, explanation)
score = unfaithfulness(explainer, explanation)
```

`fidelity` and `unfaithfulness` are not defined for regression model configs. `unfaithfulness(top_k=...)` requires a feature-level node mask, not `node_mask_type='object'`.

Ground-truth mask comparison:

```python
from torch_geometric.explain import groundtruth_metrics

accuracy, recall, precision, f1, auroc = groundtruth_metrics(
    pred_mask=explanation.edge_mask,
    target_mask=known_edge_mask,
)
```

`groundtruth_metrics` uses `torchmetrics`; ensure that optional dependency is installed before relying on it in validation code.
