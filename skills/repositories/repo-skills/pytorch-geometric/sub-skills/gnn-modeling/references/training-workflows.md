# Training Workflows

This reference gives safe, self-contained PyTorch Geometric modeling workflows using public installed APIs. Prefer tiny synthetic fixtures for smoke tests and only scale to real datasets after shapes, losses, and gradients are correct.

## Full-Batch Node Classification

Use this pattern for small homogeneous graphs or deterministic model smoke tests.

```python
import torch
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv

class GCN(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels):
        super().__init__()
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, out_channels)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index).relu()
        x = F.dropout(x, p=0.5, training=self.training)
        return self.conv2(x, edge_index)

model = GCN(data.num_node_features, 16, num_classes)
optimizer = torch.optim.Adam(model.parameters(), lr=0.01, weight_decay=5e-4)

model.train()
optimizer.zero_grad()
out = model(data.x, data.edge_index)
loss = F.cross_entropy(out[data.train_mask], data.y[data.train_mask])
loss.backward()
optimizer.step()
```

Validation checks:

- `out.shape == (data.num_nodes, num_classes)`.
- `loss` is finite before and after `backward()`.
- Train/validation/test masks are boolean tensors with shape `[num_nodes]`.
- `data.edge_index` is on the same device as `data.x` and model parameters.

## Mini-Batch Graph Classification

Use `DataLoader` from `torch_geometric.loader` to batch multiple small graphs. Loader details belong in the loaders sub-skill, but model code should expect a single batched `Data` object with `x`, `edge_index`, `batch`, and `y`.

```python
from torch_geometric.nn import GCNConv, global_mean_pool

class GraphClassifier(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels):
        super().__init__()
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, hidden_channels)
        self.lin = torch.nn.Linear(hidden_channels, out_channels)

    def forward(self, x, edge_index, batch):
        x = self.conv1(x, edge_index).relu()
        x = self.conv2(x, edge_index).relu()
        x = global_mean_pool(x, batch)
        return self.lin(x)
```

Validation checks:

- `batch.shape == [total_nodes]` and uses graph ids from `0` to `num_graphs - 1`.
- Output shape is `[num_graphs, out_channels]`.
- Graph labels `y` align with graph count, not node count.

## Link Prediction Encoder/Decoder

A common link prediction model encodes node embeddings with a GNN and scores edges with dot products or an MLP.

```python
class LinkPredictor(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels):
        super().__init__()
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, hidden_channels)

    def encode(self, x, edge_index):
        z = self.conv1(x, edge_index).relu()
        return self.conv2(z, edge_index)

    def decode(self, z, edge_label_index):
        src, dst = edge_label_index
        return (z[src] * z[dst]).sum(dim=-1)
```

Training notes:

- Keep message-passing `edge_index` separate from supervised `edge_label_index`.
- Do not score against validation/test positive edges during training.
- For binary link prediction, pair logits with labels using `binary_cross_entropy_with_logits`.
- Use metrics from `torch_geometric.metrics` when evaluating ranking quality; verify each metric's expected score and label format.

## Custom MessagePassing Smoke Test

When adding a custom operator, first test it independently from a full model:

```python
layer = MeanNeighborConv(in_channels=3, out_channels=5)
x = torch.randn(4, 3)
edge_index = torch.tensor([[0, 1, 2, 3], [1, 2, 3, 0]], dtype=torch.long)
out = layer(x, edge_index)
assert out.shape == (4, 5)
out.sum().backward()
```

Additional assertions:

- Bad `edge_index` shapes fail early with a clear assertion or `ValueError`.
- Empty-edge graphs are handled deliberately, either supported or rejected with a message.
- Bipartite inputs include explicit source/destination sizes if the graph is not square.

## Torch Compile Awareness

PyG 2.9 targets compatibility with `torch.compile` for GNN layers. Use compile after the eager model is correct:

```python
compiled_model = torch.compile(model, dynamic=True)
out = compiled_model(data.x, data.edge_index)
```

Guidance:

- Use `dynamic=True` for neighbor-sampled or variable-size mini-batches.
- Use `fullgraph=True` only as a diagnostic to force graph breaks to become errors.
- Avoid Python-side data-dependent branching inside `forward` where possible.
- Avoid constructing or mutating graph topology inside `forward` when a transform can precompute it.
- For GCN-style normalization in compiled full-graph mode, prefer preprocessing transforms and instantiate layers with settings such as `add_self_loops=False` or `normalize=False` if normalization was already applied.
- Pooling operations can graph-break if size must be inferred through device synchronization; pass explicit size where the operator supports it.

## TorchScript And JIT Awareness

JIT/TorchScript compatibility is stricter than eager execution. When scripting or tracing PyG models:

- Keep `forward` signatures explicit and type-stable.
- Avoid returning different structures based on flags.
- Prefer public PyG modules and documented model utilities over ad-hoc Python containers.
- Test scripted/traced execution on the same tiny synthetic graph used for eager mode.
- Treat JIT failures as a signal to simplify the model boundary, not to remove shape validation from data preparation.

## Profiling And Runtime Checks

Use profiling after correctness:

- Confirm CPU/GPU device placement before timing.
- Warm up the model before measuring.
- Keep optional extension absence in mind; some sparse or sampling paths may be slower or unavailable without optional PyG packages.
- Profile both forward and backward for training bottlenecks.
- Record batch sizes, node counts, edge counts, hidden channels, and compile settings next to timing results.

## Tiny Smoke Test Policy

Safe smoke tests for generated skills should:

- Use synthetic `Data` objects only.
- Set deterministic seeds.
- Stay on CPU by default.
- Finish in a few seconds.
- Avoid downloads, network calls, credentials, GPUs, and destructive writes.
- Assert tensor shapes, finite loss, and successful parameter updates.

Run the bundled smoke test with:

```bash
python scripts/tiny_gcn_smoke.py --epochs 8
```
