# DGL Message Passing Troubleshooting

Use this checklist when a DGL full-graph model, message passing call, heterograph module, or sparse op fails.

## Zero In-Degree Errors

Symptoms:

- `DGLError` mentions `0-in-degree nodes` from `GraphConv` or `GATConv`.
- Training runs but isolated nodes have suspicious or all-zero logits after bypassing the check.

Fixes:

- Homogeneous graph where self-features should contribute: call `graph = dgl.add_self_loop(graph)` before the layer.
- Heterograph or graph where self-loops are not well-defined: set `allow_zero_in_degree=True` and explicitly handle isolated destination nodes.
- For `HeteroGraphConv`, DGL attempts to set `allow_zero_in_degree=True` on relation modules that support it, but missing input features or empty relations can still produce absent destination keys.
- Do not add self-loops blindly to bipartite or heterographs; node types may differ.

## Missing Features, Labels, or Masks

Symptoms:

- `KeyError: 'feat'`, `'label'`, `'train_mask'`, or a node type key.
- Loss fails because `train_mask` is empty or has the wrong dtype.

Fixes:

- Inspect `graph.ndata.keys()` and `graph.edata.keys()` for homogeneous graphs.
- For heterographs, inspect `graph.nodes[ntype].data.keys()` and `graph.edges[etype].data.keys()`.
- Ensure masks are `torch.bool` and have shape `(num_nodes,)` or `(num_edges,)` for the supervised entity type.
- Ensure labels are `torch.long` for `F.cross_entropy` and floating point for regression losses.
- Route dataset parsing, CSV column mapping, and mask construction to `../datasets-and-io/`.

## Dtype and Device Mismatch

Symptoms:

- PyTorch error says tensors are on different devices.
- `expected scalar type Long` or `Float` errors.
- Sparse matrix multiplication fails after moving only dense features to a device.

Fixes:

- Move the graph first: `graph = graph.to(device)`; then read features from the moved graph or move feature tensors too.
- Keep labels for classification as `torch.long`.
- Keep node/edge features and edge weights as floating point tensors.
- Ensure edge IDs, relation IDs, and indices are integer tensors (`torch.int64` is safest).
- For DGL sparse, construct `row`, `col`, `val`, and dense operands on the same device.

## Shape Mismatch in Layers

Symptoms:

- Linear layer matrix multiplication shape errors.
- GAT output has an unexpected third dimension.
- `SAGEConv` on relation subgraphs complains about source/destination feature shapes.

Fixes:

- Set `in_feats` to `features.shape[1]`, not `num_nodes`.
- For `GATConv`, output shape is `(N, num_heads, out_feats)`; use `.flatten(1)` between layers or `.mean(1)`/`.squeeze(1)` for final logits.
- For bipartite or heterograph relation modules, pass tuple dimensions: `SAGEConv((src_dim, dst_dim), out_dim, 'mean')`.
- Assert logits shape before loss: `logits[mask].shape[0] == labels[mask].shape[0]`.

## Built-in Function Field Errors

Symptoms:

- `KeyError` for message fields such as `'h'`, `'w'`, `'m'`, or output fields.
- Edge scoring produces stale values from a previous forward pass.

Fixes:

- Put temporary assignments in `with graph.local_scope():`.
- Before `update_all(fn.u_mul_e('h', 'w', 'm'), ...)`, set `graph.ndata['h']` and `graph.edata['w']` with compatible shapes.
- Before `apply_edges(fn.u_dot_v('h', 'h', 'score'))`, set `graph.ndata['h']` for all needed source/destination node types.
- Avoid reusing a field name for both raw inputs and hidden states unless the scope is local.

## Heterograph Relation Key Mismatch

Symptoms:

- `KeyError: Cannot find module with edge type ...`.
- `HeteroGraphConv` output misses a supervised node type.
- Only some relations run.

Fixes:

