# DGL Message Passing and Training API Reference

This reference focuses on DGL 2.x PyTorch workflows verified against live DGL 2.1.0 signatures and source/docs/tests evidence from the DGL 2.5 checkout. Prefer these APIs for full-graph training and small deterministic examples; route stochastic minibatch loaders to `../dataloading-graphbolt/`.

## Message Passing Primitives

DGL graph message passing has three functions:

- **Message function**: computes messages on edges from `edges.src`, `edges.dst`, and `edges.data`.
- **Reduce function**: aggregates messages on destination nodes using `nodes.mailbox`.
- **Apply/update function**: post-processes aggregated node results.

Core graph methods:

- `graph.update_all(message_func, reduce_func, apply_node_func=None)`: run message, reduce, and optional node update on all edges. Use it for whole-graph propagation.
- `graph.apply_edges(func, edges=..., etype=...)`: compute edge features without reducing to nodes; use it for edge scoring, link scoring, attention logits, and feature transforms.
- `graph.send_and_recv(edges, message_func, reduce_func, apply_node_func=None, etype=...)`: run message passing on selected edges.
- `graph.multi_update_all(etype_dict, cross_reducer)`: heterograph relation-wise message passing; prefer `dgl.nn.pytorch.HeteroGraphConv` for neural modules.

Use `with graph.local_scope():` inside model `forward()` when writing temporary `ndata` or `edata` fields so feature mutations do not leak between calls.

## Built-in `dgl.function` Selection

Import built-ins as `import dgl.function as fn`. Built-ins are optimized and handle broadcasting, so prefer them over UDFs when the operation is expressible by field names.

Common message functions:

- `fn.copy_u(src_field, out_field)`: copy source node features into messages.
- `fn.copy_e(edge_field, out_field)`: copy edge features into messages.
- `fn.u_add_v(lhs_field, rhs_field, out_field)`, `fn.u_sub_v`, `fn.u_mul_v`, `fn.u_div_v`, `fn.u_dot_v`: combine source and destination node features.
- `fn.u_add_e`, `fn.u_mul_e`, `fn.e_add_v`, `fn.e_mul_v`, and other `u|v|e` binary combinations: combine source, destination, and edge fields.

Common reduce functions:

- `fn.sum(msg_field, out_field)`
- `fn.mean(msg_field, out_field)`
- `fn.max(msg_field, out_field)`
- `fn.min(msg_field, out_field)`

Examples:

```python
import dgl.function as fn

g.update_all(fn.copy_u("h", "m"), fn.sum("m", "h_neigh"))
g.update_all(fn.u_mul_e("h", "w", "m"), fn.sum("m", "h_weighted"))
g.apply_edges(fn.u_dot_v("h", "h", "score"))
```

Use a UDF only when the computation cannot be expressed as a built-in, such as concatenating features before an MLP, using custom edge attributes with nonlinear logic, or returning multiple fields. UDFs are flexible but can be slower and easier to break with shape/device mismatches.

## PyTorch GNN Layers

Import with `import dgl.nn.pytorch as dglnn` or `import dgl.nn as dglnn` in PyTorch-only code.

Verified signatures:

- `dglnn.GraphConv(in_feats, out_feats, norm='both', weight=True, bias=True, activation=None, allow_zero_in_degree=False)`
- `dglnn.SAGEConv(in_feats, out_feats, aggregator_type, feat_drop=0.0, bias=True, norm=None, activation=None)`
- `dglnn.GATConv(in_feats, out_feats, num_heads, feat_drop=0.0, attn_drop=0.0, negative_slope=0.2, residual=False, activation=None, allow_zero_in_degree=False, bias=True)`
- `dglnn.HeteroGraphConv(mods, aggregate='sum')`
- `dglnn.RelGraphConv(in_feat, out_feat, num_rels, regularizer=None, num_bases=None, bias=True, activation=None, self_loop=True, dropout=0.0, layer_norm=False)`

Layer choice:

- **GCN**: `GraphConv`; best for homogeneous graphs when degree-normalized neighbor averaging is appropriate. Add self-loops for ordinary homogeneous node classification unless zero in-degree semantics are intentional.
- **GraphSAGE**: `SAGEConv(..., aggregator_type='mean'|'gcn'|'pool'|'lstm')`; good default for inductive/full-graph encoders and edge/link predictors.
- **GAT**: `GATConv`; use when attention over neighbors matters. Output shape is usually `(num_nodes, num_heads, out_feats)`, so flatten or average heads before loss.
- **RGCN**: `RelGraphConv`; use on homogeneous relation-id encoded graphs with an edge type tensor, especially when many relations share parameters via `regularizer='basis'` or `'bdd'`.
- **Heterograph relation modules**: `HeteroGraphConv`; use on `dgl.heterograph` with one module per relation name or canonical edge type.

Forward-call reminders:

- `GraphConv(g, feat)` and `GATConv(g, feat)` accept a graph and features; many layers also accept bipartite input as `(src_feat, dst_feat)` for blocks or relation subgraphs.
- `SAGEConv` requires `aggregator_type`; omit it only if wrapping an existing module that already sets it.
- `HeteroGraphConv(g, inputs)` takes `inputs` as `{ntype: tensor}` and returns `{dst_ntype: tensor}`.
- `RelGraphConv(g, feat, etypes)` expects a tensor of relation IDs aligned with `g.edges()` order.

## Readout and Pooling

Use readout after node/edge embeddings when the task predicts graph labels or aggregate statistics.

Common APIs:

- `dgl.readout_nodes(graph, feat, weight=None, op='sum'|'mean'|'max'|'min', ntype=None)`
- `dgl.readout_edges(graph, feat, weight=None, op='sum'|'mean'|'max'|'min', etype=None)`
- `dgl.sum_nodes`, `dgl.mean_nodes`, `dgl.max_nodes`
- `dgl.sum_edges`, `dgl.mean_edges`, `dgl.max_edges`
- `dgl.softmax_nodes`, `dgl.softmax_edges`
- `dgl.broadcast_nodes`, `dgl.broadcast_edges`
- `dgl.topk_nodes`, `dgl.topk_edges`

On a batched graph created by `dgl.batch`, readout returns one row per original graph. If a graph transform discards batch metadata, restore it with `set_batch_num_nodes()` and `set_batch_num_edges()` before readout.

## Heterograph Module Keys

`HeteroGraphConv` accepts a `mods` dictionary. Keys may be relation names such as `'follows'` when relation names are unique, or canonical edge types such as `('user', 'plays', 'game')` when relation names are ambiguous.

Use canonical keys when a graph has repeated relation names across node type pairs. DGL internally stringifies module keys for `torch.nn.ModuleDict`, but lookup still supports canonical edge type keys.

Aggregation options include `'sum'`, `'max'`, `'min'`, `'mean'`, `'stack'`, or a callable `(tensors, dsttype) -> tensor`. Use `'stack'` if downstream logic needs per-relation outputs instead of an immediate reduction.

## DGL Sparse API

Import with `import dgl.sparse as dglsp`. Sparse support depends on native DGL sparse libraries; use `scripts/sparse_api_smoke.py` to detect availability.

Verified constructors and op:

- `dglsp.spmatrix(indices, val=None, shape=None)` where `indices` has shape `(2, nnz)`.
- `dglsp.from_coo(row, col, val=None, shape=None)`.
- `dglsp.from_csr(indptr, indices, val=None, shape=None)`.
- `dglsp.softmax(input, dim=1)`; `dim=1` is row-wise, `dim=0` is column-wise.

Useful sparse matrix methods/operators commonly available in DGL 2.x include `A.val`, `A.shape`, `A.nnz`, `A.indices()`, `A.coalesce()`, `A.transpose()`/`A.T`, `A.to_dense()`, `A.sum(dim)`, `A @ dense`, and sparse-sparse arithmetic where supported by the installed native extension.

Sparse caveats:

- `val` may be shape `(nnz,)` or `(nnz, D)`; higher dimensions are invalid.
- If `shape` is omitted, it is inferred from max row/column index; pass `shape` when isolated rows/columns must exist.
- Sparse ops require matching tensor devices and DGL native libraries. CPU-only installs can still use many sparse ops if `dgl_sparse` is packaged correctly.
- For GraphBolt sparse minibatch sampling, route pipeline design to `../dataloading-graphbolt/`; this sub-skill covers the sparse matrix API and model math.
