# Data and Dataset Troubleshooting

Use this checklist when `Data`, `HeteroData`, transforms, or dataset classes behave unexpectedly.

## `edge_index` Shape or Dtype Fails

Symptoms:

- `Data.validate()` reports that `edge_index` needs shape `[2, num_edges]`.
- A convolution or transform fails with an index or dtype error.
- Batching produces impossible edge offsets.

Fix:

```python
edge_index = torch.as_tensor(edge_index, dtype=torch.long)
if edge_index.dim() != 2:
    raise ValueError("edge_index must be rank-2")
if edge_index.size(0) != 2 and edge_index.size(1) == 2:
    edge_index = edge_index.t().contiguous()
if edge_index.size(0) != 2:
    raise ValueError("edge_index must have shape [2, num_edges]")
```

Then set `data.edge_index = edge_index` and call `data.validate(raise_on_error=True)`.

## Negative or Out-of-Range Node Indices

Symptoms:

- `edge_index` contains negative indices.
- `edge_index.max()` is greater than or equal to `data.num_nodes`.
- Link splits or message passing fail after filtering nodes.

Fix:

- Rebuild node-id mappings from zero to `num_nodes - 1`.
- Set `data.num_nodes` explicitly when `x` is missing or isolated nodes exist.
- After subgraphing, either relabel nodes or preserve `num_nodes` intentionally and document why.
- For hetero graphs, validate each edge type against its source and destination node counts.

## Feature Count Mismatches Node Count

Symptoms:

- `x.size(0)` does not match `num_nodes`.
- Node masks have a different length than `x`.
- Batching creates a `batch` vector with an unexpected size.

Fix:

```python
if data.x is not None:
    data.num_nodes = data.x.size(0)
data.validate(raise_on_error=True)
for key in ("train_mask", "val_mask", "test_mask"):
    if key in data:
        assert data[key].dtype == torch.bool
        assert data[key].numel() == data.num_nodes
```

If features are optional, set `data.num_nodes` from the authoritative node table before adding edges.

## Missing Masks After Splitting

Symptoms:

- Training code expects `train_mask`, `val_mask`, or `test_mask`, but the data object does not contain them.
- A link prediction workflow expects `edge_label` or `edge_label_index`, but only `edge_index` is present.

Fix:

- For node classification, apply `torch_geometric.transforms.RandomNodeSplit` or create boolean masks manually.
- For link prediction, apply `torch_geometric.transforms.RandomLinkSplit` and inspect returned `train_data`, `val_data`, and `test_data`.
- Verify mask lengths and dtypes after splitting.
- For hetero link prediction, pass `edge_types` and corresponding `rev_edge_types` when reverse relations are stored.

## Transform Ordering Problems

Symptoms:

- `NormalizeFeatures` runs before `x` exists.
- `RandomLinkSplit` runs before making an undirected graph, causing leakage or asymmetric splits.
- A cached dataset ignores a changed preprocessing function.

Fix:

- Use `T.Compose([...])` to make order explicit.
- Validate before and after transforms that alter graph structure.
- Use `pre_transform` only for deterministic preprocessing that should be cached.
- Use `transform` for per-access or stochastic operations.
- Rebuild processed files with `force_reload=True` when changing `pre_transform` or `pre_filter`.

Common safe ordering:

```python
pre_transform = T.Compose([
    T.ToUndirected(),
    T.NormalizeFeatures(),
])
```

Apply random train/validation/test splits after the basic structure is valid.

## Dataset Download vs Process Confusion

Symptoms:

- `download()` does not run.
- `process()` does not run.
- Files in `processed/` are stale.
- Dataset code unexpectedly tries network access.

Fix:

- `download()` is skipped when all `raw_file_names` exist.
- `process()` is skipped when all `processed_file_names` exist and `force_reload=False`.
- In safe local recipes, make `download()` a no-op and build from local files or synthetic tensors.
- Delete the processed directory or pass `force_reload=True` to rebuild intentionally.
- Keep all writes under the dataset `root`.

## `pre_transform` and `pre_filter` Cache Warnings

Symptoms:

- PyG warns that `pre_transform` or `pre_filter` differs from the function used to create cached data.
- Changes to preprocessing do not appear in `dataset[0]`.

Fix:

```python
dataset = TinyGraphDataset(root, pre_transform=new_transform, force_reload=True)
```

Then inspect one processed graph:

```python
data = dataset[0]
data.validate(raise_on_error=True)
```

Avoid anonymous lambdas for long-lived preprocessing if reproducibility matters; define named callables or transform objects with stable string representations.

## Hetero Metadata Issues

Symptoms:

- A hetero edge type references a node type that was never created.
- `metadata()` is missing expected node or edge types.
- A transform only affects one relation.

Fix:

```python
node_types, edge_types = data.metadata()
assert "paper" in node_types
assert ("author", "writes", "paper") in edge_types
data.validate(raise_on_error=True)
```

For undirected hetero workflows, add explicit reverse edge types or use transforms that create them, then route model-specific questions to `../heterogeneous-graphs/SKILL.md`.

## Batch Surprises

Symptoms:

- Custom index-like attributes are shifted during batching.
- `batch.batch` length differs from expected node count.
- `to_data_list()` cannot reconstruct custom fields as expected.

Fix:

- Use standard names (`edge_index`, `x`, `edge_attr`, `y`) where possible.
- For custom data classes, override `__inc__` for attributes that should or should not be incremented.
- Override `__cat_dim__` for attributes that concatenate on non-default dimensions.
- Test custom batching with two tiny graphs before using real data.

## Quick Validator

Run the bundled script when you need a fast structural check:

```bash
python scripts/validate_basic_graph.py --fixture homogeneous
python scripts/validate_basic_graph.py --fixture invalid --expect-invalid
```

If the invalid fixture unexpectedly passes or a valid fixture fails, verify the installed `torch` and `torch_geometric` versions with the root environment checker.
