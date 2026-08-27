# Model Catalog

This reference distills the DGL-LifeSci model, readout, pretrained, molecule-embedding, and link-prediction surfaces that are useful when selecting or instantiating `dgllife.model` APIs.

## Import Surfaces

Prefer importing stable public objects from `dgllife.model` when they exist:

```python
from dgllife.model import GCNPredictor, GATPredictor, MPNNPredictor, load_pretrained
```

For lower-level encoders, readouts, or version-sensitive classes, import the narrower module and verify on the target installation:

```python
from dgllife.model.gnn import GCN, GAT, GATv2, GraphSAGE, GIN
from dgllife.model.readout import WeightedSumAndMax, AttentiveFPReadout, SumAndMax
from dgllife.model.model_zoo.hadamard_link_predictor import HadamardLinkPredictor
```

Version caveat: source code includes `dgllife.model.model_zoo.gatv2_predictor.GATv2Predictor`, but an installed `dgllife` 0.3.1 inspection found no `GATv2Predictor` attribute on `dgllife.model`. Before using it, run `scripts/inspect_model_constructors.py --constructors GATv2Predictor --submodules` and prefer `GATv2` plus a readout/MLP fallback if root export is missing.

## Feature Contracts

Common feature dimensions from DGL-LifeSci examples and pretrained constructors:

| Graph/featurizer pattern | Node field | Node width/type | Edge field | Edge width/type | Typical models |
| --- | --- | ---: | --- | ---: | --- |
| `CanonicalAtomFeaturizer()` and `CanonicalBondFeaturizer()` | `h` or custom `hv` | 74 float | `e` or custom `he` | 12 or 13 float when self-loop is included | `GCNPredictor`, `GATPredictor`, `WeavePredictor`, `MPNNPredictor`, `AttentiveFPPredictor`, `NFPredictor` |
| `AttentiveFPAtomFeaturizer()` and `AttentiveFPBondFeaturizer()` | `hv` | 39 float | `he` | 10 or 11 float when self-loop is included | pretrained MoleculeNet `*_attentivefp_*`, `AttentiveFPPredictor`, `MPNNPredictor`, `WeavePredictor` |
| `PretrainAtomFeaturizer()` and `PretrainBondFeaturizer()` | `atomic_number`, `chirality_type` | two categorical tensors | `bond_type`, `bond_direction_type` | two categorical tensors | `GIN`, `gin_supervised_*` pretrained encoders and molecule embeddings |
| Weave Tox21 legacy example | `h` | 27 float | `e` | 7 float | `load_pretrained('Weave_Tox21')` only |
| WLN reaction models | reaction-specific fields | 82/89 node inputs | reaction-specific fields | 5/6 edge inputs plus pair features | route workflow details to `reaction-prediction` |
| OGB link prediction | graph node features | `x.size(-1)` float | optional | dataset-specific | `GCN`/`GraphSAGE` encoder plus `HadamardLinkPredictor` |

If a constructor parameter says `in_feats`, `node_feat_size`, or `node_in_feats`, it must match the last dimension of the node feature tensor passed to `forward()`. If it says `edge_feat_size`, `edge_in_feats`, or `edge_feats`, it must match the edge feature tensor. Do not guess these from dataset names; inspect `g.ndata` and `g.edata` or route graph construction to `molecule-data-prep`.

## GNN Encoders

These classes update node representations and are useful when the caller supplies a separate readout or head.

