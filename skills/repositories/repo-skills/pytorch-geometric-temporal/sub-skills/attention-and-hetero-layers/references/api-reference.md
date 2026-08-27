# Attention and Heterogeneous Layer API Reference

## Purpose

Use this reference when wiring PyTorch Geometric Temporal attention layers or `HeteroGCLSTM`. It records the public constructor and `forward` contracts verified from package exports, implementation behavior, and native synthetic shape checks. For task recipes, read [workflows.md](workflows.md). For errors and recovery, read [troubleshooting.md](troubleshooting.md).

## Imports

```python
from torch_geometric_temporal.nn.attention import (
    TemporalConv, STConv, ASTGCN, ChebConvAttention, MSTGCN, GMAN,
    SpatioTemporalEmbedding, SpatioTemporalAttention, MTGNN, MixProp,
    GraphConstructor, GraphAAGCN, AAGCN, DNNTSP,
)
from torch_geometric_temporal.nn.hetero import HeteroGCLSTM
```

## Layout cheat sheet

| Family | Input layout | Output layout | Notes |
| --- | --- | --- | --- |
| `TemporalConv` | `X: [B, T, N, F_in]` | `[B, T - (kernel_size - 1), N, F_out]` | Pure temporal gated-convolution block used by STGCN. |
| `STConv` | `X: [B, T, N, F_in]`, `edge_index: [2, E]` | `[B, T - 2*(kernel_size - 1), N, F_out]` | STGCN block; requires enough time steps for two temporal convolutions. |
| `ASTGCN` | `X: [B, N, F_in, T]`, `edge_index` tensor or list of length `T` | `[B, N, num_for_predict]` | High-level attention traffic-forecasting model. |
| `ChebConvAttention` | `x: [B, N, F_in]`, `spatial_attention: [B, N, N]` | `[B, N, F_out]` | Low-level ASTGCN building block. |
| `MSTGCN` | `X: [B, N, F_in, T]`, `edge_index` tensor or list | `[B, N, num_for_predict]` | High-level ASTGCN-like model without explicit attention modules. |
| `GMAN` | `X: [B, num_his, N]`, `SE: [N, K*d]`, `TE: [B, num_his + num_pred, 2]` | `[B, num_pred, N]` | `TE[..., 0]` is day-of-week, `TE[..., 1]` is time-of-day. |
| `SpatioTemporalEmbedding` | `SE: [N, D]`, `TE: [B, total_steps, 2]`, `T: int` | `[B, total_steps, N, D]` | GMAN embedding helper; usually `D = K*d`. |
| `SpatioTemporalAttention` | `X: [B, steps, N, K*d]`, `STE` same | `[B, steps, N, K*d]` | GMAN block helper. |
| `MTGNN` | `X_in: [B, in_dim, N, seq_length]` | raw `[B, out_dim, N, 1]` | Many examples transpose raw output to `[B, 1, N, out_dim]`. |
| `MixProp` | `X: [B, c_in, N, seq_len]`, `A: [N, N]` | `[B, c_out, N, seq_len]` | MTGNN helper for mix-hop propagation. |
| `GraphConstructor` | `idx: [M]`, optional `FE: [N, xd]` | `[M, M]` adjacency | MTGNN helper for adaptive adjacency/top-k graph learning. |
| `AAGCN` | `x: [B, F_in, T, N]` | `[B, F_out, ceil(T / stride), N]` | 2S-AGCN block for skeleton/action style sequences. |
| `GraphAAGCN` | `edge_index: [2, E]`, `num_nodes` | `.A: [3, N, N]` | Helper, not an `nn.Module`; creates self/inward/outward adjacency stack. |
| `DNNTSP` | `X: [batch*items_total, item_embedding_dim]` | `[batch, items_total, item_embedding_dim]` | Temporal set prediction model; first dimension must be divisible by `items_total`. |
| `HeteroGCLSTM` | `x_dict`, `edge_index_dict`, optional `h_dict`, `c_dict` | `(h_dict, c_dict)` | Dict keys are node types; state tensors are `[num_nodes_of_type, out_channels]`. |

## High-level models versus building blocks

| Class | Level | Typical role |
| --- | --- | --- |
| `STConv` | block-level component | STGCN spatio-temporal block; add a head/loss around it. |
| `ASTGCN`, `MSTGCN`, `GMAN`, `MTGNN`, `AAGCN`, `DNNTSP` | high-level model/block | Start here for named architecture prompts. |
| `TemporalConv`, `ChebConvAttention`, `SpatioTemporalEmbedding`, `SpatioTemporalAttention`, `MixProp`, `GraphConstructor`, `GraphAAGCN` | helper/building block | Use inside custom modules or for debugging layout issues. |
| `HeteroGCLSTM` | recurrent cell | Use in a snapshot loop over heterogeneous temporal graphs. |

## Public signatures and contracts

### `TemporalConv`

```python
TemporalConv(in_channels: int, out_channels: int, kernel_size: int = 3)
forward(X: torch.FloatTensor) -> torch.FloatTensor
```

