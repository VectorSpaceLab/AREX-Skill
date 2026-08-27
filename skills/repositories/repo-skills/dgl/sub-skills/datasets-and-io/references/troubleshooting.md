# Troubleshooting DGL Datasets and IO

## `meta.yaml` Missing or Wrong File Name

Signal:

- `dgl.data.CSVDataset(DATASET_DIR)` raises that `meta.yaml` cannot be found.

Fix:

- Ensure the file is named exactly `meta.yaml` for `CSVDataset`.
- Do not confuse it with GraphBolt `metadata.yaml`.
- Run `python scripts/csv_dataset_linter.py DATASET_DIR` before loading with DGL.

## YAML Validation Errors

Signals:

- DGL reports `Validation Error for YAML fields`.
- DGL reports unsupported `CSVDataset` version.
- The linter reports missing `dataset_name`, `node_data`, or `edge_data`.

Fix:

- Use `version: 1.0.0` or omit `version`.
- Make `node_data` and `edge_data` lists, not mappings.
- Add `file_name` for every node, edge, and graph-data entry.
- Keep each `ntype` unique across `node_data`.
- Keep each canonical `etype` unique across `edge_data`.

## Heterograph `etype` Is a Scalar

Signal:

- A heterograph CSV has `etype: buys` or `etype: user:buys:item`.
- DGL schema validation fails or edge data is routed to the wrong type.

Fix:

- Use a three-item YAML list: `etype: [user, buys, item]`.
- Ensure `user` and `item` are present as `ntype` values in `node_data`.
- Ensure `src_id` values exist in the source node type CSV and `dst_id` values exist in the destination node type CSV.

## Required CSV Columns Missing

Signals:

- `Missing node id field [node_id]`.
- `Missing src id field [src_id]`.
- `Missing dst id field [dst_id]`.
- The linter reports missing required columns.

Fix:

- Add `node_id` to node CSVs, or set `node_id_field` in `meta.yaml`.
- Add `src_id` and `dst_id` to edge CSVs, or set `src_id_field` and `dst_id_field`.
- For graph-level data, add `graph_id` or set `graph_id_field`.
- If a CSV was exported from pandas, remove accidental unnamed index columns or export with `index=False`.

## Bad File Paths in `meta.yaml`

Signal:

- DGL or the linter cannot find a CSV file.

Fix:

- Make every `file_name` relative to the dataset folder containing `meta.yaml`.
- Avoid absolute paths in portable datasets.
- Confirm case-sensitive file names on Linux.

## Duplicate Node IDs

Signal:

- DGL reports duplicate node IDs for a graph.

Fix:

- Within each `(graph_id, ntype)` group, every raw `node_id` must be unique.
- If data was concatenated from multiple files, namespace raw IDs or split by `graph_id`.
- Remember that raw IDs may be strings, but edge endpoints must use the same raw ID representation.

## Edge Endpoints Do Not Match Node Tables

Signals:

- Key errors during graph construction.
- Edges vanish or construction fails for heterographs.

Fix:

- For each edge CSV row, `src_id` must exist in the node table for `etype[0]` and `dst_id` must exist in the node table for `etype[2]`.
- Check type coercion: string ID `"001"` and numeric ID `1` are different raw IDs before DGL maps them.
- Run the linter with default checks; it reports missing endpoint IDs by canonical edge type.

## Feature Column Parsing Fails

Signals:

- `ValueError`, `SyntaxError`, or object dtype after CSV load.
- Empty feature cells cause failures.
- Vector feature columns have inconsistent shape.

Fix:

- Quote vector features, for example `"0.1, 0.2, 0.3"`.
- Avoid empty cells with the default parser; impute values or write a custom parser.
- For categorical strings, write `ndata_parser`, `edata_parser`, or `gdata_parser` that returns numpy arrays or tensors.
- Ensure every row of a vector feature has the same length.
- Remove `Unnamed` columns created by pandas index exports.

## Masks Are Wrong Shape or Dtype

Signals:

- Training code cannot index with `train_mask`.
- Mask lengths differ from node or edge counts.
- Masks are strings or integers when the model expects booleans.

Fix:

- Put node task masks in node CSVs so they become `g.ndata["train_mask"]`, `g.ndata["val_mask"]`, and `g.ndata["test_mask"]`.
- Put edge task masks in edge CSVs so they become `g.edata[...]`.
- Use `True`/`False` consistently in CSVs or cast in a custom parser.
- Validate that each mask length equals the number of nodes or edges for its type.

## Cache Does Not Update After CSV Changes

Signal:

- `CSVDataset` returns old features or labels after editing CSV files.

Fix:

- Instantiate with `force_reload=True` after changing CSVs, `meta.yaml`, or parser code.
- Delete the processed `<dataset_name>.bin` cache if you need a clean reload.
- Change `dataset_name` or cache location when comparing two incompatible CSV revisions side by side.

## Custom `DGLDataset` Loads Partial Cache

Signal:

- `has_cache()` returns true, then `load()` fails because `info.pkl`, labels, or another file is missing.
- `force_reload=False` unexpectedly reprocesses every time.

Fix:

- Make `has_cache()` check every file used by `load()`.
- Keep graph tensors in `graphs.bin` via `save_graphs()` and non-tensor metadata in `info.pkl` via `save_info()`.
- Restore all attributes used by `__getitem__`, `__len__`, and properties inside `load()`.
- Include preprocessing options in `hash_key` when cache variants can conflict.

## `save_graphs()` or `load_graphs()` Fails

Signals:

- Filename points to a directory.
- File does not exist on load.
- Batched graph serialization fails.
- Reloaded labels do not match selected `idx_list` expectations.

Fix:

- Pass a file path such as `cache/graphs.bin`, not a directory path.
- Ensure the parent directory is writable.
- Use `dgl.unbatch()` before serialization if the graph is batched.
- Remember that `load_graphs(path, idx_list=[...])` returns selected graphs but a labels dict for all saved graphs.

## Download or Cache Directory Problems

Signals:

- Built-in dataset download fails.
- Cache is written to an unexpected location.
- A mirror URL is wrong.

Fix:

- Pass explicit `raw_dir=` and `save_dir=` to dataset constructors for reproducibility.
- `DGL_DOWNLOAD_DIR` changes the default download/cache root when `raw_dir` is omitted.
- `DGL_REPO` changes the base URL for DGL-hosted downloads.
- Avoid network-dependent built-ins in automated verification unless the user explicitly permits downloads.
- Use `force_reload=True` only to repair or refresh a known cache.

## Confusing `CSVDataset`, GraphBolt, and Distributed Files

Signals:

- A folder has `metadata.yaml` but `CSVDataset` says `meta.yaml` is missing.
- A folder has distributed partition outputs but no node/edge CSV schema.
- A task asks for minibatch streaming from disk after CSV validation.

Fix:

- `CSVDataset` consumes `meta.yaml` plus node/edge/graph CSVs.
- GraphBolt `OnDiskDataset` consumes `metadata.yaml` plus graph structure, feature arrays, and task-set files; route execution to `dataloading-graphbolt`.
- Distributed partition artifacts and `part_config` files belong to `distributed-tools`.