| Class | Signature highlights | Forward inputs | Output expectation | Notes |
| --- | --- | --- | --- | --- |
| `GCN` | `in_feats`, list-valued `hidden_feats`, `gnn_norm`, `activation`, `residual`, `batchnorm`, `dropout`, `allow_zero_in_degree` | `(g, feats)` | node tensor `(N, hidden_feats[-1])` | Defaults to two 64-dim layers; all per-layer lists must have equal length. |
| `GAT` | `in_feats`, `hidden_feats`, `num_heads`, `agg_modes`, `allow_zero_in_degree` | `(g, feats)` | node tensor with last layer width `hidden_feats[-1]` if `agg_modes[-1]='mean'`, else `hidden_feats[-1] * num_heads[-1]` | Defaults to two layers, 4 heads, final mean aggregation. |
| `GATv2` | like `GAT`, plus `share_weights`; supports `get_attention=True` | `(g, feats, get_attention=False)` | node tensor or `(node_tensor, attentions)` | Prefer this stable encoder when `GATv2Predictor` root export is absent. |
| `GraphSAGE` | `in_feats`, `hidden_feats`, `activation`, `dropout`, `aggregator_type` | `(g, feats)` | node tensor `(N, hidden_feats[-1])` | Used in OGB link-prediction examples as a full-graph encoder. |
| `AttentiveFPGNN` | `node_feat_size`, `edge_feat_size`, `num_layers`, `graph_feat_size`, `dropout` | `(g, node_feats, edge_feats)` | node tensor `(N, graph_feat_size)` | Use with `AttentiveFPReadout` or `AttentiveFPPredictor`. |
| `MPNNGNN` | `node_in_feats`, `edge_in_feats`, `node_out_feats`, `edge_hidden_feats`, message-passing steps | `(g, node_feats, edge_feats)` | node tensor `(N, node_out_feats)` | Property predictor adds Set2Set readout and task head. |
| `WeaveGNN` | `node_in_feats`, `edge_in_feats`, layer counts and hidden dims | `(g, node_feats, edge_feats, node_only=True)` | node tensor, or node and edge tensors when `node_only=False` | Complete-graph/self-loop details usually matter. |
| `GIN` | `num_node_emb_list`, `num_edge_emb_list`, `num_layers`, `emb_dim`, `JK`, `dropout` | `(g, categorical_node_feats, categorical_edge_feats)` | node tensor `(N, emb_dim)` or concatenated JK width | Pretrained GIN expects categorical feature lists from `PretrainAtomFeaturizer`/`PretrainBondFeaturizer`. |
| `GNNOGB` | categorical node types and edge features; `gnn_type='gcn'|'gin'` | `(g, node_feats, edge_feats)` | node tensor `(N, hidden_feats)` | Specialized for OGB graph property examples, not MoleculeNet defaults. |
| `MGCNGNN` / `SchNetGNN` | atomic types and distance-like edge features | model-specific | node tensor | More common in geometry or binding-affinity workflows; validate fields carefully. |
| `WLN` | reaction atom/bond dimensions | reaction-specific | reaction node features | Shared constructor exists here, but route reaction pipelines to `reaction-prediction`. |
| `PAGTNGNN` | path-augmented atom and edge dimensions | `(g, node_feats, edge_feats)` | node tensor | Requires path/edge features chosen upstream. |

## Graph-Level Predictors

These wrap a GNN/readout/head and return graph-level logits or regression values. Classification outputs are logits before sigmoid/softmax.

| Class | Signature highlights | Forward inputs | Output |
| --- | --- | --- | --- |
| `GCNPredictor` | `in_feats`, per-layer GCN options, `predictor_hidden_feats`, `n_tasks` | `(bg, feats)` | `(B, n_tasks)` |
| `GATPredictor` | `in_feats`, attention lists, `agg_modes`, `predictor_hidden_feats`, `n_tasks` | `(bg, feats)` | `(B, n_tasks)` |
| `GATv2Predictor` | source has `in_feats`, GATv2 options, `n_tasks`, `predictor_out_feats`; root export may be absent | `(bg, feats, get_attention=False)` | `(B, n_tasks)` or with attention |
| `AttentiveFPPredictor` | `node_feat_size`, `edge_feat_size`, `graph_feat_size`, `num_timesteps`, `n_tasks` | `(g, node_feats, edge_feats, get_node_weight=False)` | `(B, n_tasks)` or `(preds, node_weights)` |
| `MPNNPredictor` | `node_in_feats`, `edge_in_feats`, `node_out_feats`, Set2Set steps/layers, `n_tasks` | `(g, node_feats, edge_feats)` | `(B, n_tasks)` |
| `WeavePredictor` | `node_in_feats`, `edge_in_feats`, `graph_feats`, `gaussian_expand`, `n_tasks` | `(g, node_feats, edge_feats)` | `(B, n_tasks)` |
| `GINPredictor` | categorical embedding cardinalities, `emb_dim`, `readout`, `n_tasks` | `(g, categorical_node_feats, categorical_edge_feats)` | `(B, n_tasks)` |
| `NFPredictor` | `in_feats`, degree-aware hidden layers, `n_tasks` | `(g, feats)` | `(B, n_tasks)` |
| `GNNOGBPredictor` | `in_edge_feats`, categorical node types, `gnn_type`, readout | `(g, node_feats, edge_feats)` | `(B, n_tasks)` |
| `MGCNPredictor` / `SchNetPredictor` | atomic type and distance parameters | model-specific graph fields | `(B, n_tasks)` |
| `PAGTNPredictor` | `node_in_feats`, `node_out_feats`, `node_hid_feats`, `edge_feats`, `mode` | `(g, node_feats, edge_feats)` | `(B, n_tasks)` |
| `ACNN` / `PotentialNet` | protein-ligand binding-specific geometric features | binding-specific | binding outputs; route workflow details to binding-affinity skill if present |
| `WLNReactionCenter` / `WLNReactionRanking` | reaction node/edge/pair dimensions | reaction-specific | reaction scores; route workflow details to `reaction-prediction` |

## Readouts

Use readouts when building a custom graph-level head around an encoder.