- Input `X`: `[batch_size, input_time_steps, num_nodes, in_channels]`.
- Output: `[batch_size, input_time_steps - (kernel_size - 1), num_nodes, out_channels]`.
- It permutes internally to channel-first for `Conv2d` and then returns to `[B, T, N, F]`.

### `STConv`

```python
STConv(
    num_nodes: int,
    in_channels: int,
    hidden_channels: int,
    out_channels: int,
    kernel_size: int,
    K: int,
    normalization: str = "sym",
    bias: bool = True,
)
forward(
    X: torch.FloatTensor,
    edge_index: torch.LongTensor,
    edge_weight: torch.FloatTensor = None,
) -> torch.FloatTensor
```

- Input `X`: `[B, T, N, F_in]`.
- Output: `[B, T - 2*(kernel_size - 1), N, F_out]`.
- `edge_index` is `[2, E]`; `edge_weight` is `[E]` or omitted for an unweighted graph.
- Prefer `normalization="sym"`. The wrapper does not expose `lambda_max`, so non-symmetric Chebyshev normalization is a bad fit for this class.

### `ASTGCN`

```python
ASTGCN(
    nb_block: int,
    in_channels: int,
    K: int,
    nb_chev_filter: int,
    nb_time_filter: int,
    time_strides: int,
    num_for_predict: int,
    len_input: int,
    num_of_vertices: int,
    normalization: Optional[str] = None,
    bias: bool = True,
)
forward(X: torch.FloatTensor, edge_index: torch.LongTensor) -> torch.FloatTensor
```

- Input `X`: `[B, N, F_in, T_in]`.
- `edge_index` may be one static `[2, E]` tensor or a list of `[2, E_t]` tensors, one per time step.
- Output: `[B, N, num_for_predict]`.
- `normalization` may be `None`, `"sym"`, or `"rw"`; ASTGCN computes the largest Laplacian eigenvalue internally when needed.

### `ChebConvAttention`

```python
ChebConvAttention(
    in_channels: int,
    out_channels: int,
    K: int,
    normalization: Optional[str] = None,
    bias: bool = True,
    **kwargs,
)
forward(
    x: torch.FloatTensor,
    edge_index: torch.LongTensor,
    spatial_attention: torch.FloatTensor,
    edge_weight: Optional[torch.Tensor] = None,
    batch: Optional[torch.Tensor] = None,
    lambda_max: Optional[torch.Tensor] = None,
) -> torch.FloatTensor
```

- Input `x`: `[B, N, F_in]`; `spatial_attention`: `[B, N, N]`.
- Output: `[B, N, F_out]`.
- If `normalization` is not `"sym"`, pass `lambda_max` unless the caller is inside a wrapper that computes it.

### `MSTGCN`

```python
MSTGCN(
    nb_block: int,
    in_channels: int,
    K: int,
    nb_chev_filter: int,
    nb_time_filter: int,
    time_strides: int,
    num_for_predict: int,
    len_input: int,
)
forward(X: torch.FloatTensor, edge_index: torch.LongTensor) -> torch.FloatTensor
```

- Input `X`: `[B, N, F_in, T_in]`.
- `edge_index` may be one static `[2, E]` tensor or a list with one `[2, E_t]` tensor per time step.
- Output: `[B, N, num_for_predict]`.
- This is a high-level multi-component model; prefer tiny synthetic dimensions before scaling to full traffic data.

### `GMAN`

```python
GMAN(
    L: int,
    K: int,
    d: int,
    num_his: int,
    bn_decay: float,
    steps_per_day: int,
    use_bias: bool,
    mask: bool,
)
forward(X: torch.FloatTensor, SE: torch.FloatTensor, TE: torch.FloatTensor) -> torch.FloatTensor
```

- Input `X`: `[B, num_his, N]`.
- `SE`: spatial embedding `[N, K*d]`.
- `TE`: temporal embedding codes `[B, num_his + num_pred, 2]`; column 0 is day of week, column 1 is time of day. Values are cast to integer indices and wrapped by modulo, so supply clean integer-coded tensors to avoid silent coercion.
- Output: `[B, num_pred, N]`, where `num_pred = TE.shape[1] - num_his`.

### `SpatioTemporalEmbedding`

```python
SpatioTemporalEmbedding(D: int, bn_decay: float, steps_per_day: int, use_bias: bool = True)
forward(SE: torch.FloatTensor, TE: torch.FloatTensor, T: int) -> torch.FloatTensor
```

- `SE`: `[N, D]`; `TE`: `[B, total_steps, 2]`; `T` is usually `steps_per_day`.
- Output: `[B, total_steps, N, D]`.
- In GMAN, `D = K*d`.

### `SpatioTemporalAttention`

```python
SpatioTemporalAttention(K: int, d: int, bn_decay: float, mask: bool)
forward(X: torch.FloatTensor, STE: torch.FloatTensor) -> torch.FloatTensor
```

- Input `X` and `STE`: `[B, steps, N, K*d]`.
- Output: `[B, steps, N, K*d]`.
- Use this only when customizing GMAN-like attention blocks.

