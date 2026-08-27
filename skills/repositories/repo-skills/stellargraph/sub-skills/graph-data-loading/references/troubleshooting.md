# Graph Data Loading Troubleshooting

## Constructor rejects edge columns

**Symptoms**

- `edges: expected 'source', 'target', 'weight' columns, found ...`
- `expected pandas DataFrame` or `expected IndexedArray`

**Likely causes**

- Edge DataFrame uses non-default source/target column names.
- Edge data was passed as a list or dict with wrong value types.
- Edge weight/type columns were not named or declared consistently.

**Recovery**

- Rename edge columns to `source`, `target`, and optional `weight`, or pass
  `source_column`, `target_column`, and `edge_weight_column` explicitly.
- For multiple edge types, use a dict of DataFrames keyed by edge type, or pass
  one DataFrame plus `edge_type_column="..."`.

## Edge endpoints are missing from explicit nodes

**Symptoms**

- `expected all source and target node IDs to be contained in nodes`
- Model/generator later reports invalid node IDs.

**Likely causes**

- Explicit `nodes` omit at least one edge endpoint.
- Node IDs have different dtypes between nodes and edges, such as string IDs in
  one table and integers in another.

**Recovery**

- Normalize node IDs before construction.
- Add missing node rows, or omit `nodes` intentionally when you want the graph to
  infer no-feature nodes from edges.
- After construction, compare `set(graph.nodes())` with target and edge IDs.

## Duplicate node IDs across types

**Symptoms**

- Heterogeneous graph construction fails or node features appear under the wrong
  type.

**Likely causes**

- Source data uses overlapping IDs for different entity types, such as user `1`
  and movie `1`.

**Recovery**

- Prefix or namespace IDs before construction, e.g. `user:1`, `movie:1`.
- Keep the node-type dictionary separate from ID names; IDs still need global
  uniqueness within one graph.

## Feature shape or dtype problems

**Symptoms**

- `check_graph_for_ml` fails.
- TensorFlow/Keras model errors appear after generator construction.
- Feature-size maps show zero-width or inconsistent features.

**Likely causes**

- Non-numeric columns were included as features.
- Labels or categories were left as strings instead of encoded separately.
- Heterogeneous node types have different feature dimensions and the selected
  model/generator does not support that shape.

**Recovery**

- Keep supervised labels outside the node feature DataFrame unless deliberately
  using `subject_as_feature` in a dataset loader.
- Encode categorical features with Pandas/scikit-learn before graph creation.
- Print `graph.node_feature_sizes()` and select a compatible model route.

## NetworkX conversion warnings

**Symptoms**

- Deprecation warnings about constructing a `StellarGraph` from a NetworkX graph.

**Recovery**

- Use `StellarGraph.from_networkx(...)` with explicit `node_type_attr`,
  `edge_type_attr`, `edge_weight_attr`, and `node_features`.

## Dataset download/cache failures

**Symptoms**

- `URLError`, `FileNotFoundError`, unexpected missing files, or permission
  errors under the dataset cache.

**Recovery**

1. Confirm the task really needs the external dataset; use a synthetic graph if
   a tiny API smoke is enough.
2. Set `STELLARGRAPH_DATASETS_PATH` to a writable location.
3. Instantiate the dataset class and inspect `base_directory`/`data_directory`.
4. Use `download(ignore_cache=True)` only when replacing an existing cache is
   intentional.
5. If remote hosts fail, stop and report network/data availability instead of
   debugging model code.

## Tiny diagnostic

Run the bundled smoke before blaming a model or generator:

```bash
python sub-skills/graph-data-loading/scripts/stellargraph_data_smoke.py
```

If this passes but the real graph fails, compare your real node IDs, edge
columns, feature sizes, and directedness to the smoke's printed summary.
