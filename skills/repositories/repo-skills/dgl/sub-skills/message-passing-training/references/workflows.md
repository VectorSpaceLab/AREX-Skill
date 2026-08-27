# DGL Message Passing Training Workflows

These workflows are self-contained templates for PyTorch DGL full-graph training. They assume a graph already has feature, label, and mask fields prepared; route dataset construction and mask preparation to `../datasets-and-io/`.

## Full-Graph Node Classification

Use this workflow for GCN, GraphSAGE, or GAT over all nodes at once.

Checklist:

1. Confirm the graph is on the same device as tensors: `g = g.to(device)` and `features = features.to(device)`.
2. Confirm fields: `g.ndata['feat']`, `g.ndata['label']`, `g.ndata['train_mask']`, and optionally `val_mask`/`test_mask`.
3. For `GraphConv` or `GATConv`, decide how to handle zero in-degree nodes before training.
4. Build a small `torch.nn.Module` with two DGL layers.
5. Compute logits for all nodes and loss on `train_mask` only.
6. Run `zero_grad()`, `loss.backward()`, and `optimizer.step()`.

GraphSAGE template:

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
import dgl.nn.pytorch as dglnn

class SAGE(nn.Module):
    def __init__(self, in_feats, hidden_feats, out_feats):
        super().__init__()
        self.conv1 = dglnn.SAGEConv(in_feats, hidden_feats, "mean")
        self.conv2 = dglnn.SAGEConv(hidden_feats, out_feats, "mean")

    def forward(self, graph, features):
        h = self.conv1(graph, features)
        h = F.relu(h)
        return self.conv2(graph, h)

features = graph.ndata["feat"]
labels = graph.ndata["label"]
train_mask = graph.ndata["train_mask"].bool()
model = SAGE(features.shape[1], 64, int(labels.max().item()) + 1)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-2)

model.train()
logits = model(graph, features)
loss = F.cross_entropy(logits[train_mask], labels[train_mask])
optimizer.zero_grad()
loss.backward()
optimizer.step()
```

GCN variant:

- Use `dglnn.GraphConv(in_feats, hidden_feats, allow_zero_in_degree=True)` only if you intentionally tolerate invalid outputs for zero in-degree nodes.
- Prefer `graph = dgl.add_self_loop(graph)` for homogeneous graphs where self-loops are semantically valid.
- If passing edge weights, normalize them explicitly or use `dglnn.EdgeWeightNorm` with `GraphConv(norm='none')`.

GAT variant:

```python
class GAT(nn.Module):
    def __init__(self, in_feats, hidden_feats, out_feats, heads=2):
        super().__init__()
        self.gat1 = dglnn.GATConv(in_feats, hidden_feats, heads, allow_zero_in_degree=True)
        self.gat2 = dglnn.GATConv(hidden_feats * heads, out_feats, 1, allow_zero_in_degree=True)

    def forward(self, graph, features):
        h = self.gat1(graph, features).flatten(1)
        h = F.elu(h)
        return self.gat2(graph, h).mean(1)
```

Use `flatten(1)` for intermediate multi-head features and `mean(1)` or `squeeze(1)` for final logits depending on the number of output heads.

## Manual Message Passing Layer

Use `update_all` for custom message-passing math that built-in layers do not expose.

```python
import torch.nn as nn
import dgl.function as fn

class WeightedSumLayer(nn.Module):
    def __init__(self, in_feats, out_feats):
        super().__init__()
        self.linear = nn.Linear(in_feats, out_feats)

    def forward(self, graph, features, edge_weight):
        with graph.local_scope():
            graph.ndata["h"] = self.linear(features)
            graph.edata["w"] = edge_weight
            graph.update_all(fn.u_mul_e("h", "w", "m"), fn.sum("m", "h_neigh"))
            return graph.ndata["h_neigh"]
```

Rules:

- Put temporary fields inside `local_scope()`.
- Use built-ins for common tensor algebra.
- Validate `edge_weight.shape[0] == graph.num_edges()` and `edge_weight.device == features.device`.
- Avoid storing the message field after `update_all`; DGL cleans intermediate messages.

## Edge Classification or Regression

Use a node encoder plus `apply_edges` predictor.

```python
import dgl.function as fn

class DotPredictor(nn.Module):
    def forward(self, graph, h):
        with graph.local_scope():
            graph.ndata["h"] = h
            graph.apply_edges(fn.u_dot_v("h", "h", "score"))
            return graph.edata["score"].squeeze(-1)

class EdgeModel(nn.Module):
    def __init__(self, in_feats, hidden_feats):
        super().__init__()
        self.encoder = SAGE(in_feats, hidden_feats, hidden_feats)
        self.predictor = DotPredictor()

    def forward(self, graph, features):
        return self.predictor(graph, self.encoder(graph, features))
```

Training loop:

```python
pred = model(graph, graph.ndata["feat"])
labels = graph.edata["label"].float()
mask = graph.edata["train_mask"].bool()
loss = F.mse_loss(pred[mask], labels[mask])
```

For multi-class edge classification, replace the dot predictor with an MLP UDF that concatenates `edges.src['h']`, `edges.dst['h']`, and optional `edges.data[...]`, returning logits under `score`.

## Full-Graph Link Prediction

Use one graph for positive edges and a synthetic negative graph for sampled non-edges.

```python
def construct_negative_graph(graph, k):
    src, _ = graph.edges()
    neg_src = src.repeat_interleave(k)
    neg_dst = torch.randint(0, graph.num_nodes(), (len(src) * k,), device=src.device)
    return dgl.graph((neg_src, neg_dst), num_nodes=graph.num_nodes(), device=graph.device)

