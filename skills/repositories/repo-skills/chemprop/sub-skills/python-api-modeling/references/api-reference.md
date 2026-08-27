# Chemprop Python API Reference

This reference summarizes public Chemprop v2 APIs that are useful when building models directly in Python.

## Imports

```python
from lightning import pytorch as pl
from chemprop import data, models, nn
from chemprop.models import MPNN, MulticomponentMPNN, MolAtomBondMPNN, save_model, load_model
from chemprop.models.utils import load_output_columns
```

Chemprop 2.2.3 supports Python `>=3.11,<3.15`. The installed console command is `chemprop`, but this sub-skill focuses on Python code rather than CLI invocations.

## Data Objects

### Molecule datapoints

```python
dp = data.MoleculeDatapoint.from_smi("CCO", y=np.array([1.2]))
dset = data.MoleculeDataset([dp])
loader = data.build_dataloader(dset, batch_size=32, shuffle=True)
```

`MoleculeDatapoint` fields used by model batches:

- `y`: target array; missing targets are represented with `np.nan`.
- `weight`: per-datapoint loss weight.
- `gt_mask` / `lt_mask`: inequality masks for bounded regression losses.
- `x_d`: molecule-level descriptors concatenated after aggregation.
- `V_f` / `E_f`: extra atom/bond features added before message passing through the molgraph featurizer.
- `V_d`: atom-level descriptors concatenated after message passing before readout.
- `name`: identifier, defaulting to the SMILES string when using `from_smi`.

`MoleculeDataset` exposes:

- `Y`: scaled/current targets; `_Y`: raw targets.
- `X_d`, `V_fs`, `E_fs`, `V_ds`: current descriptor/feature arrays.
- `d_xd`, `d_vf`, `d_ef`, `d_vd`: inferred descriptor dimensions.
- `normalize_targets(scaler=None)`: fits or applies a `sklearn.preprocessing.StandardScaler` for regression targets.
- `normalize_inputs(key="X_d", scaler=None)`: supports `X_d`, `V_f`, `E_f`, and `V_d`.
- `reset()`: restores raw targets and descriptors/features.

### Dataloaders and batch signatures

`data.build_dataloader(dataset, batch_size=64, num_workers=0, class_balance=False, seed=None, shuffle=True, drop_last=None, **kwargs)` chooses the correct collate function for the dataset type.

Plain molecule/reaction batches unpack as:

```python
bmg, V_d, X_d, targets, weights, lt_mask, gt_mask = batch
```

Shape expectations:

- `bmg`: `BatchMolGraph`; contains `V`, `E`, `edge_index`, `rev_edge_index`, and `batch` tensors.
- `V_d`: concatenated atom descriptors with shape `(total_atoms, d_vd)`, or `None`.
- `X_d`: molecule descriptors with shape `(batch_size, d_xd)`, or `None`.
- `targets`: target matrix with shape `(batch_size, n_tasks)`, or `None` for prediction-only data.
- `weights`: shape `(batch_size, 1)`.
- masks: shape compatible with targets, or `None`.

`build_dataloader` defaults to `shuffle=True`; set `shuffle=False` for validation, test, and prediction loaders. If `drop_last=None`, Chemprop drops a final batch of size 1 when needed to avoid batch-normalization issues.

### Multicomponent batches

For multicomponent data, batches unpack as:

```python
bmgs, V_ds, X_d, targets, weights, lt_mask, gt_mask = batch
```

`bmgs` is a list of `BatchMolGraph` objects, one per component, and `V_ds` is the parallel list of atom descriptor tensors or `None` values.

### MolAtomBond batches

MolAtomBond batches unpack as:

```python
bmg, V_d, E_d, X_d, Ys, weights, lt_masks, gt_masks, constraints = batch
```

`Ys`, `weights`, `lt_masks`, and `gt_masks` are ordered as molecule-level, atom-level, and bond-level values. Atom and bond target arrays are stacked across atoms/bonds in the batch. Detailed reaction and atom/bond constraint workflows belong in the specialized molecular sub-skill.

## Model Classes

### `MPNN`

```python
models.MPNN(
    message_passing,
    agg,
    predictor,
    batch_norm=False,
    metrics=None,
    warmup_epochs=2,
    init_lr=0.0001,
    max_lr=0.001,
    final_lr=0.0001,
    X_d_transform=None,
)
```

Core methods and properties:

- `output_dim`, `n_tasks`, `n_targets`, `criterion` reflect the predictor.
- `fingerprint(bmg, V_d=None, X_d=None)`: message passing → aggregation → optional batch norm → optional `X_d` concatenation.
- `encoding(bmg, V_d=None, X_d=None, i=-1)`: hidden representation from predictor MLP slice.
- `forward(bmg, V_d=None, X_d=None)`: predictions.
- `predict_step(batch, batch_idx, dataloader_idx=0)`: used by Lightning `Trainer.predict`.
- `load_from_file(model_path, map_location=None, strict=True, **submodules)`: load a Chemprop-saved model object.
- `load_from_checkpoint(checkpoint_path, ...)`: load a Lightning checkpoint.

