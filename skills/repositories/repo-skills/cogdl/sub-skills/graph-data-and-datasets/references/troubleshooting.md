# Graph Data Troubleshooting

Use this matrix when CogDL data construction, validation, or batching fails.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ValueError: Node features must be Tensor` | `Graph(x=...)` received a list, NumPy array, SciPy matrix, or pandas object. | Convert explicitly: `x = torch.as_tensor(array, dtype=torch.float)`. For sparse features, densify only if memory-safe or choose a workflow that supports sparse/featureless data. |
| `edge_index` has wrong shape | Input is `[num_edges, 2]`, nested Python pairs, or a tuple with mismatched lengths. | Convert to long COO: `edge_index = torch.as_tensor(edges, dtype=torch.long).t().contiguous()` and assert `edge_index.shape[0] == 2`. |
| Edge ids out of range | One-based ids, stale node count, or missing isolated nodes. | Normalize ids, set `graph.num_nodes` explicitly for real isolated nodes, and fail validation for genuinely invalid ids. |
| Edge weights or attributes mismatch edge count | Edges were filtered/reordered without filtering `edge_weight` or `edge_attr`. | Apply the same edge mask/reindex to all edge-aligned tensors. Rebuild attributes after self-loop or subgraph operations if necessary. |
| `train_mask`/`val_mask`/`test_mask` length mismatch | Masks were created before subgraphing, with the wrong node count, or as graph-level labels. | Rebuild masks for the current local node ordering. Run `python scripts/validate_graph_masks.py --path <graph.pt>`. |
| Split masks overlap unexpectedly | Boolean masks were composed independently or index masks have duplicate ids. | Decide whether overlap is intentional. For standard node classification, make masks disjoint and rerun the validator. |
| Missing labels or `num_classes == 0` | `graph.y` is absent, scalar, or not node-aligned. | Add `y` with shape `[num_nodes]` for single-label node classification or `[num_nodes, num_labels]` for multi-label classification. |
| `NodeDataset` reuses old data | The `.pt` path already exists, so processing/loading skipped new data. | Use a fresh path, deliberately remove the stale artifact, or pass an explicit `data=graph` with a known output path. |
| `GraphDataset` fails before processing | Base `GraphDataset` expects the `.pt` file to exist unless subclass `process()` creates it. | Save `list[Graph]` to the path first, or implement a subclass whose `process()` returns and saves the list. |
| Built-in dataset load starts downloading | Raw/processed cache files are absent. | Stop unless network/cache writes are approved. For smoke tests, use a custom graph or bundled tiny-data script. |
| Dataset download/unpack fails | Network unavailable, mirror changed, archive incomplete, or storage quota exceeded. | Treat built-in use as optional until cache is present. Do not substitute a partial cache; rebuild or choose a no-download fixture. |
| Unsupported metric raises `NotImplementedError` | Custom dataset metric is not one of CogDL's supported strings. | Use `accuracy`, `multiclass_f1`, or `multilabel_f1`; check label shape before relying on `metric='auto'`. |
| Graph-classification model receives `x=None` | TU-style or custom graphs may lack node attributes. | Either provide node features per graph or route to training-wrapper guidance for `degree_node_features=True`. |
| Batched graph has unexpected node ids | `DataLoader` offsets local graph node ids when forming a block-diagonal batch. | Inspect `batch.batch` to map nodes back to source graphs. Keep per-graph edge ids local before batching. |
| `subgraph` changes edge count or masks break | `subgraph(node_idx)` induces edges among selected nodes and reindexes node attributes; masks from the original graph do not automatically match. | Slice/rebuild masks using the selected node list. For edge-based selection, use `edge_subgraph(..., require_idx=True)` and use returned `nodes` for mapping. |
| `local_graph()` did not restore a value | In-place tensor mutation changed the original tensor object. | Inside `local_graph()`, prefer out-of-place assignment such as `graph.edge_weight = graph.edge_weight + 1`. Clone tensors before in-place experiments. |
| `train()` and `eval()` appear identical | No train-specific adjacency was provided. | This is normal for transductive graphs. For inductive data, construct with fields such as `edge_index_train` and `edge_attr_train`. |
| CSR fields behave differently from COO | COO/CSR conversion can sort or reindex edges. | Prefer COO for construction and validation. If using CSR, validate `row_indptr[-1] == len(col_indices)` and edge-aligned attributes after conversion. |
| `torch.load` rejects a saved `Graph` on newer PyTorch | Safe-loading defaults may reject custom classes. | Use trusted CogDL-created artifacts. The bundled scripts register CogDL graph classes as safe globals where supported; only use unsafe pickle loading for trusted files. |
| Optional OGB dataset import fails | The optional `ogb` package is missing or incompatible. | Install/verify `ogb` only if the user approved that dataset family; otherwise use a core/custom dataset. |
| CUDA, PyG, Jittor, or DGL errors appear while handling data | The task has moved into optional acceleration or third-party library territory. | Keep data validation on CPU and route backend/model/operator decisions to the models/layers/operators sub-skill. |

## Debug sequence for node fixtures

1. Load the saved graph or dataset artifact in a clean Python process.
2. Print `graph.num_nodes`, `graph.num_edges`, `graph.num_features`, and
   `graph.num_classes`.
3. Validate `x`, `y`, `edge_index`, and masks with the bundled validator.
4. Use `with graph.local_graph():` for temporary edge edits while avoiding
   in-place tensor mutation.
5. Only after validation succeeds, route to experiment or training-wrapper
   guidance.

## Debug sequence for graph-classification fixtures

1. Confirm the saved object is a nonempty list of `Graph` objects.
2. For each graph, validate local edge ids and graph-level label shape.
3. Instantiate `GraphDataset(path=...)` and take one `DataLoader` batch.
4. If node features are missing, decide whether to add explicit features or use
   degree features in the training wrapper.
5. Route model and training-budget choices away from this data sub-skill.
