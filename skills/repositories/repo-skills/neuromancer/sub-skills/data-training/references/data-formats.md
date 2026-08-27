# Data formats and batch schemas

## Choose one sample axis

Before constructing any dataset, make the first dimension explicit:

| Dataset | Input value shape | Sample axis | Batch output |
|---|---|---|---|
| `DictDataset` | keyed tensor `(N, ...)` | `N` | keyed `(B, ...)` plus `name` |
| `StaticDataset` | keyed array/tensor `(N, D)` | `N` | keyed `(B, D)` plus `index` and `name` |
| `SequenceDataset` | keyed array/tensor `(T, D)` or list of such dicts | time `T` | keyed `*p`/`*f` `(B, nsteps, D)` plus `name` |
| `GraphDataset` | per-experiment node/edge/graph feature lists | experiment and optional time | concatenated graph features, node `batch`, offset `edge_index`, `name` |

For dictionary and static inputs, every value must have the same first axis.
For one sequence, every variable must have the same time length. For a list of
sequences, every dictionary must have the same keys and each sequence must be
internally time-aligned. A feature dimension may differ between variables; it
is not the sample axis.

## Dictionary and static schemas

A minimal static setup is conceptually:

```python
raw = {
    "x": torch.randn(N, nx),
    "u": torch.randn(N, nu),
    "y": torch.randn(N, ny),
}
train = DictDataset(raw, name="train")
loader = DataLoader(train, batch_size=32, collate_fn=train.collate_fn)
```

`StaticDataset` uses the same keyed input but exposes an `index` in each item
and has `get_full_batch()` for one full tensor dictionary. Feature names are
application-defined; they should match the keys consumed by the model/problem.
Keep values as floating point unless the consuming module explicitly expects an
integer field.

The `name` field is not metadata to discard. NeuroMANCER's `Problem.forward`
uses it when prefixing loss/output keys, so a `train` batch commonly produces
`train_*` metric keys. A loader made with ordinary default collation omits the
field and is not a valid training loader for the usual Problem contract.

## Sequence schemas and names

Raw sequential data normally uses keys such as `X`, `Y`, `U`, and `D`, each of
shape `(T, Dk)`. `SequenceDataset` transforms each key into:

```text
Xp: (nsteps, Dx)   Xf: (nsteps, Dx)
Yp: (nsteps, Dy)   Yf: (nsteps, Dy)
Up: (nsteps, Du)   Uf: (nsteps, Du)
Dp: (nsteps, Dd)   Df: (nsteps, Dd)
```

Only keys supplied in the input are emitted. `moving_horizon=False` produces
non-overlapping windows with stride `nsteps`; `True` uses stride 1. The `p` and
`f` suffixes mean past/window and following window in the dataset item
contract, not arbitrary variable renaming. Use `dataset.dims`,
`get_full_batch()`, and one collated batch to confirm the actual shapes before
connecting a model.

For multiple trajectories, pass `[{"X": seq0, "Y": seq0_y}, {"X": seq1,
"Y": seq1_y}]`. The constructor preserves sequence boundaries in
`get_full_sequence()` and checks that all dictionaries have matching keys. A
list is split by trajectory count by the multi-sequence branch of
`split_sequence_data`; it is not split by total time rows.

## Graph schemas

Use per-experiment lists, for example:

```text
node_attr = {"pos": [nodes_exp0, nodes_exp1]}
edge_attr = {"weight": [edges_exp0, edges_exp1]}
graph_attr = {"context": [graph_exp0, graph_exp1]}
graphs = {0: edge_index_exp0, 1: edge_index_exp1}
```

Categorical node, edge, and graph features are typically rank 2. Temporal
features are rank 3 and are sliced using `seq_len`, `seq_horizon`, and
`seq_stride`. An adjacency tensor is `(2, E)` with integer indices. When graph
samples are collated, edge indices are offset by the cumulative node count and
the `batch` vector identifies the source graph for every node.

Use `build_graphs="feature_name"` only when the named node feature exists and
its distances are meaningful. `connectivity_radius` and `graph_self_loops`
control the local CPU radius graph builder. For deterministic experiments,
precompute and pass `graphs`; this also avoids depending on unrelated optional
graph packages. Check that every sampled item has the feature keys expected by
the collator.

## CSV and MAT conventions

The generic file reader accepts `.csv` and `.mat` files. At a high level:

- MAT variables use lowercase `y`, `x`, `u`, and `d` for observations, states,
  inputs, and disturbances; `exp_id` optionally partitions rows into
  trajectories.
- CSV columns use exact lower-case numbered prefixes such as `y1`, `x1`, `u1`,
  and `d1`; columns beginning with `exp_id` optionally partition rows.
- At least one of Y, X, U, or D must be present. A directory is read in sorted
  filename order and produces one result per file.
- With `exp_id`, the result is a list of dictionaries, one per sorted id;
  without it, the result is one dictionary. The reader does not invent missing
  X/Y/U/D values.

Keep file ingestion separate from normalization and split decisions. The PSL
file-emulator family may additionally recognize `Time`, but generic dataset
preparation should not assume a time column is emitted by every reader.

## Normalization schema

`normalize_data(data, norm_type, stats=None)` supports:

- `zscore`: `(M - mean) / std`
- `zero-one`: `(M - min) / (max - min)`
- `one-one`: `2 * (M - min) / (max - min) - 1`

The returned stats map is `{key + "_min": vector, key + "_max": vector}`.
For z-score, these two fields contain mean and standard deviation despite their
historical names. Constant columns are converted to finite values by the
underlying implementation. Reuse the stats map unchanged for dev/test; do not
recompute it on held-out data.

A leakage-safe pattern is:

```python
train_raw, dev_raw, test_raw = split_static_data(raw, [70.0, 15.0])
train_norm, stats = normalize_data(train_raw, "zscore")
dev_norm, _ = normalize_data(dev_raw, "zscore", stats)
test_norm, _ = normalize_data(test_raw, "zscore", stats)
```

Use the analogous `split_sequence_data` call for time series. The convenience
loader factories normalize before splitting when `norm_type` is provided, so
call them with `norm_type=None` after performing the explicit sequence above if
statistics must be train-only.

## Split schema

`split_static_data` and `split_sequence_data` take
`split_ratio=[train_percent, dev_percent]`; the remainder is test. With no
ratio, each uses thirds. Explicit ratios are rounded up at boundaries. For a
single sequence, the default sequence split aligns the usable train/dev ranges
to `nsteps` and carries context across a boundary. For a list of sequences,
splits are over trajectory entries and each resulting list must still contain a
valid sequence for the selected `nsteps`.

Always print or assert split sizes before building datasets. A tiny input can
legitimately yield an empty dev/test partition; decide whether to reduce the
ratio, omit that split, or stop before constructing a loader.
