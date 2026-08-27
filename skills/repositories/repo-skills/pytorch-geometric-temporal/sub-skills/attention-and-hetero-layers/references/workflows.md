# Attention and Heterogeneous Layer Workflows

## Purpose

Use these workflows to choose and wire attention-based temporal graph models and `HeteroGCLSTM`. API signatures and shapes are summarized in [api-reference.md](api-reference.md); failure recovery is in [troubleshooting.md](troubleshooting.md).

## Workflow 1: choose the smallest class that matches the task

1. **User has a traffic tensor and asks for STGCN.** Start with `STConv` if they need the STGCN spatio-temporal block; use `TemporalConv` only to debug or customize the temporal convolution sub-block.
2. **User asks for ASTGCN or spatial/temporal attention for traffic forecasting.** Use `ASTGCN` as the high-level model. Reach for `ChebConvAttention` only inside a custom ASTGCN-like module.
3. **User asks for MSTGCN.** Use `MSTGCN`; it has the same `[B, N, F, T]` family as ASTGCN but no explicit spatial/temporal attention inputs.
4. **User asks for GMAN.** Use `GMAN` and prepare spatial embeddings (`SE`) plus temporal integer codes (`TE`). Use `SpatioTemporalEmbedding` and `SpatioTemporalAttention` only when modifying GMAN internals.
5. **User asks for adaptive adjacency or multivariate time-series graph learning.** Use `MTGNN`; use `GraphConstructor` and `MixProp` for custom MTGNN-style components.
6. **User asks for skeleton/action or 2S-AGCN.** Use `AAGCN`; use `GraphAAGCN` to inspect or build the three-channel adjacency stack.
7. **User asks for temporal set prediction.** Use `DNNTSP`; ensure node rows are grouped by `items_total`.
8. **User has heterogeneous PyG snapshots.** Use `HeteroGCLSTM`; carry `h_dict`/`c_dict` across time steps.

## Workflow 2: convert common temporal tensors safely

Many users start with a stacked traffic tensor shaped `[snapshots, nodes, features]`, here called `raw_tnf`.

```python
# raw_tnf: [T, N, F]
raw_tnf = raw_tnf.float()

# TemporalConv/STConv expect [B, T, N, F].
x_stconv = raw_tnf.unsqueeze(0)

# ASTGCN/MSTGCN expect [B, N, F, T].
x_astgcn = raw_tnf.permute(1, 2, 0).unsqueeze(0).contiguous()

# MTGNN expects [B, in_dim, N, seq_length].
x_mtgnn = raw_tnf.permute(2, 1, 0).unsqueeze(0).contiguous()

# GMAN uses a scalar or channel-selected history series [B, num_his, N].
target_feature = 0
x_gman = raw_tnf[:, :, target_feature].unsqueeze(0).contiguous()
```

Rules of thumb:

- Do not feed `[T, N, F]` directly to any class in this sub-skill.
- For STGCN-style layers, time is the second axis: `[B, T, N, F]`.
- For ASTGCN/MSTGCN, node and feature axes precede time: `[B, N, F, T]`.
- For MTGNN/AAGCN, channel/feature is second: `[B, F, N, T]` for MTGNN and `[B, F, T, N]` for AAGCN.
- If the data came from temporal signal iterators or dataset loaders, let the owning data sub-skill choose the iterator/loader first, then convert the resulting snapshot tensors here.

## Workflow 3: STGCN block with `STConv`

Use `STConv` as a spatio-temporal block, not as a full forecasting model with loss/head included.

```python
import torch
from torch_geometric_temporal.nn.attention import STConv

B, T, N, F_in = 2, 6, 4, 3
x = torch.randn(B, T, N, F_in)
edge_index = torch.tensor(
    [[0, 1, 2, 3, 0, 2], [1, 2, 3, 0, 2, 0]], dtype=torch.long
)
edge_weight = torch.ones(edge_index.size(1))

block = STConv(
    num_nodes=N,
    in_channels=F_in,
    hidden_channels=8,
    out_channels=4,
    kernel_size=2,
    K=2,
    normalization="sym",
)
y = block(x, edge_index, edge_weight)
assert y.shape == (B, T - 2, N, 4)  # two temporal convolutions with kernel_size=2
```

Integration pattern:

- Add a forecasting head after `STConv`, for example flatten or pool over the remaining time axis and project to the target horizon.
- Keep `normalization="sym"` unless you have a custom wrapper that can pass `lambda_max` to Chebyshev graph convolutions.
- If `T - 2*(kernel_size-1) <= 0`, increase the input window or reduce `kernel_size`.

