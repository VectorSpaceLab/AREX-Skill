# Recurrent layer API reference

This reference summarizes the recurrent graph layers exported from `torch_geometric_temporal.nn.recurrent`. Use it to choose the layer and to check the shape/state contract before writing a model `forward` method.

## Shared tensor conventions

| Symbol | Expected shape and dtype | Notes |
| --- | --- | --- |
| `N` | scalar | Number of nodes in one graph. |
| `E` | scalar | Number of edges. |
| `F` | scalar | Input feature channels (`in_channels`). |
| `O` | scalar | Output or hidden channels (`out_channels` or `hidden_size`). |
| `B` | scalar | Batch size for batch-aware recurrent layers. |
| `T` | scalar | Sequence length or number of periods, depending on the layer. |
| `X` | usually `torch.float32` | Ordinary recurrent cells use `[N, F]`; batch-aware variants use the layouts in the layer table. |
| `edge_index` | `torch.long`, `[2, E]` | Source/target COO indices for a single graph topology. Batch-specific expansion is internal only for layers that support it. |
| `edge_weight` | float, `[E]` | Optional in many forward signatures; use ones for unweighted synthetic diffusion/batched checks when the implementation needs explicit weights. |
| `H` | float hidden state | Same node/batch leading dimensions as the layer output, with trailing dimension `O`. Pass `None` to reset state. |
| `C` | float cell state | LSTM-style state with the same shape as `H`. Pass `None` together with `H` to reset. |
| `lambda_max` | scalar or `[num_graphs]` | Required by Chebyshev layers when `normalization` is not symmetric. Use a scalar/0-D tensor for one graph. The underlying Chebyshev docs mention `[num_graphs]` for mini-batches, but these recurrent wrappers do not expose a `batch` argument; verify custom mini-batching before relying on it. |
| `batch` | not a recurrent forward argument | These recurrent wrappers do not expose a PyG `batch` vector. Batch-aware variants use an explicit leading `B` dimension; for Chebyshev wrappers, prefer single-graph snapshot loops with scalar `lambda_max` unless you have separately verified the exact mini-batch behavior.
| `periods` | last tensor axis for A3 variants | `A3TGCN` uses `X [N, F, periods]`; `A3TGCN2` uses `X [B, N, F, periods]`; constructor `periods` must equal `X.size(-1)`. |

For ordinary temporal-signal snapshots, a snapshot exposes `snapshot.x`, `snapshot.edge_index`, `snapshot.edge_attr`, and `snapshot.y`; route iterator construction and splitting to the signal/data sub-skills, then use this reference for the recurrent layer call.

## Constructor and forward signatures

| Layer | Constructor | Forward call | Input layout | Return shape/state |
| --- | --- | --- | --- | --- |
| `GConvGRU` | `GConvGRU(in_channels, out_channels, K, normalization="sym", bias=True)` | `layer(X, edge_index, edge_weight=None, H=None, lambda_max=None)` | `X [N, F]`; `H [N, O]` when supplied. | `H [N, O]`. |
| `GConvLSTM` | `GConvLSTM(in_channels, out_channels, K, normalization="sym", bias=True)` | `layer(X, edge_index, edge_weight=None, H=None, C=None, lambda_max=None)` | `X [N, F]`; `H, C [N, O]` when supplied. | `(H, C)`, each `[N, O]`. |
| `GCLSTM` | `GCLSTM(in_channels, out_channels, K, normalization="sym", bias=True)` | `layer(X, edge_index, edge_weight=None, H=None, C=None, lambda_max=None)` | `X [N, F]`; `H, C [N, O]` when supplied. | `(H, C)`, each `[N, O]`. |
| `LRGCN` | `LRGCN(in_channels, out_channels, num_relations, num_bases)` | `layer(X, edge_index, edge_type, H=None, C=None)` | `X [N, F]`; `edge_type [E]` with integer relation ids; `H, C [N, O]`. | `(H, C)`, each `[N, O]`. |
| `DyGrEncoder` | `DyGrEncoder(conv_out_channels, conv_num_layers, conv_aggr, lstm_out_channels, lstm_num_layers)` | `layer(X, edge_index, edge_weight=None, H=None, C=None)` | `X [N, F]`; input feature width must be compatible with `GatedGraphConv` and is commonly `F <= conv_out_channels`; for the one-layer LSTM path, `H, C [N, lstm_out_channels]`. | `(H_tilde, H, C)`; with `lstm_num_layers=1`, each `[N, lstm_out_channels]`. |
| `EvolveGCNH` | `EvolveGCNH(num_of_nodes, in_channels, improved=False, cached=False, normalize=True, add_self_loops=True)` | `layer(X, edge_index, edge_weight=None)` | `X [N, F]` where `N == num_of_nodes` and `F == in_channels`. | Updated `X [N, F]`; recurrent weight is stored internally until `reinitialize_weight()`. |
| `EvolveGCNO` | `EvolveGCNO(in_channels, improved=False, cached=False, normalize=True, add_self_loops=True)` | `layer(X, edge_index, edge_weight=None)` | `X [N, F]` where `F == in_channels`. | Updated `X [N, F]`; recurrent weight is stored internally until `reinitialize_weight()`. |
| `DCRNN` | `DCRNN(in_channels, out_channels, K, bias=True)` | `layer(X, edge_index, edge_weight=None, H=None)` | `X [N, F]`; `H [N, O]`. | `H [N, O]`. |
| `BatchedDCRNN` | `BatchedDCRNN(in_channels, out_channels, K, bias=True)` | `layer(X, edge_index, edge_weight)` | `X [B, T, N, F]`; `edge_index [2, E]`; explicit `edge_weight [E]` is required by the batched implementation. | Output sequence `[B, T, N, O]`; hidden state resets inside each `forward`. |
| `TGCN` | `TGCN(in_channels, out_channels, improved=False, cached=False, add_self_loops=True)` | `layer(X, edge_index, edge_weight=None, H=None)` | `X [N, F]`; `H [N, O]`. | `H [N, O]`. |
| `TGCN2` | `TGCN2(in_channels, out_channels, batch_size, improved=False, cached=False, add_self_loops=True)` | `layer(X, edge_index, edge_weight=None, H=None)` | `X [B, N, F]`; `H [B, N, O]`. The `batch_size` constructor argument is retained for compatibility; the current hidden-state initialization infers `B` from `X`. | `H [B, N, O]`. |
| `A3TGCN` | `A3TGCN(in_channels, out_channels, periods, improved=False, cached=False, add_self_loops=True)` | `layer(X, edge_index, edge_weight=None, H=None)` | `X [N, F, periods]`; `H [N, O]`. | Weighted-sum hidden state `[N, O]`. |
| `A3TGCN2` | `A3TGCN2(in_channels, out_channels, periods, batch_size, improved=False, cached=False, add_self_loops=True)` | `layer(X, edge_index, edge_weight=None, H=None)` | `X [B, N, F, periods]`; `H [B, N, O]`. | Weighted-sum hidden state `[B, N, O]`. |
| `MPNNLSTM` | `MPNNLSTM(in_channels, hidden_size, num_nodes, window, dropout)` | `layer(X, edge_index, edge_weight)` | Flattened temporal-window input. For `window=1`, `X [N, F]` works. For `window>1`, shape is flattened from `[B, window, num_nodes, F]` into `[B * window * num_nodes, F]`. | `H [B * num_nodes, 2 * hidden_size + in_channels + window - 1]`; with `B=1, window=1`, `[N, 2 * hidden_size + F]`. |
| `AGCRN` | `AGCRN(number_of_nodes, in_channels, out_channels, K, embedding_dimensions)` | `layer(X, E, H=None)` | `X [B, N, F]`; node embeddings `E [N, embedding_dimensions]`; `H [B, N, O]`. | `H [B, N, O]`. |

