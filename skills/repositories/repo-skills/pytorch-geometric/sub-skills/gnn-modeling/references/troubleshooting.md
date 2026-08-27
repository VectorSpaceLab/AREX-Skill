# GNN Modeling Troubleshooting

Use this guide when PyTorch Geometric model construction, training, metrics, compilation, or tiny smoke tests fail.

## `edge_index` Shape Or Dtype Failures

Symptoms:

- Indexing errors inside convolution layers.
- Messages about expected `LongTensor` indices.
- Output node count is wrong or an index is out of bounds.

Checks:

```python
assert edge_index.dtype == torch.long
assert edge_index.dim() == 2 and edge_index.size(0) == 2
assert edge_index.numel() == 0 or int(edge_index.max()) < x.size(0)
assert edge_index.numel() == 0 or int(edge_index.min()) >= 0
```

Fixes:

- Construct `edge_index` as `torch.tensor([[src...], [dst...]], dtype=torch.long)`.
- If starting from edge pairs shaped `[num_edges, 2]`, transpose and call `.contiguous()`.
- Move `edge_index` to the same device as `x` and the model.
- Preserve directedness intentionally; add reverse edges explicitly when an undirected graph is required.

## In/Out Channel Mismatch

Symptoms:

- Matrix multiplication shape errors.
- `GATConv` output has more channels than the next layer expects.
- Bipartite `SAGEConv` input fails with tuple feature shapes.

Fixes:

- Set the first layer `in_channels` to `data.num_node_features` or `x.size(-1)`.
- For `GATConv(out_channels=c, heads=h, concat=True)`, next layer input is `c * h`.
- For `GATConv(..., concat=False)`, next layer input is `c`.
- For bipartite use, pass `SAGEConv((src_channels, dst_channels), out_channels)` and call with `(x_src, x_dst)`.
- Add one forward-pass assertion immediately after each block while developing.

## Cached Convolution Misuse

`GCNConv(cached=True)` caches normalized graph structure. It is appropriate only when the graph topology is fixed across forwards, such as full-batch transductive training on one graph.

Do not use `cached=True` when:

- Training with mini-batches or neighbor sampling.
- Changing `edge_index` between epochs or batches.
- Using data augmentation that changes edges.
- Switching between train/validation/test graphs with different topology.

Fix: instantiate `GCNConv(..., cached=False)` unless you have proved topology is constant.

## Loss Or Gradient Problems

Symptoms:

- `loss` is `nan` or `inf`.
- Parameters do not update.
- Accuracy stays constant on a tiny fixture.

Checks:

```python
assert torch.isfinite(loss)
loss.backward()
assert any(p.grad is not None for p in model.parameters() if p.requires_grad)
```

Fixes:

- Use `model.train()` during optimization and `model.eval()` during evaluation.
- Call `optimizer.zero_grad()` before `backward()`.
- Use `F.cross_entropy(logits[mask], y[mask])` with class labels of dtype `torch.long`.
- Use `binary_cross_entropy_with_logits` for binary link logits; do not apply sigmoid twice.
- Reduce learning rate or remove dropout while debugging a tiny synthetic graph.

## Torch Compile Unsupported Or Dynamic Paths

Symptoms:

- `torch.compile` raises graph-break or dynamic-shape errors.
- Compiled model recompiles often on variable-size batches.
- Full-graph compilation fails around pooling or self-loop utilities.

Fixes:

- First prove the model in eager mode.
- Use `torch.compile(model, dynamic=True)` for variable graph sizes.
- Use `fullgraph=True` only to diagnose graph breaks.
- Move graph topology preprocessing outside `forward` when possible.
- Precompute self-loops or normalization with transforms, then configure layers so they do not alter topology inside `forward`.
- Pass explicit size information to pooling when supported.
- If a path remains unsupported, keep compile optional and fall back to eager execution.

## Optional Sparse Extension Absence

PyG can run many basic neural network layers with PyTorch-only tensors, but some sparse, sampling, or accelerated paths require optional packages such as `pyg-lib`, `torch-sparse`, `torch-scatter`, or related extensions.

Symptoms:

- Import errors for optional sparse libraries.
- Sparse tensor examples fail while dense `edge_index` examples work.
- Runtime messages mention unavailable sampler or sparse backends.

Fixes:

- Keep tiny modeling smoke tests on dense `edge_index` tensors.
- Use public `edge_index` APIs unless a sparse backend is explicitly required.
- Guard optional sparse imports and print actionable messages.
- Do not make generated scripts download or install optional packages automatically.
- Route large-scale sampling/backend troubleshooting to the scalable or loader sub-skills when present.

## Over-Smoothing And Deep GNN Instability

Symptoms:

- Node embeddings become nearly identical after many layers.
- Training accuracy improves but validation degrades.
- Deeper GCN/SAGE stacks underperform shallow baselines.

Fixes:

- Start with 2 to 3 message-passing layers.
- Add residual connections, normalization, dropout, or Jumping Knowledge when increasing depth.
- Use `decomposed_layers` for memory reduction only after correctness; it is not a cure for over-smoothing.
- Monitor per-layer embedding variance on a small validation graph.
- Compare against a shallow baseline before adding attention, pooling, or compile.

## Pooling And Batch Vector Errors

Symptoms:

- Graph classification output has node count instead of graph count.
- Pooling raises shape or device errors.
- A single graph accidentally pools all nodes into an unexpected number of graphs.

Fixes:

- Pass `batch` from a PyG mini-batch object into `global_mean_pool`, `global_add_pool`, or `global_max_pool`.
- For a single graph without a loader, create `batch = x.new_zeros(x.size(0), dtype=torch.long)`.
- Assert output shape after pooling: `[num_graphs, hidden_channels]`.
- Keep `batch` on the same device as node embeddings.

## Metrics Misconfiguration

Symptoms:

- Link prediction metric values are impossible or constant.
- Metric input shape errors.
- Accuracy is computed over validation/test labels during training.

Fixes:

- Separate training loss computation from validation/test metric computation.
- For node classification, mask predictions and labels with the same boolean mask.
- For link prediction, verify whether the metric expects logits, probabilities, ranks, positive scores, negative scores, labels, or top-k settings.
- Assert score and label tensors have matching first dimensions before passing to a metric.
