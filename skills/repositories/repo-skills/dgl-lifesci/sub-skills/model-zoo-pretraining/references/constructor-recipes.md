# Constructor Recipes

These snippets are CPU-safe patterns for choosing constructor parameters and reasoning about output shapes. They do not download datasets or checkpoints unless explicitly noted.

## Validate Feature Dimensions First

Before choosing a model, inspect the graph fields produced by data preparation:

```python
print(g.ndata.keys(), {k: tuple(v.shape) for k, v in g.ndata.items()})
print(g.edata.keys(), {k: tuple(v.shape) for k, v in g.edata.items()})
```

Then map tensor widths into constructor names:

- `feats.shape[-1]` -> `in_feats` for `GCN`, `GAT`, `GATv2`, `GraphSAGE`, `GCNPredictor`, `GATPredictor`, `GATv2Predictor`.
- `node_feats.shape[-1]` -> `node_feat_size`, `node_in_feats`, or `node_in_feats` for `AttentiveFPPredictor`, `MPNNPredictor`, `WeavePredictor`, `PAGTNPredictor`.
- `edge_feats.shape[-1]` -> `edge_feat_size`, `edge_in_feats`, or `edge_feats` for edge-aware models.
- list-valued categorical features -> `GIN`/`GINPredictor` `num_node_emb_list` and `num_edge_emb_list`; each list entry is the number of categories, not a tensor width.

## Tiny Graph Setup

Use this tiny graph for constructor smoke tests:

```python
import dgl
import torch

g = dgl.graph(([0, 1, 2], [1, 2, 0]))
g = dgl.add_self_loop(g)
node_feats = torch.randn(g.num_nodes(), 74)
edge_feats = torch.randn(g.num_edges(), 13)
```

Self-loops help avoid zero-in-degree failures for GCN/GAT-style layers. If a production graph intentionally has isolated nodes, set `allow_zero_in_degree=True` only after documenting that those outputs need special handling.

## GCN Predictor for Canonical Atom Features

```python
import torch.nn.functional as F
from dgllife.model import GCNPredictor

model = GCNPredictor(
    in_feats=74,
    hidden_feats=[64, 64],
    activation=[F.relu, F.relu],
    residual=[False, False],
    batchnorm=[True, True],
    dropout=[0.0, 0.0],
    predictor_hidden_feats=128,
    n_tasks=1,
)
out = model(g, node_feats)
assert out.shape == (1, 1)
```

Shape reasoning: `hidden_feats[-1]` is the graph encoder width before `WeightedSumAndMax`; the predictor returns one row per graph and one column per task.

## GAT/GATv2 Head Width

For attention encoders, the final node width depends on final aggregation:

```python
from dgllife.model import GAT

encoder = GAT(
    in_feats=74,
    hidden_feats=[32, 16],
    num_heads=[4, 2],
    agg_modes=['flatten', 'mean'],
    allow_zero_in_degree=False,
)
h = encoder(g, node_feats)
assert h.shape[-1] == 16
```

If the final `agg_modes[-1]` is `'flatten'`, final width is `hidden_feats[-1] * num_heads[-1]`. If it is `'mean'`, final width is `hidden_feats[-1]`. This matters when attaching `WeightedSumAndMax`, `MLPPredictor`, or `HadamardLinkPredictor`.

Use the same reasoning for `GATv2`. Because root-level `GATv2Predictor` availability is version-sensitive, a robust fallback is `GATv2` + `WeightedSumAndMax` + `MLPPredictor`.

## Edge-Aware Property Predictor

```python
from dgllife.model import MPNNPredictor

model = MPNNPredictor(
    node_in_feats=74,
    edge_in_feats=13,
    node_out_feats=64,
    edge_hidden_feats=128,
    n_tasks=2,
)
out = model(g, node_feats, edge_feats)
assert out.shape == (1, 2)
```

Use this family when the graph has meaningful bond features. If edge features are absent, choose `GCNPredictor`, `GATPredictor`, `GATv2` with a custom head, `NFPredictor`, or add a data-prep step that builds bond features.

## AttentiveFP Predictor with Node Weights