### `MTGNN`

```python
MTGNN(
    gcn_true: bool,
    build_adj: bool,
    gcn_depth: int,
    num_nodes: int,
    kernel_set: list,
    kernel_size: int,
    dropout: float,
    subgraph_size: int,
    node_dim: int,
    dilation_exponential: int,
    conv_channels: int,
    residual_channels: int,
    skip_channels: int,
    end_channels: int,
    seq_length: int,
    in_dim: int,
    out_dim: int,
    layers: int,
    propalpha: float,
    tanhalpha: float,
    layer_norm_affline: bool,
    xd: Optional[int] = None,
)
forward(
    X_in: torch.FloatTensor,
    A_tilde: Optional[torch.FloatTensor] = None,
    idx: Optional[torch.LongTensor] = None,
    FE: Optional[torch.FloatTensor] = None,
) -> torch.FloatTensor
```

- Input `X_in`: `[B, in_dim, N, seq_length]`; `seq_length` must equal the constructor value.
- If `build_adj=True`, the internal `GraphConstructor` builds adjacency from node embeddings or optional static features `FE`.
- If `build_adj=False` and `gcn_true=True`, pass `A_tilde: [N, N]`.
- Raw output is `[B, out_dim, N, 1]`; transpose if your training code expects `[B, 1, N, out_dim]` or `[B, N, out_dim]`.

### `MixProp`

```python
MixProp(c_in: int, c_out: int, gdep: int, dropout: float, alpha: float)
forward(X: torch.FloatTensor, A: torch.FloatTensor) -> torch.FloatTensor
```

- Input `X`: `[B, c_in, N, seq_len]`; adjacency `A`: `[N, N]`.
- Output: `[B, c_out, N, seq_len]`.
- `alpha` controls how much root-node state is retained during propagation.

### `GraphConstructor`

```python
GraphConstructor(nnodes: int, k: int, dim: int, alpha: float, xd: Optional[int] = None)
forward(idx: torch.LongTensor, FE: Optional[torch.FloatTensor] = None) -> torch.FloatTensor
```

- `idx` is a node-index tensor for all nodes or a selected subset.
- With `xd=None`, the constructor learns node embeddings. With `xd` set, pass `FE` whose second dimension equals `xd`.
- Output is a dense top-k learned adjacency for the selected `idx` nodes.

### `GraphAAGCN` and `AAGCN`

```python
GraphAAGCN(edge_index: torch.LongTensor, num_nodes: int)
# exposes .A after construction

AAGCN(
    in_channels: int,
    out_channels: int,
    edge_index: torch.LongTensor,
    num_nodes: int,
    stride: int = 1,
    residual: bool = True,
    adaptive: bool = True,
    attention: bool = True,
)
forward(x) -> torch.FloatTensor
```

- `GraphAAGCN` is a helper object, not a PyTorch module. It creates `.A` with shape `[3, N, N]` for self, inward, and outward normalized adjacency channels.
- `AAGCN` input `x`: `[B, F_in, T, N]`.
- `AAGCN` output: `[B, F_out, ceil(T / stride), N]` for the tested padding/stride behavior.
- Make tensors contiguous after `permute` before passing them into `AAGCN` if later operations complain about non-contiguous layout.

### `DNNTSP`

```python
DNNTSP(items_total: int, item_embedding_dim: int, n_heads: int)
forward(
    X: torch.FloatTensor,
    edge_index: torch.LongTensor,
    edge_weight: torch.FloatTensor = None,
)
```

- Input `X` should contain `batch * items_total` rows and `item_embedding_dim` features.
- Output: `[batch, items_total, item_embedding_dim]`.
- The implementation includes internal diagnostic `print` calls in helper modules; do not treat printed shapes as errors during exploratory smoke runs.

### `HeteroGCLSTM`

```python
HeteroGCLSTM(
    in_channels_dict: dict,
    out_channels: int,
    metadata: tuple,
    bias: bool = True,
)
forward(x_dict, edge_index_dict, h_dict=None, c_dict=None)
```

- `in_channels_dict`: maps each node type to its feature dimension.
- `metadata`: PyG metadata tuple `(node_types, edge_types)`, usually from a `HeteroData` snapshot.
- `x_dict`: maps node type to `[num_nodes_of_type, in_channels_dict[node_type]]`.
- `edge_index_dict`: maps edge type tuples `(src_type, relation, dst_type)` to `[2, E]` tensors.
- `h_dict` and `c_dict` are optional. If omitted, the layer initializes zero states with shape `[num_nodes_of_type, out_channels]`.
- Return value is `(h_dict, c_dict)`, each keyed by node type.

## State and device notes for `HeteroGCLSTM`

- For CPU runs, omitting `h_dict` and `c_dict` is fine.
- For GPU runs, create explicit `h_dict` and `c_dict` on the same device as each node type's features before calling the layer; otherwise zero-state initialization may use the wrong device.
- Every node type in `in_channels_dict` should receive messages from at least one edge type in `edge_index_dict`; add reverse edge types when needed so `HeteroConv` returns outputs for all node types.