def margin_loss(pos_score, neg_score, k, margin=1.0):
    return (margin - pos_score.view(-1, 1) + neg_score.view(-1, k)).clamp_min(0).mean()

k = 2
neg_graph = construct_negative_graph(graph, k)
h = encoder(graph, graph.ndata["feat"])
pos_score = predictor(graph, h)
neg_score = predictor(neg_graph, h)
loss = margin_loss(pos_score, neg_score, k)
```

Use binary cross entropy instead when scores represent logits for positive/negative labels. For stochastic edge prediction samplers and exclusion of reverse edges, route to `../dataloading-graphbolt/`.

## Graph Classification with Readout

Use `dgl.batch()` plus node readout when each training item is a graph.

```python
class GraphClassifier(nn.Module):
    def __init__(self, in_feats, hidden_feats, num_classes):
        super().__init__()
        self.conv1 = dglnn.GraphConv(in_feats, hidden_feats, allow_zero_in_degree=True)
        self.conv2 = dglnn.GraphConv(hidden_feats, hidden_feats, allow_zero_in_degree=True)
        self.classify = nn.Linear(hidden_feats, num_classes)

    def forward(self, batched_graph, features):
        h = F.relu(self.conv1(batched_graph, features))
        h = F.relu(self.conv2(batched_graph, h))
        with batched_graph.local_scope():
            batched_graph.ndata["h"] = h
            graph_repr = dgl.mean_nodes(batched_graph, "h")
            return self.classify(graph_repr)
```

Collation pattern:

```python
batched_graph = dgl.batch(graph_list)
labels = torch.as_tensor(graph_labels, dtype=torch.long)
logits = model(batched_graph, batched_graph.ndata["feat"])
loss = F.cross_entropy(logits, labels)
```

If preprocessing transforms a batched graph, preserve or restore batch metadata before readout.

## Heterograph `HeteroGraphConv` Node Classification

Use relation modules when features are keyed by node type.

```python
class HeteroSAGE(nn.Module):
    def __init__(self, in_feats, hidden_feats, out_feats, canonical_etypes):
        super().__init__()
        self.conv1 = dglnn.HeteroGraphConv({
            etype: dglnn.SAGEConv((in_feats, in_feats), hidden_feats, "mean")
            for etype in canonical_etypes
        }, aggregate="sum")
        self.conv2 = dglnn.HeteroGraphConv({
            etype: dglnn.SAGEConv((hidden_feats, hidden_feats), out_feats, "mean")
            for etype in canonical_etypes
        }, aggregate="sum")

    def forward(self, graph, x_dict):
        h = self.conv1(graph, x_dict)
        h = {ntype: F.relu(value) for ntype, value in h.items()}
        return self.conv2(graph, h)

features = {ntype: graph.nodes[ntype].data["feat"] for ntype in graph.ntypes}
logits = model(graph, features)["user"]
labels = graph.nodes["user"].data["label"]
mask = graph.nodes["user"].data["train_mask"].bool()
loss = F.cross_entropy(logits[mask], labels[mask])
```

Use canonical edge type keys if relation names are not unique. If only one destination type is supervised, compute the loss only on that destination type's logits and mask.

For heterograph edge or link prediction, compute `h_dict = model(graph, features)`, assign `graph.ndata['h'] = h_dict` inside `local_scope()`, then call `graph.apply_edges(..., etype=target_etype)` and read `graph.edges[target_etype].data['score']`.

## `RelGraphConv` on Relation-ID Graphs

Use `RelGraphConv` when a graph is represented as one homogeneous graph with per-edge relation IDs.

```python
conv = dglnn.RelGraphConv(in_feat, out_feat, num_rels, regularizer="basis", num_bases=4)
etype_ids = graph.edata["etype"].long()
h = conv(graph, features, etype_ids)
```

Validate that `etype_ids.shape[0] == graph.num_edges()`, IDs are in `[0, num_rels)`, and `num_rels` matches the relation vocabulary used to build the graph.

## DGL Sparse Matrix Workflow

Use `dgl.sparse` when the model math is easier as sparse matrix algebra or when implementing sparse attention/sampling primitives.

```python
import dgl.sparse as dglsp

row = torch.tensor([0, 0, 1, 2])
col = torch.tensor([1, 2, 2, 0])
val = torch.ones(row.numel())
A = dglsp.from_coo(row, col, val, shape=(3, 3))
X = torch.randn(3, 4)
Y = A @ X
attention = dglsp.softmax(A, dim=1)
```

Sparse GraphSAGE-style mean aggregation pattern:

```python
A = dglsp.from_coo(dst, src, shape=(num_nodes, num_nodes))
degree = A.sum(1).clamp(min=1).view(-1, 1)
neigh = (A @ features) / degree
out = self.fc_self(features) + self.fc_neigh(neigh)
```

Caveats:

- The row/column orientation is model-defined. Document whether rows are destinations and columns are sources before multiplying.
- Pass `shape` when isolated nodes exist.
- Use `scripts/sparse_api_smoke.py` to detect missing native sparse libraries before relying on sparse ops.
- Route GraphBolt sparse sampling pipelines to `../dataloading-graphbolt/`.

## Validation Steps Before Handoff

For any generated training code:

- Run one CPU optimizer step on a tiny synthetic graph.
- Print or assert the loss is finite.
- Assert output shapes: node logits `(num_nodes, classes)`, edge scores `(num_edges,)` or `(num_edges, classes)`, graph logits `(batch_size, classes)`, heterograph logits keyed by supervised node type.
- Check masks are boolean and non-empty.
- Check all tensors and graph storage are on one device.
- For zero in-degree-sensitive layers, either add self-loops or intentionally set `allow_zero_in_degree=True` with a note about semantics.
