# Explainability Troubleshooting

## `model_config` Mismatch

Symptoms:

- `ValueError` during `ModelConfig` construction.
- Metrics or targets look wrong even though masks are produced.
- Binary classification with `return_type='log_probs'` fails.
- Regression configured with `return_type='probs'` or `return_type='log_probs'` fails.

Fix:

1. Inspect the model output before building the explainer:

   ```python
   with torch.no_grad():
       out = model(data.x, data.edge_index)
   print(out.shape, out[:2])
   ```

2. Set `mode` to the task semantics, not merely the tensor shape.
3. Set `task_level` to the output row meaning: node, edge, or graph.
4. Set `return_type` to actual values returned by `forward`:
   - logits/scores: `raw`
   - probabilities from `sigmoid` or `softmax`: `probs`
   - log probabilities from `log_softmax`: `log_probs`

Rules enforced by PyG 2.9.0:

- Regression must use `return_type='raw'`.
- Binary classification supports `raw` or `probs`, not `log_probs`.
- Multiclass classification supports `raw`, `probs`, and `log_probs`.

## Missing or Invalid Mask Types

Symptoms:

- `ValueError: Either 'node_mask_type' or 'edge_mask_type' must be provided`.
- `ValueError` says `edge_mask_type` needs to be `None` or `'object'`.
- `explanation.available_explanations` lacks the mask a later step expects.

Fix:

- Set at least one mask: `node_mask_type='attributes'` and/or `edge_mask_type='object'`.
- Use feature-level node masks (`'attributes'` or `'common_attributes'`) when feature importance or `unfaithfulness(top_k=...)` is required.
- Use `node_mask_type='object'` only when per-node importance is sufficient.
- Do not request edge feature masks through `edge_mask_type`; PyG's explainer edge mask is per edge.

## Threshold Misuse

Symptoms:

- `ValueError` says hard threshold value must be between 0 and 1.
- `ValueError` says top-k value needs to be a positive integer.
- A top-k explanation unexpectedly keeps every entry.

Fix:

- For `threshold_config=('hard', value)`, choose a float in `[0, 1]`.
- For `('topk', value)` or `('topk_hard', value)`, choose a positive integer.
- Remember top-k is applied over the flattened mask; if `value >= mask.numel()`, `topk` keeps all original entries and `topk_hard` marks all entries selected.
- Apply thresholding after generating masks if you need to compare raw and thresholded explanations:

  ```python
  raw = explainer(data.x, data.edge_index, index=0)
  hard = raw.threshold('topk_hard', 5)
  ```

## Phenomenon Target Errors

Symptoms:

- `ValueError` says target has to be provided for explanation type `phenomenon`.
- Runtime error mentions backward through the graph a second time.

Fix:

- Pass `target=` for `explanation_type='phenomenon'`.
- If the target comes from the model, compute it under `torch.no_grad()`:

  ```python
  with torch.no_grad():
      target = model(data.x, data.edge_index).argmax(dim=-1)
  explanation = explainer(data.x, data.edge_index, target=target, index=0)
  ```

- For `explanation_type='model'`, do not pass `target`; the explainer derives the target from the model prediction.

## Heterogeneous Routing Problems

Symptoms:

- `HeteroExplanation` exists but masks are missing for an expected node or edge type.
- `index` explains the wrong output rows.
- The model fails when called with `x_dict` and `edge_index_dict`.

Fix:

- Confirm the model forward signature accepts typed dictionaries:

  ```python
  out = model(hetero_data.x_dict, hetero_data.edge_index_dict)
  ```

- Inspect typed masks with `explanation.collect('node_mask')` and `explanation.collect('edge_mask')` instead of homogeneous attributes.
- Ensure `index` targets rows of the model output tensor. It is not automatically a typed node id unless the model output is arranged that way.
- If the failure is about metadata, missing reverse relations, `to_hetero`, or `HeteroConv`, use the heterogeneous-graphs sub-skill first.

## Slow or Expensive Explanations

Symptoms:

- `GNNExplainer` takes too long.
- A notebook or CI check hangs on large graphs.
- GPU memory grows unexpectedly.

Fix:

- Use `GNNExplainer(epochs=1..5)` for smoke tests and CI checks.
- Explain a single `index` or a small tensor of output rows, not all nodes.
- Use a sampled subgraph or preselected neighborhood for exploratory debugging.
- Run on CPU for tiny synthetic validation; reserve GPU runs for real workloads.
- Avoid dataset downloads and long base-model training in explainability checks.

## Metric Failures

Symptoms:

- `fidelity` or `unfaithfulness` raises on regression.
- `unfaithfulness(top_k=...)` raises for object-level node masks.
- `groundtruth_metrics` fails because an optional dependency is missing.

Fix:

- Use `fidelity` and `unfaithfulness` only for classification configs.
- For top-k feature unfaithfulness, configure `node_mask_type='attributes'` or `'common_attributes'`.
- Install or skip `torchmetrics` before using `groundtruth_metrics`.
- Always check mask shape and finiteness before interpreting metric values.

## Visualization Failures

Symptoms:

- Feature visualization raises because `node_mask` is missing or has shape `[num_nodes, 1]`.
- Graph visualization raises because `edge_mask` is missing.
- Plotting fails in headless or minimal environments.

Fix:

- For feature importance plots, request a feature-level node mask such as `node_mask_type='attributes'`.
- For graph/subgraph visualization, request `edge_mask_type='object'`.
- In automation, avoid plotting and assert numeric mask properties instead.
- If writing plot files, make the output path explicit and user-controlled.
