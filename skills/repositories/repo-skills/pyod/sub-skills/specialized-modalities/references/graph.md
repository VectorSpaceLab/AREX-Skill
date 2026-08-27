# PyOD graph anomaly detection

## Backend and data contract

Install graph support with:

```bash
pip install 'pyod[graph]'
```

The `graph` extra installs PyTorch and PyTorch Geometric. Pick a PyTorch CPU/CUDA/ROCm wheel appropriate for the target runtime before installing the extra when a specific accelerator build is required.

PyOD graph detectors accept either:

1. A PyTorch Geometric `Data` object.
2. A NumPy feature matrix plus a separate COO `edge_index`.

Primary `Data` contract:

```python
import torch
from torch_geometric.data import Data

data = Data(
    x=torch.as_tensor(X, dtype=torch.float32),             # (n_nodes, n_features)
    edge_index=torch.as_tensor(edge_index, dtype=torch.long)  # (2, n_edges)
)
```

For structure-only graphs without `x`, set `num_nodes` explicitly:

```python
data = Data(edge_index=edge_index_tensor, num_nodes=n_nodes)
```

Use zero-based node ids. For undirected graphs, include both directions in `edge_index` unless the source graph is intentionally directed.

## Graph detectors

All graph detectors in this PyOD version are transductive: fit them on the graph to be scored and read `decision_scores_` and `labels_`. Do not expect out-of-sample `decision_function()` or `predict(X_new)`.

| Detector | Import | Requires node features? | Main idea | Common parameters |
|---|---|---:|---|---|
| `DOMINANT` | `pyod.models.pyg_dominant.DOMINANT` | Yes | GCN autoencoder reconstructing structure and attributes | `hidden_dim`, `num_layers`, `dropout`, `alpha`, `epochs`, `lr` |
| `CoLA` | `pyod.models.pyg_cola.CoLA` | Yes | Contrastive local neighbor context scoring | `hidden_dim`, `num_layers`, `epochs`, `lr` |
| `CONAD` | `pyod.models.pyg_conad.CONAD` | Yes | Contrastive + reconstruction with anomalous-view injection | `hidden_dim`, `num_layers`, `aug_ratio`, `alpha`, `dropout`, `epochs`, `lr` |
| `AnomalyDAE` | `pyod.models.pyg_anomalydae.AnomalyDAE` | Yes | Dual autoencoder with GAT structure encoder and attribute decoder | `embed_dim`, `num_heads`, `alpha`, `dropout`, `epochs`, `lr` |
| `GUIDE` | `pyod.models.pyg_guide.GUIDE` | Yes | Motif/higher-order structure plus GCN autoencoders | `hidden_dim`, `num_layers`, `alpha`, `dropout`, `epochs`, `lr` |
| `Radar` | `pyod.models.pyg_radar.Radar` | Yes | Residual analysis with graph Laplacian smoothing | `alpha`, `gamma`, `max_iter` |
| `ANOMALOUS` | `pyod.models.pyg_anomalous.ANOMALOUS` | Yes | CUR-style decomposition plus residual row norms | `alpha`, `gamma`, `lambda_r`, `max_iter` |
| `SCAN` | `pyod.models.pyg_scan.SCAN` | **No** | Structure-only SCAN clustering, hubs, and outliers | `epsilon`, `mu` |

## Minimal examples

### Attributed graph with DOMINANT

```python
import torch
from torch_geometric.data import Data
from pyod.models.pyg_dominant import DOMINANT
from pyod.utils.data import generate_graph_data

X, edge_index, y = generate_graph_data(
    n_nodes=200, n_features=16, contamination=0.1, random_state=42)
data = Data(x=torch.FloatTensor(X), edge_index=torch.LongTensor(edge_index))

clf = DOMINANT(hidden_dim=32, num_layers=2, epochs=5,
               contamination=0.1)
clf.fit(data)
node_scores = clf.decision_scores_
node_labels = clf.labels_
```

### Structure-only graph with SCAN

```python
import torch
from torch_geometric.data import Data
from pyod.models.pyg_scan import SCAN

edge_index = torch.LongTensor([[0, 1, 1, 2, 3, 4],
                               [1, 0, 2, 1, 4, 3]])
data = Data(edge_index=edge_index, num_nodes=5)

clf = SCAN(epsilon=0.5, mu=2, contamination=0.2)
clf.fit(data)
scores = clf.decision_scores_
```

## Choosing a graph path

- Use `SCAN` when only structure is available. It ignores features and can fit `Data(edge_index=..., num_nodes=...)`.
- Use `DOMINANT` or `CoLA` for a first attributed-graph baseline.
- Use `GUIDE` only when the graph has triangle motifs; it raises a clear error when no triangles exist.
- Use `Radar`/`ANOMALOUS` when a non-neural matrix-factorization style baseline is preferred, but PyG is still required for input conversion.
- Keep epochs small for smoke tests and increase only after shapes, dtypes, and optional packages are verified.

## Validation checklist

- `edge_index.shape == (2, n_edges)` and dtype is integer/long.
- `data.x.shape[0] == data.num_nodes` when node features exist.
- `data.x` is present for every detector except `SCAN`.
- `decision_scores_.shape == (num_nodes,)` after `fit()`.
- All graph detectors are treated as transductive; downstream workflows should score the full graph of interest at fit time.