- Compare `graph.canonical_etypes` to the `mods` keys.
- Use canonical edge type keys like `('user', 'plays', 'game')` when relation names are reused.
- Ensure `features` contains every source and destination node type needed by active relations.
- Empty relation graphs may be skipped; downstream code must tolerate missing outputs or fill defaults.
- For prediction on one edge type, pass the exact `etype` to `apply_edges` and read `graph.edges[etype].data[...]`.

## Link Prediction Negative Graph Issues

Symptoms:

- Positive and negative scores have incompatible shapes.
- Negative graph is on CPU while the model is on GPU.
- Heterograph negative samples target invalid destination node IDs.

Fixes:

- Preserve `num_nodes` or `num_nodes_dict` when creating negative graphs.
- Use `device=graph.device` where supported, or call `.to(graph.device)`.
- Repeat each positive source `k` times and reshape negative scores as `(-1, k)` for margin losses.
- For heterographs, sample negatives from the destination node type count: `graph.num_nodes(vtype)`.

## Graph Readout Problems

Symptoms:

- Graph classification logits have one row instead of `batch_size` rows.
- Readout fails after graph transforms.

Fixes:

- Build batches with `dgl.batch(graphs)`.
- Use `dgl.mean_nodes`, `dgl.sum_nodes`, or `dgl.readout_nodes` after setting a node feature field.
- If a transform discards batch metadata, restore batch node/edge counts before readout.
- For heterographs, pass `ntype=` or `etype=` when readout is type-specific.

## DGL Sparse Import or Native Library Mismatch

Symptoms:

- `import dgl.sparse` fails.
- Error mentions `dgl_sparse`, `torch.ops.dgl_sparse`, missing shared object, or ABI mismatch.
- Sparse constructors work but `softmax` or matrix multiplication fails.

Fixes:

- Run `python scripts/sparse_api_smoke.py` from this sub-skill directory to get a clear skip/error summary.
- Confirm installed DGL, PyTorch, and `dgl_sparse` native extension versions are compatible.
- Keep sparse smoke tests optional if the task does not require sparse APIs.
- Fall back to dense DGL message passing (`update_all`, `GraphConv`, `SAGEConv`) when sparse native libraries are unavailable and the graph is tiny enough.

## GraphBolt Native Library Mismatch

Symptoms:

- Importing DGL triggers an error about missing GraphBolt native library for the installed PyTorch version.
- `dgl.graphbolt` or dataloaders fail before model code runs.

Fixes:

- For full-graph training, avoid GraphBolt imports entirely.
- If stochastic sampling is required, route to `../dataloading-graphbolt/` and verify the GraphBolt smoke there.
- Align DGL and PyTorch versions when installing; a PyTorch minor-version mismatch commonly breaks native GraphBolt libraries.

## Gradient or Memory Issues

Symptoms:

- `loss.backward()` reports in-place modification or detached tensor errors.
- Full-graph training runs out of memory.
- Loss is `nan` or `inf`.

Fixes:

- Avoid in-place mutation on tensors used in loss; prefer `h = F.relu(h)` over in-place activations while debugging.
- Use `local_scope()` so feature stores do not accumulate hidden states across epochs.
- For large graphs, route to `../dataloading-graphbolt/` for minibatch neighbor sampling.
- Reduce hidden size, heads, layers, or use GraphSAGE before GAT when memory is tight.
- Check for empty masks, invalid labels, non-finite input features, and overly high learning rates.

## When to Run the Bundled Smokes

- Run `python scripts/training_smoke.py` after installing or changing DGL/PyTorch to verify `dgl.graph`, `update_all`, `GraphConv`, `SAGEConv`, `GATConv`, `HeteroGraphConv`, readout, and one optimizer step.
- Run `python scripts/sparse_api_smoke.py` before using `dgl.sparse` in a solution. Treat a clear sparse skip as a dependency/environment issue, not a failure of full-graph DGL training.