| Readout | Constructor | Forward expectation | Output |
| --- | --- | --- | --- |
| `WeightedSumAndMax` | `in_feats` | `(g, node_feats)` | `(B, 2 * in_feats)` |
| `SumAndMax` | no args | `(g, node_feats)` | `(B, 2 * node_feat_width)` |
| `AttentiveFPReadout` | `feat_size`, `num_timesteps`, `dropout` | `(g, node_feats, get_node_weight=False)` | `(B, feat_size)` or weights |
| `MLPNodeReadout` | `node_feats`, `hidden_feats`, `graph_feats`, `activation`, `mode='sum'|'max'|'mean'` | `(g, node_feats)` | `(B, graph_feats)` |
| `WeaveGather` | `node_in_feats`, `gaussian_expand`, `gaussian_memberships`, `activation` | `(g, node_feats)` | `(B, node_in_feats)` or expanded graph features depending options |

## Pretrained Names and Contracts

`load_pretrained(model_name, log=True)` constructs a model, downloads a checkpoint on first use, loads it on CPU, and returns the model. Unsupported names raise `RuntimeError`. Use `model.eval()` for inference.

Primary standalone names:

- Property/toxicity: `GCN_Tox21`, `GAT_Tox21`, `Weave_Tox21`, `AttentiveFP_Aromaticity`.
- Molecule embeddings: `gin_supervised_contextpred`, `gin_supervised_infomax`, `gin_supervised_edgepred`, `gin_supervised_masking`.
- Generative models: `DGMG_ChEMBL_canonical`, `DGMG_ChEMBL_random`, `DGMG_ZINC_canonical`, `DGMG_ZINC_random`, `JTVAE_ZINC_no_kl`.
- Reaction models: `wln_center_uspto`, `wln_rank_uspto`; route workflow usage to `reaction-prediction`.

MoleculeNet fine-tuned naming pattern:

- Datasets: `BACE`, `BBBP`, `ClinTox`, `ESOL`, `FreeSolv`, `HIV`, `Lipophilicity`, `MUV`, `PCBA`, `SIDER`, `Tox21`, `ToxCast`.
- Model/featurizer pattern: `{GCN|GAT|Weave|MPNN|AttentiveFP}_{canonical|attentivefp}_{Dataset}`.
- GIN pattern: `{gin_supervised_contextpred|gin_supervised_infomax|gin_supervised_edgepred|gin_supervised_masking}_{Dataset}`, except some datasets omit GIN variants in source.
- NF pattern: `NF_canonical_{Dataset}` exists for only some datasets, including BACE, BBBP, HIV, SIDER, Tox21, and ToxCast in source.

Feature implications:

- `*_canonical_*` property models commonly expect 74-dimensional atom features and 13-dimensional bond features when self-loops are included for edge-aware models.
- `*_attentivefp_*` property models commonly expect 39-dimensional atom features and 11-dimensional bond features when self-loops are included for edge-aware models.
- `GCN_Tox21` and `GAT_Tox21` use `CanonicalAtomFeaturizer()` and `g.ndata['h']` with width 74.
- `Weave_Tox21` is a legacy special case using Weave featurizers and the model constructor in source expects `node_in_feats=27`, `edge_in_feats=7`.
- `AttentiveFP_Aromaticity` source constructs `AttentiveFPPredictor(node_feat_size=39, edge_feat_size=10, n_tasks=1)` and tests use custom fields `hv`/`he`.
- Standalone `gin_supervised_*` models return node representations, not graph-level task logits; pool them with DGL readouts such as `AvgPooling` for molecule embeddings.

## Molecule Embedding Pattern

For pretrained GIN molecule embeddings:

1. Construct each molecule graph with `mol_to_bigraph(..., add_self_loop=True, node_featurizer=PretrainAtomFeaturizer(), edge_featurizer=PretrainBondFeaturizer(), canonical_atom_order=False)`.
2. Batch graphs with `dgl.batch`.
3. Load one of the standalone `gin_supervised_*` models.
4. Pass categorical feature lists: `[bg.ndata.pop('atomic_number'), bg.ndata.pop('chirality_type')]` and `[bg.edata.pop('bond_type'), bg.edata.pop('bond_direction_type')]`.
5. Pool node representations with `dgl.nn.pytorch.glob.AvgPooling()` or another readout.

The repo's full embedding example reads input files and writes NumPy arrays, and pretrained loading may download checkpoints. For runtime skill use, keep this as a reference pattern rather than a bundled data-processing script unless the caller explicitly asks to build a local embedding CLI.

## Link Prediction Pattern

`HadamardLinkPredictor(in_feats, hidden_feats=256, num_layers=3, n_tasks=1, dropout=0.0)` predicts from pairs of node embeddings by multiplying the left and right vectors elementwise and passing the product through an MLP. It is symmetric: swapping left and right inputs gives the same pair features.

Typical workflow:

```python
encoder = GCN(in_feats=x.size(-1), hidden_feats=[hidden_dim] * num_layers)
predictor = HadamardLinkPredictor(in_feats=hidden_dim, hidden_feats=hidden_dim, num_layers=num_layers)
h = encoder(g, x)
logits = predictor(h[src_nodes], h[dst_nodes])
```

The OGB example also demonstrates a `GraphSAGE` alternative. That script downloads/uses OGB data and performs full training, so treat it as reference-only unless the caller has already prepared the dataset and environment.