`MPNN` is a `lightning.pytorch.LightningModule`; train it with `Trainer.fit(model, train_loader, val_loader)` and infer with `Trainer.predict(model, predict_loader)`.

### `MulticomponentMPNN`

```python
models.MulticomponentMPNN(
    message_passing,
    agg,
    predictor,
    batch_norm=False,
    metrics=None,
    warmup_epochs=2,
    init_lr=0.0001,
    max_lr=0.001,
    final_lr=0.0001,
    X_d_transform=None,
)
```

`message_passing` is `nn.MulticomponentMessagePassing(blocks, n_components, shared=False)`. Its `output_dim` is the sum of component block output dimensions, so the predictor `input_dim` must match that sum plus any `X_d` width.

### `MolAtomBondMPNN`

```python
models.MolAtomBondMPNN(
    message_passing,
    agg=None,
    mol_predictor=None,
    atom_predictor=None,
    bond_predictor=None,
    atom_constrainer=None,
    bond_constrainer=None,
    batch_norm=False,
    metrics=None,
    warmup_epochs=2,
    init_lr=0.0001,
    max_lr=0.001,
    final_lr=0.0001,
    X_d_transform=None,
)
```

Rules enforced by the constructor:

- At least one of `mol_predictor`, `atom_predictor`, or `bond_predictor` is required.
- If `mol_predictor` is supplied, `agg` is also required.
- `output_dimss`, `n_taskss`, `n_targetss`, and `criterions` return molecule/atom/bond tuples.

## Message Passing

Common public classes from `chemprop.nn`:

- `BondMessagePassing(d_v=..., d_e=..., d_h=300, bias=False, depth=3, dropout=0.0, activation="relu", undirected=False, d_vd=None, V_d_transform=None, graph_transform=None)`.
- `AtomMessagePassing(...)` with the same general options.
- `MulticomponentMessagePassing(blocks, n_components, shared=False)`.
- `MABBondMessagePassing` and `MABAtomMessagePassing` for MolAtomBond models.

`message_passing.output_dim` is the learned fingerprint width before any molecule-level `X_d` concatenation.

## Aggregations

Registered aggregation aliases include:

- `mean`: `nn.MeanAggregation()`.
- `sum`: `nn.SumAggregation()`.
- `norm`: `nn.NormAggregation(norm=100.0)`.

`MeanAggregation` and `SumAggregation` aggregate node embeddings by `bmg.batch`. `NormAggregation` divides the sum by a normalization constant.

## Predictors, Losses, and Metrics

Predictor registry aliases include:

- `regression`: `nn.RegressionFFN` with default `MSE` criterion and metric.
- `regression-mve`: `nn.MveFFN` with mean/variance output.
- `regression-evidential`: `nn.EvidentialFFN`.
- `regression-quantile`: `nn.QuantileFFN`.
- `classification`: `nn.BinaryClassificationFFN` with sigmoid inference and BCE-style training logits.
- `classification-dirichlet`: `nn.BinaryDirichletFFN`.
- `multiclass`: `nn.MulticlassClassificationFFN(n_classes=...)`.
- `multiclass-dirichlet`: `nn.MulticlassDirichletFFN(n_classes=...)`.
- `spectral`: `nn.SpectralFFN`.

Common predictor parameters:

```python
nn.RegressionFFN(
    n_tasks=1,
    input_dim=300,
    hidden_dim=300,
    n_layers=1,
    dropout=0.0,
    activation="relu",
    criterion=None,
    task_weights=None,
    threshold=None,
    output_transform=None,
)
```

Loss registry includes `mse`, `mae`, `rmse`, bounded variants, `mve`, `evidential`, quantile/pinball variants, `bce`, `ce`, MCC losses, `dirichlet`, `sid`, `earthmovers`/`wasserstein`, and `nlogprob_enrichment`. Metrics include `mse`, `mae`, `rmse`, bounded variants, `r2`, binary/multiclass MCC, ROC, PRC, accuracy, and F1.

## Save and Load

```python
from chemprop.models import save_model, load_model
from chemprop.models.utils import load_output_columns

save_model("model.pt", model, output_columns=["activity"])
model = load_model("model.pt")
columns = load_output_columns("model.pt")
```

`save_model(path, model, output_columns=None)` stores:

- `hyper_parameters`: model component hparams.
- `state_dict`: model weights.
- `output_columns`: optional task names.

`load_model(path, multicomponent=False, mol_atom_bond=False)` reloads onto CPU and chooses `MPNN`, `MulticomponentMPNN`, or `MolAtomBondMPNN` according to flags.

For legacy v2.0 checkpoints, loading errors may indicate that the file must be converted with Chemprop's conversion tooling before it can be loaded by v2.2.x.
