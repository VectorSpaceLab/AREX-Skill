# Custom GNN Recipe

## Purpose

Read this when a user wants to implement a small CogDL model from scratch or
adapt a paper idea onto the package's `Graph` and layer APIs.

## Minimum recipe

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
from cogdl.data import Graph
from cogdl.layers import GCNLayer
from cogdl.models import BaseModel

class TinyGCN(BaseModel):
    def __init__(self, in_feats, hidden_size, out_feats, dropout=0.5):
        super().__init__()
        self.conv1 = GCNLayer(in_feats, hidden_size)
        self.conv2 = GCNLayer(hidden_size, out_feats)
        self.dropout = nn.Dropout(dropout)

    def forward(self, graph):
        graph.sym_norm()
        x = self.dropout(graph.x)
        x = F.relu(self.conv1(graph, x))
        x = self.dropout(x)
        x = self.conv2(graph, x)
        return x
```

## Practical pattern

1. Build or load a `Graph` with tensor `x`, a valid `edge_index`, and the
   task labels/masks required by the data sub-skill.
2. Normalize the graph inside the model if the architecture expects it. For
   GCN-like models, `graph.sym_norm()` is the common first step.
3. Keep the forward signature `forward(self, graph)` or `forward(self, graph,
   x)` consistent with the layer wrappers you use.
4. Keep the model small enough that the bundled smoke script can exercise it
   on a toy graph before you move to a real dataset.
5. Hand the model to the training-wrapper or experiment sub-skill when you are
   ready to choose wrappers, checkpoints, or CLI flags.

## Common custom-model decisions

- For graph classification, read the graph-data sub-skill first so you know
  whether node features exist or whether degree features need to be enabled in
  the training wrapper.
- For attention models, make sure `nhead`, `alpha`, and dropout values are
  compatible with the target `GATLayer` signature.
- For residual or normalization-heavy models, keep the options explicit in the
  constructor so the model can be reproduced from a config.

## Example usage pattern

```python
from cogdl import experiment
from cogdl.datasets import build_dataset_from_name

dataset = build_dataset_from_name("cora")
model = TinyGCN(dataset.num_features, 32, dataset.num_classes, dropout=0.5)
experiment(dataset=dataset, model=model, mw="node_classification_mw", dw="node_classification_dw")
```

This pattern is a convenience sketch, not a recommendation to run Cora
without first considering cache/network availability.
