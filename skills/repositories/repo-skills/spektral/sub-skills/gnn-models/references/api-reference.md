# GNN Model API Reference

This reference summarizes Spektral 1.3.1 model, layer, and graph-utility surfaces relevant to GNN construction.

## Ready-made models

| Object | Signature | Use |
| --- | --- | --- |
| `spektral.models.GCN` | `(n_labels, channels=16, activation='relu', output_activation='softmax', use_bias=False, dropout_rate=0.5, l2_reg=0.00025, **kwargs)` | Two-layer GCN model for node-level predictions; accepts `(x, a)` or `(x, a, i)` |
| `spektral.models.GeneralGNN` | `(output, activation=None, hidden=256, message_passing=4, pre_process=2, post_process=2, connectivity='cat', batch_norm=True, dropout=0.0, aggregate='sum', hidden_activation='prelu', pool='sum')` | General-purpose GNN from design-space defaults; supports global pooling or node-level output with `pool=None` |
| `spektral.models.GNNExplainer` | `(model, n_hops=None, preprocess=None, graph_level=False, verbose=False, learning_rate=0.01, a_size_coef=0.0005, x_size_coef=0.1, a_entropy_coef=0.1, x_entropy_coef=0.1, laplacian_coef=0.0)` | Learns feature/edge masks to explain node or graph predictions |

`GeneralGNN` configuration notes:

- `connectivity`: `None`, `'sum'`, or `'cat'`.
- `aggregate`: one of the supported scatter aggregations such as `'sum'`, `'mean'`, `'max'`, `'min'`, or `'prod'`.
- `pool`: `None`, `'sum'`, `'avg'`, `'max'`, `'attn'`, `'attn_sum'`, or `'sort'` through global pooling helpers.

## Core layer base classes

| Object | Signature | Use |
| --- | --- | --- |
| `Conv` | `(**kwargs)` | Base for dense/mixed/batch-capable graph convolution layers; subclasses implement `call()` and `config` |
| `MessagePassing` | `(aggregate='sum', **kwargs)` | Base for sparse single/disjoint message passing; override `message`, `aggregate`, and/or `update` |
| `GraphMasking` | Keras layer args | Removes the last mask feature inserted by `BatchLoader(mask=True)` and starts mask propagation |
| `Disjoint2Batch` | Keras layer args | Converts sparse disjoint mode tensors to dense batch tensors |
| `SparseDropout` | `(rate, noise_shape=None, seed=None, **kwargs)` | Dropout for TensorFlow sparse tensors |

`MessagePassing.propagate(x, a, e=None, **kwargs)` expects `a` to be a TensorFlow `SparseTensor`. During propagation the layer exposes `index_sources`, `index_targets`, and `n_nodes`.

## Common convolution signatures

| Layer | Signature highlights |
| --- | --- |
| `GCNConv` | `(channels, activation=None, use_bias=True, kernel_initializer='glorot_uniform', ...)` |
| `GeneralConv` | `(channels=256, batch_norm=True, dropout=0.0, aggregate='sum', activation='prelu', use_bias=True, ...)` |
| `GATConv` | `(channels, attn_heads=1, concat_heads=True, dropout_rate=0.5, return_attn_coef=False, add_self_loops=True, ...)` |
| `ChebConv` | `(channels, K=1, activation=None, use_bias=True, ...)` |
| `ARMAConv` | `(channels, order=1, iterations=1, share_weights=False, gcn_activation='relu', dropout_rate=0.0, ...)` |
| `APPNPConv` | `(channels, alpha=0.2, propagations=1, mlp_hidden=None, mlp_activation='relu', dropout_rate=0.0, ...)` |
| `ECCConv` | `(channels, kernel_network=None, root=True, activation=None, use_bias=True, ...)` |
| `GINConv` | `(channels, epsilon=None, mlp_hidden=None, mlp_activation='relu', mlp_batchnorm=True, aggregate='sum', ...)` |
| `GraphSageConv` | `(channels, aggregate='mean', activation=None, use_bias=True, ...)` |
| `XENetConv` | `(stack_channels, node_channels, edge_channels, attention=True, node_activation=None, edge_activation=None, aggregate='sum', ...)` |

See `references/layer-catalog.md` for mode support and edge-feature notes.

## Pooling and readout signatures

| Layer | Signature highlights | Use |
| --- | --- | --- |
| `GlobalSumPool`, `GlobalAvgPool`, `GlobalMaxPool` | `(**kwargs)` | Global graph readout for single/disjoint/mixed/batch modes |
| `GlobalAttentionPool` | `(channels, kernel_initializer='glorot_uniform', ...)` | Gated attention readout |
| `GlobalAttnSumPool` | `(attn_kernel_initializer='glorot_uniform', ...)` | Node-attention sum readout |
| `SortPool` | `(k, **kwargs)` | Sort and keep top `k` nodes |
| `MinCutPool` | `(k, mlp_hidden=None, mlp_activation='relu', return_selection=False, ...)` | Dense pooling for single/batch |
| `DiffPool` | `(k, channels=None, return_selection=False, activation=None, ...)` | Differentiable dense pooling |
| `TopKPool`, `SAGPool` | `(ratio, return_selection=False, ...)` | Selection pooling for sparse-style workflows |

## Graph utility signatures

| Function | Signature | Use |
| --- | --- | --- |
| `spektral.utils.convolution.degree_matrix` | `(A)` | Degree matrix |
| `degree_power` | `(A, k)` | Degree matrix power |
| `normalized_adjacency` | `(A, symmetric=True)` | Adjacency normalization |
| `laplacian` | `(A)` | Graph Laplacian |
| `normalized_laplacian` | `(A, symmetric=True)` | Normalized Laplacian |
| `rescale_laplacian` | `(L, lmax=None)` | Rescale Laplacian for Chebyshev filters |
| `gcn_filter` | `(A, symmetric=True)` | GCN preprocessing with self-loops |
| `incidence_matrix` | `(adjacency)` | Incidence matrix for one or batched graph |
| `line_graph` | `(incidence)` | Line graph adjacency from incidence |
| `chebyshev_polynomial` | `(X, k)` | Chebyshev polynomial sequence |
| `chebyshev_filter` | `(A, k, symmetric=True)` | Chebyshev filter preprocessing |
| `spektral.utils.sparse.sp_matrix_to_sp_tensor` | `(x)` | SciPy sparse matrix to TensorFlow sparse tensor |
| `sp_batch_to_sp_tensor` | `(a_list)` | List of same-shape sparse matrices to rank-3 sparse tensor |
| `edge_index_to_matrix` | `(edge_index, edge_weight, edge_features=None, shape=None)` | COO edge index to adjacency and optional sorted edge features |

## I/O and logging helpers

- `spektral.utils.io` includes `load_binary`, `dump_binary`, CSV, DOT, NPY, TXT, OFF, and SDF readers/writers.
- `spektral.utils.logging` includes `init_logging`, `log`, `tic`, `toc`, and `model_to_str`.
- `spektral.utils.misc` includes `pad_jagged_array`, `one_hot`, `label_to_one_hot`, and `flatten_list`.
