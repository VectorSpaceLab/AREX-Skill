# Recurrent layer workflows

Use these workflows after another sub-skill has produced temporal snapshots or tensors. They distill the recurring patterns used by the package examples and tests while avoiding network downloads and long training runs.

## 1. Snapshot forecasting loop with an explicit head

Most non-batched recurrent examples follow this structure: a recurrent layer converts one snapshot into a hidden representation, a nonlinearity and `torch.nn.Linear` head map hidden features to the task target, and an outer training loop accumulates loss over snapshots.

```python
import torch
import torch.nn.functional as F
from torch_geometric_temporal.nn.recurrent import DCRNN  # or GConvGRU, TGCN, ...

class RecurrentForecaster(torch.nn.Module):
    def __init__(self, node_features: int, hidden: int = 32, target_dim: int = 1):
        super().__init__()
        self.recurrent = DCRNN(node_features, hidden, K=1)
        self.head = torch.nn.Linear(hidden, target_dim)

    def forward(self, x, edge_index, edge_weight=None, h=None):
        h = self.recurrent(x, edge_index, edge_weight, h)
        y_hat = self.head(F.relu(h))
        return y_hat, h

model = RecurrentForecaster(node_features=4)
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

model.train()
h = None  # preserve within this sequence; set to None again for an independent sequence
loss = 0.0
for t, snapshot in enumerate(train_snapshots):
    y_hat, h = model(snapshot.x, snapshot.edge_index, snapshot.edge_attr, h)
    loss = loss + F.mse_loss(y_hat, snapshot.y.view_as(y_hat))
loss = loss / (t + 1)
loss.backward()
optimizer.step()
optimizer.zero_grad()
```

Key decisions:

- Preserve `h` across snapshots when the snapshots are consecutive steps in one temporal sequence and gradients across the sequence are intentional.
- Reset `h = None` before a new independent graph sequence, a validation/test segment that must not carry training state, or a mini-batch whose node order/count changed.
- Detach `h = h.detach()` between long truncated-BPTT chunks if you need persistent state but do not want gradients through the entire history.
- Keep the final head outside the recurrent cell. The layer output is a hidden representation, not a finished regression/classification output.

## 2. LSTM-style snapshot loop (`GConvLSTM`, `GCLSTM`, `LRGCN`, `DyGrEncoder`)

LSTM-style cells need hidden and cell state. Reuse or reset them together.

```python
from torch_geometric_temporal.nn.recurrent import GConvLSTM

class LSTMForecaster(torch.nn.Module):
    def __init__(self, node_features: int, hidden: int = 32):
        super().__init__()
        self.recurrent = GConvLSTM(node_features, hidden, K=2)
        self.head = torch.nn.Linear(hidden, 1)

    def forward(self, x, edge_index, edge_weight=None, h=None, c=None, lambda_max=None):
        h, c = self.recurrent(x, edge_index, edge_weight, h, c, lambda_max)
        return self.head(F.relu(h)), h, c

h, c = None, None
for snapshot in train_snapshots:
    y_hat, h, c = model(snapshot.x, snapshot.edge_index, snapshot.edge_attr, h, c)
```

For `LRGCN`, replace `edge_weight` with `edge_type`, a long tensor of relation ids shaped `[num_edges]`. For `DyGrEncoder`, the recurrent call returns `(h_tilde, h, c)`; use `h_tilde` or `h` as the representation passed to the head, and pass both returned states to the next step.

## 3. Chebyshev `lambda_max` workflow

When `GConvGRU`, `GConvLSTM`, or `GCLSTM` uses the default `normalization="sym"`, you can omit `lambda_max`. If you set `normalization=None` or `normalization="rw"`, compute or supply the largest Laplacian eigenvalue for the graph and pass it on every step.

```python
from torch_geometric.transforms import LaplacianLambdaMax
from torch_geometric.data import Data

transform = LaplacianLambdaMax(normalization="rw")
data = transform(Data(x=x, edge_index=edge_index, edge_weight=edge_weight))
h = layer(x, edge_index, edge_weight, h, lambda_max=data.lambda_max)
```

For one graph reused across temporal snapshots, a scalar tensor is enough. The underlying Chebyshev convolution API documents one `lambda_max` value per graph for mini-batches, but these recurrent wrappers do not expose a separate `batch` argument; prefer scalar single-graph snapshot loops unless you have verified a custom batching path.

## 4. Period-aware `A3TGCN` pattern

`A3TGCN` attends over the last axis of `X` and outputs one hidden state per node. A common single-graph pattern turns lag columns into a singleton feature channel plus `periods`:

```python
from torch_geometric_temporal.nn.recurrent import A3TGCN

class A3Forecaster(torch.nn.Module):
    def __init__(self, periods: int, hidden: int = 32):
        super().__init__()
        self.recurrent = A3TGCN(in_channels=1, out_channels=hidden, periods=periods)
        self.head = torch.nn.Linear(hidden, 1)

    def forward(self, x_lags, edge_index, edge_weight=None, h=None):
        # x_lags: [N, periods]
        x_periods = x_lags.view(x_lags.size(0), 1, x_lags.size(1))
        h = self.recurrent(x_periods, edge_index, edge_weight, h)
        return self.head(F.relu(h)), h
```

Use `A3TGCN` for non-batched snapshots shaped `[N, F, periods]`. Do not feed `[B, N, F, periods]` into `A3TGCN`; use `A3TGCN2` for that layout.

## 5. Batched `TGCN2` and `A3TGCN2` patterns

The batch-aware variants keep the graph topology static and add a leading batch dimension to node features and states.