## Workflow 4: ASTGCN and MSTGCN traffic-forecasting layout

`ASTGCN` and `MSTGCN` use `[B, N, F, T]`, not the `[B, T, N, F]` order used by `STConv`.

```python
import torch
from torch_geometric_temporal.nn.attention import ASTGCN, MSTGCN

B, N, F_in, T = 2, 5, 2, 6
edge_index = torch.tensor(
    [[0, 1, 2, 3, 4, 0, 2], [1, 2, 3, 4, 0, 2, 0]], dtype=torch.long
)
x = torch.randn(B, N, F_in, T)

astgcn = ASTGCN(
    nb_block=1,
    in_channels=F_in,
    K=2,
    nb_chev_filter=8,
    nb_time_filter=8,
    time_strides=1,
    num_for_predict=3,
    len_input=T,
    num_of_vertices=N,
    normalization="sym",
)
y_ast = astgcn(x, edge_index)
assert y_ast.shape == (B, N, 3)

mstgcn = MSTGCN(
    nb_block=1,
    in_channels=F_in,
    K=2,
    nb_chev_filter=8,
    nb_time_filter=8,
    time_strides=1,
    num_for_predict=3,
    len_input=T,
)
y_mst = mstgcn(x, edge_index)
assert y_mst.shape == (B, N, 3)
```

Use a list of `edge_index` tensors when graph connectivity changes at every time step:

```python
edge_index_sequence = [edge_index for _ in range(T)]
y_ast_dynamic_edges = astgcn(x, edge_index_sequence)
```

Scale note: full ASTGCN/MSTGCN settings from traffic benchmarks can be memory- and time-heavy. Validate on tiny `B`, `N`, and `T` first, then scale.

## Workflow 5: GMAN temporal embeddings

GMAN differs from Chebyshev traffic models because it consumes temporal codes and spatial embeddings directly.

```python
import torch
from torch_geometric_temporal.nn.attention import GMAN

B, N = 2, 5
num_his, num_pred = 4, 2
K, d = 2, 4
steps_per_day = 24
D = K * d

X = torch.randn(B, num_his, N)
SE = torch.randn(N, D)

# TE[..., 0] = day of week in 0..6; TE[..., 1] = time of day in 0..steps_per_day-1.
TE = torch.zeros(B, num_his + num_pred, 2, dtype=torch.long)
TE[:, :, 0] = torch.arange(num_his + num_pred) % 7
TE[:, :, 1] = torch.arange(num_his + num_pred) % steps_per_day

model = GMAN(
    L=1,
    K=K,
    d=d,
    num_his=num_his,
    bn_decay=0.1,
    steps_per_day=steps_per_day,
    use_bias=True,
    mask=False,
)
y = model(X, SE, TE)
assert y.shape == (B, num_pred, N)
```

GMAN pitfalls:

- `num_pred` is inferred from `TE.shape[1] - num_his`; it is not a constructor argument.
- `TE` is cast to integer one-hot indices internally. Passing arbitrary floats can silently coerce to unexpected bins.
- Use `SpatioTemporalEmbedding` or `SpatioTemporalAttention` directly only when customizing GMAN internals.

## Workflow 6: MTGNN with adaptive or predefined adjacency

MTGNN is channel-first and asserts that `X_in.size(3)` equals the constructor `seq_length`.

```python
import torch
from torch_geometric_temporal.nn.attention import MTGNN

B, in_dim, N, seq_length = 2, 2, 6, 8
out_dim = 3
x = torch.randn(B, in_dim, N, seq_length)

model = MTGNN(
    gcn_true=True,
    build_adj=True,
    gcn_depth=2,
    num_nodes=N,
    kernel_set=[2, 3],
    kernel_size=3,
    dropout=0.1,
    subgraph_size=3,
    node_dim=8,
    dilation_exponential=1,
    conv_channels=8,
    residual_channels=8,
    skip_channels=16,
    end_channels=32,
    seq_length=seq_length,
    in_dim=in_dim,
    out_dim=out_dim,
    layers=1,
    propalpha=0.05,
    tanhalpha=3.0,
    layer_norm_affline=True,
)
raw = model(x)
assert raw.shape == (B, out_dim, N, 1)
y = raw.transpose(1, 3)  # common downstream shape: [B, 1, N, out_dim]
```

