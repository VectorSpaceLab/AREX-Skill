# Loader and Sampling Troubleshooting

Start by identifying whether the failure is ordinary mini-batching (`DataLoader`) or neighborhood/link sampling (`NeighborLoader`/`LinkNeighborLoader`). `DataLoader` should work with the core installed package; neighborhood and link sampling may require optional backends such as `pyg-lib` or `torch-sparse` when the loader is iterated.

## `DataLoader` batch vectors are missing or wrong

Symptoms:

- Expected `x_s_batch`, `x_t_batch`, or another per-attribute assignment vector is absent.
- Graph pooling mixes nodes from different embedded graphs.
- Custom fields with `index` in their name are unexpectedly incremented.

Fixes:

- Add `follow_batch=["attribute_name"]` for every node-feature-like tensor that needs a graph assignment vector.
- Use the built-in top-level `batch.batch` only for the primary `x` tensor; use `*_batch` for secondary node tensors.
- Rename non-index attributes that contain `index`, or override `Data.__inc__` for that key.
- For graph-level vectors, override `Data.__cat_dim__` to return `None` so a new batch dimension is created.
- Validate `batch.ptr`, `batch.batch`, and `batch.edge_index.max() < batch.num_nodes` on a tiny fixture before using the dataset at scale.

## `exclude_keys` removed needed data

Symptoms:

- Model receives `None` or raises an attribute error for a field that exists in individual examples.
- Loss cannot access labels or masks after batching.

Fixes:

- Keep `exclude_keys` limited to bulky metadata, raw strings, debug payloads, or fields not used by the transform/model/loss.
- Inspect one batch with `print(batch)` and `batch.keys()` before training.
- If only a transform needs a field, apply the transform before excluding it.

## Neighbor sampling backend is missing

Symptoms often mention that `NeighborSampler` requires `pyg-lib` or `torch-sparse`, or iteration fails although `NeighborLoader(...)` constructed successfully.

Fixes:

- Treat this as an environment optional-dependency issue, not a model bug.
- From this sub-skill directory, run the bundled script: `python scripts/loader_smoke_test.py --check-neighbor`.
- If the script reports a missing backend, install a PyG-compatible `pyg-lib` or `torch-sparse` build matching the current Torch/PyG installation.
- Avoid `subgraph_type="induced"` unless the environment supports the sparse backend path required for that sampling mode.
- Keep the skill's scripts backend-agnostic: report the missing backend clearly instead of downloading or compiling packages automatically.

## `input_nodes` is wrong

Symptoms:

- `NeighborLoader` samples unexpected seed nodes.
- Heterogeneous loader raises type errors or returns the wrong input type.
- `batch.n_id[:batch.batch_size]` does not match expected seeds.

Fixes:

- Homogeneous graph: pass `input_nodes` as a `torch.long` index tensor, `torch.bool` mask, or `None` for all nodes.
- Heterogeneous graph: pass a node type string such as `"paper"` or a tuple such as `("paper", train_mask)`.
- Ensure boolean masks have length equal to the number of nodes for that node type.
- Check one batch: `batch.n_id[:batch.batch_size]` for homogeneous data, or `batch["paper"].n_id[:batch["paper"].batch_size]` for hetero data.

## `edge_label_index` or `edge_label` is wrong

Symptoms:

- Link loader labels have the wrong length.
- Supervised edges refer to nodes outside the graph.
- Heterogeneous link loader uses the wrong edge type.
- Validation appears too good because supervision edges are visible in message passing.

Fixes:

- Homogeneous graph: pass `edge_label_index` with shape `[2, num_supervision_edges]`.
- Heterogeneous graph: pass `edge_label_index=(edge_type, tensor)` or an edge type tuple to use all edges of that type.
- Ensure `edge_label.numel() == edge_label_index.size(1)` when labels are provided.
- Map local output back to global ids with `batch.n_id[batch.edge_label_index]` before comparing to original edges.
- Prevent leakage by making `data.edge_index` and `edge_label_index` disjoint when required by the evaluation design.
- Prefer `neg_sampling=dict(mode="binary", amount=ratio)` over the older `neg_sampling_ratio` argument in new code.

## Temporal sampling arguments conflict

Symptoms:

- Error says `input_time` is set while `time_attr` is not set.
- Error says `edge_label_time` and `time_attr` must both be provided.
- Temporal sampling returns empty or surprising neighborhoods.

Fixes:

- For `NeighborLoader`, provide `time_attr` whenever `input_time` is provided.
- For `LinkNeighborLoader`, provide both `edge_label_time` and `time_attr`, or neither.
- Verify timestamp tensor lengths: node timestamps align with nodes; edge-label timestamps align with supervision edges.
- If using `is_sorted=True`, sort `edge_index` by destination column and sort temporal rows within each neighborhood.
- Choose `temporal_strategy="last"` for recency-biased sampling or `"uniform"` for uniform sampling among valid earlier neighbors.

## Directed, bidirectional, and induced subgraphs do not match the model

Symptoms:

- A deeper model underperforms or cannot propagate information as expected.
- Sampled subgraphs contain only edges toward seed nodes.
- `e_id` or `edge_attr` behavior changes with `subgraph_type`.

Fixes:

- Use default `subgraph_type="directional"` when the number of sampling hops equals the number of message-passing layers.
- Use `subgraph_type="bidirectional"` if the model needs reverse message flow or has more layers than sampled hops.
- Use `subgraph_type="induced"` only when edges among all sampled nodes are required and optional sparse backends are available.
- Re-check assumptions about `e_id` and `edge_attr`; bidirectional conversion may synthesize reverse edges that do not correspond one-to-one with original edge ids.

## Heterogeneous `num_neighbors` dictionary fails

Symptoms:

- Error says hop counts must be the same across all edge types.
- Error says not all edge types are covered.
- Some edge types are never sampled.

Fixes:

- Use canonical edge-type tuple keys, for example `("author", "writes", "paper")`.
- Give every edge type the same number of hop entries, such as `[10, 5]` for all types.
- If using a default fanout through lower-level APIs, ensure the default has the same hop count.
- Start with a shared list `num_neighbors=[10, 5]`; switch to a dictionary only when edge-type-specific fanout is needed.

## Multiprocessing and worker filtering issues

Symptoms:

- Too many open files when using workers.
- Features appear on an unexpected device.
- Worker failures disappear when `num_workers=0`.

Fixes:

- Reproduce with `num_workers=0` first to isolate sampler configuration from multiprocessing.
- Set `filter_per_worker=False` for fully in-memory CPU features when worker shared-memory pressure is high.
- Set `filter_per_worker=True` only when filtering in subprocesses is needed, especially for partially GPU-resident data.
- Keep smoke tests CPU-only and single-process for deterministic diagnostics.

## Minimal debug routine

```python
batch = next(iter(loader))
print(batch)
for key in ["batch_size", "n_id", "e_id", "input_id", "edge_label_index", "edge_label"]:
    if hasattr(batch, key):
        value = getattr(batch, key)
        print(key, getattr(value, "shape", value))
```

For hetero outputs, iterate through `batch.node_types` and `batch.edge_types` and inspect each store separately.