### Batched sequence loop with `TGCN2`

```python
from torch_geometric_temporal.nn.recurrent import TGCN2

class BatchedTGCNForecaster(torch.nn.Module):
    def __init__(self, in_channels: int, hidden: int, target_dim: int, batch_size: int):
        super().__init__()
        self.recurrent = TGCN2(in_channels, hidden, batch_size=batch_size)
        self.head = torch.nn.Linear(hidden, target_dim)

    def forward(self, x, edge_index, edge_weight=None, h=None):
        # x: [B, N, F, T]
        outputs = []
        for t in range(x.size(-1)):
            h = self.recurrent(x[..., t], edge_index, edge_weight, h)  # [B, N, hidden]
            outputs.append(self.head(F.relu(h)).unsqueeze(1))          # [B, 1, N, target_dim]
        return torch.cat(outputs, dim=1), h                            # [B, T, N, target_dim]
```

If a `DataLoader` produces a smaller final batch, either set `drop_last=True` or reset `h=None` when `x.size(0)` changes.

### Single-shot batched-period prediction with `A3TGCN2`

```python
from torch_geometric_temporal.nn.recurrent import A3TGCN2

class BatchedA3Forecaster(torch.nn.Module):
    def __init__(self, in_channels: int, periods: int, hidden: int, batch_size: int):
        super().__init__()
        self.recurrent = A3TGCN2(in_channels, hidden, periods=periods, batch_size=batch_size)
        self.head = torch.nn.Linear(hidden, periods)

    def forward(self, x, edge_index, edge_weight=None, h=None):
        # x: [B, N, F, periods]
        h = self.recurrent(x, edge_index, edge_weight, h)  # [B, N, hidden]
        return self.head(F.relu(h)), h                     # [B, N, periods]
```

This pattern is useful when the target is a vector of prediction horizons per node. Keep `periods == x.size(-1)` and align targets as `[B, N, periods]` unless your loss expects a different layout.

## 6. `BatchedDCRNN` sequence-to-sequence smoke pattern

`BatchedDCRNN` consumes the full input sequence at once and returns a hidden sequence. It does not accept an external hidden state.

```python
from torch_geometric_temporal.nn.recurrent import BatchedDCRNN

class BatchedDCRNNForecaster(torch.nn.Module):
    def __init__(self, in_channels: int, hidden: int, target_dim: int):
        super().__init__()
        self.recurrent = BatchedDCRNN(in_channels, hidden, K=2)
        self.head = torch.nn.Linear(hidden, target_dim)

    def forward(self, x_seq, edge_index, edge_weight):
        # x_seq: [B, T, N, F]
        h_seq = self.recurrent(x_seq, edge_index, edge_weight)  # [B, T, N, hidden]
        return self.head(F.relu(h_seq))                         # [B, T, N, target_dim]
```

Pass explicit `edge_weight`; for a synthetic unweighted graph use `torch.ones(edge_index.size(1))`.

## 7. `AGCRN` pattern with trainable node embeddings

`AGCRN` learns adaptive supports from node embeddings and uses batch-shaped node features.

```python
from torch_geometric_temporal.nn.recurrent import AGCRN

class AGCRNForecaster(torch.nn.Module):
    def __init__(self, num_nodes: int, in_channels: int, hidden: int, emb_dim: int):
        super().__init__()
        self.emb = torch.nn.Parameter(torch.empty(num_nodes, emb_dim))
        torch.nn.init.xavier_uniform_(self.emb)
        self.recurrent = AGCRN(num_nodes, in_channels, hidden, K=2, embedding_dimensions=emb_dim)
        self.head = torch.nn.Linear(hidden, 1)

    def forward(self, x, h=None):
        # x: [B, N, F]
        h = self.recurrent(x, self.emb, h)
        return self.head(F.relu(h)), h
```

The node count in `x`, `self.emb`, and the `AGCRN(number_of_nodes=...)` constructor must match.

## 8. `MPNNLSTM` window workflow

`MPNNLSTM` expects a flattened temporal window. For the simple single-window case, pass ordinary node features:

```python
layer = MPNNLSTM(in_channels=F, hidden_size=32, num_nodes=N, window=1, dropout=0.0)
h = layer(x, edge_index, edge_weight)  # [N, 2 * 32 + F]
y_hat = linear(F.relu(h))
```

For `window>1`, construct data as `[B, window, N, F]` and flatten it to `[B * window * N, F]` before the layer. The returned representation is `[B * N, 2 * hidden_size + F + window - 1]`, so the head input dimension changes with `window`.

## 9. Optional PyTorch Lightning caveats

Lightning integration is optional. If the environment does not already include Lightning, do not install it just to use core recurrent layers. When Lightning is available:

- A `LightningModule` can wrap the same recurrent/head pattern shown above.
- The training and validation steps must receive individual temporal snapshots or a collated representation whose fields match the layer layout.
- Hidden state is normally reset per `training_step` unless you deliberately manage state across batches.
- Early-stopping mode and monitor names must match the metric you log.

For core package smoke tests, prefer the bundled CPU script because it requires no Lightning, no network, and no long training.

## 10. Run the bundled synthetic smoke first

Use the bundled script to verify imports, shapes, heads, losses, and optimizer steps before adapting large examples:

```bash
python scripts/recurrent_forecasting_smoke.py --help
python scripts/recurrent_forecasting_smoke.py --layer gconvgru --train-steps 2
python scripts/recurrent_forecasting_smoke.py --layer all --train-steps 1
```

The smoke script uses synthetic CPU tensors and tiny graphs. It is not a benchmark and does not claim task accuracy.