```python
from dgllife.model import AttentiveFPPredictor

model = AttentiveFPPredictor(
    node_feat_size=74,
    edge_feat_size=13,
    num_layers=2,
    num_timesteps=2,
    graph_feat_size=128,
    n_tasks=1,
    dropout=0.0,
)
preds, node_weights = model(g, node_feats, edge_feats, get_node_weight=True)
assert preds.shape == (1, 1)
```

`get_node_weight=True` is useful for explaining atom-level attention. Keep graph construction and atom/bond featurizer choices with `molecule-data-prep`.

## GIN Pretrained Encoder for Embeddings

Standalone `gin_supervised_*` pretrained models are encoders. They expect categorical node and edge feature lists.

```python
import dgl
import torch
from dgl.nn.pytorch.glob import AvgPooling
from dgllife.model import GIN

encoder = GIN(
    num_node_emb_list=[120, 3],
    num_edge_emb_list=[6, 3],
    num_layers=5,
    emb_dim=300,
    JK='last',
    dropout=0.5,
)
node_categories = [torch.zeros(g.num_nodes(), dtype=torch.long), torch.zeros(g.num_nodes(), dtype=torch.long)]
edge_categories = [torch.zeros(g.num_edges(), dtype=torch.long), torch.zeros(g.num_edges(), dtype=torch.long)]
node_repr = encoder(g, node_categories, edge_categories)
mol_repr = AvgPooling()(g, node_repr)
assert mol_repr.shape == (1, 300)
```

When using `load_pretrained('gin_supervised_contextpred')`, replace the synthetic categorical tensors with graph fields from `PretrainAtomFeaturizer` and `PretrainBondFeaturizer`: `atomic_number`, `chirality_type`, `bond_type`, and `bond_direction_type`.

## Readout-Only Custom Head

```python
import torch.nn as nn
from dgllife.model.readout import WeightedSumAndMax

readout = WeightedSumAndMax(in_feats=64)
head = nn.Linear(128, 3)
graph_feats = readout(g, torch.randn(g.num_nodes(), 64))
logits = head(graph_feats)
assert logits.shape == (1, 3)
```

`WeightedSumAndMax` doubles the node feature width. `SumAndMax` also doubles the input width but has no learned weighting. `MLPNodeReadout` lets you choose `mode='sum'`, `'max'`, or `'mean'` and an explicit graph feature width.

## Link Prediction Head

```python
from dgllife.model import GraphSAGE, HadamardLinkPredictor

encoder = GraphSAGE(in_feats=74, hidden_feats=[64, 64])
predictor = HadamardLinkPredictor(in_feats=64, hidden_feats=64, num_layers=3, n_tasks=1)
h = encoder(g, node_feats)
edge_pairs = torch.tensor([[0, 1], [1, 2]])
logits = predictor(h[edge_pairs[:, 0]], h[edge_pairs[:, 1]])
assert logits.shape == (2, 1)
```

`HadamardLinkPredictor` multiplies pair features elementwise and is symmetric. It only scores pairs; negative sampling, split handling, and ranking metrics belong to the training workflow.

## Pretrained Property Inference

This recipe downloads a checkpoint if it is not already cached in the current working directory:

```python
from dgllife.model import load_pretrained

model = load_pretrained('GCN_Tox21', log=True)
model.eval()
# Pass graphs featurized with CanonicalAtomFeaturizer and use g.ndata['h'].
```

Fallback when network is unavailable:

1. Instantiate the matching architecture directly from `references/model-catalog.md` or `scripts/inspect_model_constructors.py`.
2. Load a caller-provided local checkpoint with `torch.load(..., map_location='cpu')` if available.
3. Otherwise proceed with random initialization and clearly state that pretrained weights were not used.

## Constructor Inspection Helper

Run the bundled helper from this sub-skill directory:

```bash
python scripts/inspect_model_constructors.py --constructors GCNPredictor,GATPredictor,MPNNPredictor --instantiate --node-feats 74 --edge-feats 13 --tasks 2
```

The helper prints installed signatures and attempts tiny CPU-safe constructor instantiation for supported classes. It does not run forward passes or download pretrained checkpoints.