Use a predefined adjacency by instantiating `MTGNN` with the same constructor values as the example above, changing only `build_adj=False`, and then calling `model_no_build(x, A_tilde=A_tilde)` with `A_tilde: [N, N]`. Keep `gcn_true=True` only when an adjacency is available; otherwise set `gcn_true=False` for a temporal-convolution-only variant.

If using static node features, set `xd` in the constructor and pass `FE` with shape `[N, xd]`.

## Workflow 7: AAGCN and GraphAAGCN

`AAGCN` expects `[B, F, T, N]`. If the user starts with `[B, T, N, F]`, permute and make the tensor contiguous.

```python
import math
import torch
from torch_geometric_temporal.nn.attention import AAGCN, GraphAAGCN

B, T, N, F_in = 2, 5, 4, 3
x_btnf = torch.randn(B, T, N, F_in)
x = x_btnf.permute(0, 3, 1, 2).contiguous()  # [B, F, T, N]
edge_index = torch.tensor([[0, 1, 2, 3, 0], [1, 2, 3, 0, 2]], dtype=torch.long)

model = AAGCN(
    in_channels=F_in,
    out_channels=6,
    edge_index=edge_index,
    num_nodes=N,
    stride=2,
    adaptive=True,
    attention=True,
)
y = model(x)
assert y.shape == (B, 6, math.ceil(T / 2), N)

adj = GraphAAGCN(edge_index=edge_index, num_nodes=N).A
assert adj.shape == (3, N, N)
```

Use AAGCN for skeleton/action-style spatio-temporal graph convolutions, not ordinary traffic forecasting unless the user's graph/tensor semantics match this layout.

## Workflow 8: DNNTSP temporal set prediction

`DNNTSP` expects node rows grouped into batches of `items_total`.

```python
import torch
from torch_geometric_temporal.nn.attention import DNNTSP

items_total = 5
item_embedding_dim = 4
batch = 3
X = torch.randn(batch * items_total, item_embedding_dim)
edge_index = torch.tensor(
    [[0, 1, 2, 3, 4, 0, 5, 6, 7, 8], [1, 2, 3, 4, 0, 2, 6, 7, 8, 9]],
    dtype=torch.long,
)
edge_weight = torch.ones(edge_index.size(1))

model = DNNTSP(items_total=items_total, item_embedding_dim=item_embedding_dim, n_heads=2)
y = model(X, edge_index, edge_weight)
assert y.shape == (batch, items_total, item_embedding_dim)
```

The implementation may print intermediate shapes from helper modules. Treat that as noisy diagnostics unless it breaks a test harness.

## Workflow 9: HeteroGCLSTM snapshot loop

Use `HeteroGCLSTM` when each time step is a heterogeneous graph with `x_dict`, `edge_index_dict`, and metadata.

```python
import torch
from torch_geometric_temporal.nn.hetero import HeteroGCLSTM

x_dict = {
    "author": torch.randn(3, 2),
    "paper": torch.randn(4, 3),
}
edge_index_dict = {
    ("author", "writes", "paper"): torch.tensor([[0, 1, 2], [1, 2, 3]], dtype=torch.long),
    ("paper", "rev_writes", "author"): torch.tensor([[1, 2, 3], [0, 1, 2]], dtype=torch.long),
}
metadata = (list(x_dict.keys()), list(edge_index_dict.keys()))
layer = HeteroGCLSTM(
    in_channels_dict={"author": 2, "paper": 3},
    out_channels=5,
    metadata=metadata,
)

h_dict, c_dict = None, None
for _ in range(3):
    h_dict, c_dict = layer(x_dict, edge_index_dict, h_dict, c_dict)

assert h_dict["author"].shape == (3, 5)
assert h_dict["paper"].shape == (4, 5)
```

State rules:

- Carry `h_dict` and `c_dict` across consecutive snapshots from the same temporal sequence.
- Reset them to `None` or fresh zeros between independent sequences.
- Include reverse edge types or other incoming relations so each destination node type receives a `HeteroConv` update.
- For GPU, create explicit state dictionaries on the same device as each node type's features.

## Workflow 10: quick no-download smoke check

From this sub-skill directory, run:

```bash
python scripts/attention_hetero_smoke.py --help
python scripts/attention_hetero_smoke.py
```

The script uses tiny CPU tensors and checks `TemporalConv`, `STConv`, and `HeteroGCLSTM`. It is appropriate before drafting user code or after installing PyTorch Geometric Temporal in a fresh environment.
