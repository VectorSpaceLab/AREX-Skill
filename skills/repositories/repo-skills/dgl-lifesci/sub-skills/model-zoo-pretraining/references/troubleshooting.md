# Troubleshooting Model Zoo and Pretraining

Use this guide when model construction, pretrained loading, molecule embeddings, or link prediction fails.

## Import and Install Failures

### `ModuleNotFoundError: No module named 'dgllife'`

The active Python environment does not have DGL-LifeSci installed. Ask the user which environment should run the code. Do not hard-code environment paths in reusable scripts or skill content.

### `ModuleNotFoundError: No module named 'dgl'` or DGL backend errors

`dgllife.model` depends on DGL. Check that DGL imports before debugging model code:

```python
import dgl
import torch
import dgllife
print(dgl.__version__, torch.__version__, dgllife.__version__)
```

DGL 1.1.3 with CPU Torch was verified for this skill. If the target uses a different DGL/PyTorch pair, re-run `scripts/inspect_model_constructors.py` and a tiny forward smoke test before assuming API compatibility.

### RDKit or optional generative imports fail

DGMG, JTVAE, molecule construction, and many featurizers need RDKit. The model zoo wraps some generative imports in `try/except ImportError`, so missing optional dependencies can make classes unavailable rather than producing a loud failure at package import time. For property-only GCN/GAT/MPNN model selection, RDKit may only be needed upstream for SMILES-to-graph conversion.

## Missing Constructor or Root Export

### `ImportError: cannot import name 'GATv2Predictor' from 'dgllife.model'`

Source contains `dgllife.model.model_zoo.gatv2_predictor.GATv2Predictor`, but a verified installed `dgllife` 0.3.1 inspection found no root-level `dgllife.model.GATv2Predictor` attribute. Use one of these fallbacks:

```python
from dgllife.model import GATv2
from dgllife.model.readout import WeightedSumAndMax
```

Then add your own readout/head, or inspect whether the narrower submodule exists in the target installation:

```python
from dgllife.model.model_zoo.gatv2_predictor import GATv2Predictor
```

If the submodule import succeeds, still guard user-facing code with a clear version caveat.

### `AttributeError` for a model class that exists in source docs

Docs/source and installed package can differ. Run:

```bash
python scripts/inspect_model_constructors.py --constructors GCN,GAT,GATv2,GATv2Predictor --submodules
```

Then choose an installed class or implement a small custom head around a stable encoder.

## Feature-Dimension Mismatches

### `mat1 and mat2 shapes cannot be multiplied` or linear layer shape errors

The constructor input dimension does not match the tensor passed to `forward()`. Check:

```python
print(g.ndata.keys(), {k: tuple(v.shape) for k, v in g.ndata.items()})
print(g.edata.keys(), {k: tuple(v.shape) for k, v in g.edata.items()})
```

Then adjust:

- `GCNPredictor(in_feats=...)` and `GATPredictor(in_feats=...)` to node feature width.
- `AttentiveFPPredictor(node_feat_size=..., edge_feat_size=...)` to node and edge widths.
- `MPNNPredictor(node_in_feats=..., edge_in_feats=...)` to node and edge widths.
- `WeavePredictor(node_in_feats=..., edge_in_feats=...)` to Weave graph fields.
- `HadamardLinkPredictor(in_feats=...)` to the encoder output width, not the raw node feature width unless there is no encoder.

### Canonical vs AttentiveFP featurizer mismatch

MoleculeNet pretrained naming encodes feature assumptions:

- `*_canonical_*`: commonly 74-dimensional atom features and 13-dimensional bond features when self-loops are included for edge-aware models.
- `*_attentivefp_*`: commonly 39-dimensional atom features and 11-dimensional bond features when self-loops are included for edge-aware models.
- Standalone `GCN_Tox21`/`GAT_Tox21`: canonical atom field `h`, width 74.
- Standalone `Weave_Tox21`: legacy Weave feature widths in source are 27 node and 7 edge.

If the graph fields do not match these widths, route data construction to `molecule-data-prep` and rebuild the graph with the intended featurizer.

### Missing edge features

Edge-aware models (`MPNNPredictor`, `WeavePredictor`, `AttentiveFPPredictor`, `PAGTNPredictor`, WLN models) need edge tensors. If `g.edata` is empty, choose a node-only model (`GCNPredictor`, `GATPredictor`, `NFPredictor`) or construct bond features upstream.

## Zero-In-Degree and Self-Loops

DGL graph convolution and attention layers may raise an error for zero-in-degree nodes, especially with molecular graphs that omit self-loops or graphs with isolated nodes. Fixes:

1. For molecular graphs where self-messages are appropriate, add self-loops during graph construction or with `dgl.add_self_loop(g)`.
2. For constructors that support it, set `allow_zero_in_degree=True` only when the caller understands that isolated-node outputs may be invalid or require downstream masking.
3. For edge-aware pretrained MoleculeNet models, ensure the edge featurizer creates self-loop edge features when self-loops are added.

## Pretrained Download and Checkpoint Failures

### Network unavailable or download blocked

`load_pretrained()` calls DGL's download utility and writes a checkpoint file named like `{model_name}_pre_trained.pth` in the current working directory. If network access is unavailable:

- Instantiate the architecture directly and run without pretrained weights only if the user accepts random initialization.
- Ask for a local checkpoint path and load it with `torch.load(path, map_location='cpu')`.
- If reproducibility matters, stop and report that pretrained weights were not loaded.

### `RuntimeError: Cannot find a pretrained model with name ...`

Check capitalization and naming pattern. Examples are `GCN_Tox21`, `gin_supervised_contextpred`, `GCN_canonical_BACE`, and `wln_center_uspto`. Dataset suffixes are case-sensitive (`FreeSolv`, `ToxCast`, `ClinTox`, `Lipophilicity`).

### Checkpoint state dict mismatch

This usually means the architecture instantiated by the installed package differs from the checkpoint, or the wrong local file was supplied. Confirm `dgllife.__version__`, rebuild the exact model constructor from `load_pretrained()` source patterns, and avoid mixing checkpoints across model families or featurizer variants.

## Molecule Embedding Failures

### Missing `atomic_number`, `chirality_type`, `bond_type`, or `bond_direction_type`

Standalone pretrained GIN encoders expect categorical fields from `PretrainAtomFeaturizer` and `PretrainBondFeaturizer`. Rebuild graphs with those featurizers and `add_self_loop=True`; do not pass canonical float `h`/`e` tensors to pretrained GIN.

### Invalid SMILES or empty graph list

The embedding example records parse success and skips invalid SMILES. In production, preserve an output mask or index map so embeddings can be aligned back to input rows. Route robust SMILES validation and CSV/text loading to `molecule-data-prep`.

### Unexpected graph-level output from `gin_supervised_*`

Standalone `gin_supervised_*` models return node embeddings. Add a DGL readout such as `AvgPooling`, `SumPooling`, or `WeightedSumAndMax` for molecule-level embeddings.

## Link Prediction Failures

### Pair logits shape is wrong

`HadamardLinkPredictor` expects left and right tensors shaped `(P, D)` and returns `(P, n_tasks)`. Make sure `D` equals `in_feats` and both sides are indexed from the same encoder output tensor.

### Negative sampling or OGB evaluator errors

`HadamardLinkPredictor` is only a scoring head. Dataset splits, negative sampling, OGB evaluators, and hit-rate metrics belong to the training workflow and may require `ogb` plus downloaded datasets. Keep large OGB full-graph examples reference-only unless the user has explicitly prepared those dependencies and data.

## API Misuse and Configuration Issues

### Per-layer list length assertion

GNN constructors such as `GCN`, `GAT`, and `GATv2` require all per-layer lists to have the same length as `hidden_feats`. If you set `hidden_feats=[64, 64, 64]`, also provide three entries for `activation`, `dropout`, `residual`, heads, and aggregation lists when overriding defaults.

### Activation names in reusable snippets

Constructors expect callables, not strings. Use `torch.nn.functional.relu`, `torch.nn.functional.elu`, `None`, or module instances where the constructor expects them.

### Classification probabilities vs logits

Predictors return logits for classification tasks. Apply `torch.sigmoid` for independent binary/multitask labels or `torch.softmax` for mutually exclusive multiclass labels as appropriate. Do not apply sigmoid before `BCEWithLogitsLoss`.

### Popping graph features mutates graphs

Examples often use `g.ndata.pop('h')` or `bg.edata.pop('he')`. This removes fields. If the same graph is reused, use `g.ndata['h']` or clone/cache the tensor instead.

## Quick Diagnostic Sequence

1. Import and version check: `import dgl, torch, dgllife`.
2. Constructor check: `python scripts/inspect_model_constructors.py --constructors GCNPredictor,GATPredictor,MPNNPredictor --submodules`.
3. Feature check: print `g.ndata` and `g.edata` shapes.
4. Match constructor dimensions to features, not dataset names.
5. Add self-loops or set `allow_zero_in_degree=True` with caveats.
6. For pretrained models, confirm exact name and network/checkpoint availability.