## Layer-specific notes

### Chebyshev recurrent layers

`GConvGRU`, `GConvLSTM`, and `GCLSTM` wrap PyG `ChebConv`. With the default `normalization="sym"`, `lambda_max` may be omitted. With `normalization=None` or `normalization="rw"`, pass `lambda_max` to every recurrent step. In a single-graph snapshot loop a scalar tensor is enough; in a mini-batch scenario pass one value per graph.

### LSTM-style state returns

`GConvLSTM`, `GCLSTM`, `LRGCN`, and `DyGrEncoder` return cell state as well as hidden state. Reuse both state tensors together:

```python
h, c = None, None
for snapshot in train_snapshots:
    h, c = layer(snapshot.x, snapshot.edge_index, snapshot.edge_attr, h, c)
```

If only one of `H` or `C` is available, reset both to `None` or reconstruct both. `DyGrEncoder` explicitly rejects calls where exactly one of `H` or `C` is provided.

### Evolution layers keep internal state

`EvolveGCNH` and `EvolveGCNO` do not expose `H`/`C` arguments. They update an internal recurrent weight across calls. Use the same module across snapshots in one sequence, and call `reinitialize_weight()` before a new independent sequence or before a smoke test that must be order-independent.

### Batch-aware recurrent variants

- `TGCN2` and `A3TGCN2` keep the graph topology unbatched (`edge_index [2, E]`) and batch node features in the leading dimension.
- `BatchedDCRNN` consumes a whole sequence at once and internally replicates the graph for each batch element. It also caches expanded edges for repeated calls with the same batch size and graph.
- If using a `DataLoader` with `drop_last=False`, the final batch can have a smaller `B`. That is acceptable for `TGCN2` hidden-state initialization, but your own persistent `H` tensor and prediction head must be reset or resized for the smaller batch.

### Period-aware attention recurrent variants

`A3TGCN` and `A3TGCN2` attend across the last axis of `X`. The constructor `periods` must equal the last dimension used in `forward`. For a non-batched snapshot with lags stored as columns, reshape from `[N, periods]` to `[N, 1, periods]` and instantiate with `in_channels=1`.

### AGCRN node embeddings

`AGCRN` does not use `edge_index` or `edge_weight`; it builds adaptive supports from the learnable node embedding matrix `E`. Make `E` an `nn.Parameter` in the surrounding model if the embeddings should train:

```python
self.node_embeddings = torch.nn.Parameter(torch.empty(num_nodes, embedding_dimensions))
torch.nn.init.xavier_uniform_(self.node_embeddings)
h = self.recurrent(x, self.node_embeddings, h)
```

### Heads and losses belong outside the recurrent layer

The recurrent output is usually a hidden representation. Common examples add nonlinearities and task heads explicitly:

```python
h = self.recurrent(x, edge_index, edge_weight, h)
y_hat = self.linear(torch.nn.functional.relu(h))
loss = torch.nn.functional.mse_loss(y_hat, y)
```

Do not assume that the recurrent layer already applies `relu`, dropout, final `Linear`, `log_softmax`, MSE, or task-specific normalization.
