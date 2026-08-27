# Chemprop Python Workflows

These recipes are intended for coding agents writing reusable Python code around Chemprop v2. They avoid CLI-only patterns and use public package APIs.

## Minimal Regression Training

```python
import numpy as np
from lightning import pytorch as pl
from chemprop import data, models, nn

smiles = ["CCO", "CCN", "CCC", "c1ccccc1"]
targets = np.array([[0.1], [0.2], [0.25], [0.4]], dtype=float)

dataset = data.MoleculeDataset([
    data.MoleculeDatapoint.from_smi(smi, y=target)
    for smi, target in zip(smiles, targets)
])
train_loader = data.build_dataloader(dataset, batch_size=2, shuffle=True)
val_loader = data.build_dataloader(dataset, batch_size=2, shuffle=False)

message_passing = nn.BondMessagePassing(d_h=64, depth=2)
aggregation = nn.MeanAggregation()
predictor = nn.RegressionFFN(input_dim=message_passing.output_dim, hidden_dim=64, n_tasks=1)
model = models.MPNN(message_passing, aggregation, predictor, metrics=[nn.RMSE(), nn.MAE()])

trainer = pl.Trainer(
    accelerator="cpu",
    devices=1,
    logger=False,
    enable_checkpointing=False,
    max_epochs=2,
    log_every_n_steps=1,
)
trainer.fit(model, train_loader, val_loader)
```

Notes:

- `MoleculeDatapoint.from_smi` builds RDKit molecules internally; invalid SMILES fail before model training.
- Use at least two datapoints per batch when `batch_norm=True`.
- For prediction or validation, set `shuffle=False` to preserve row order.

## Prediction With Row Order Preserved

```python
predict_dataset = data.MoleculeDataset([
    data.MoleculeDatapoint.from_smi(smi) for smi in ["CCO", "CCN"]
])
predict_loader = data.build_dataloader(predict_dataset, batch_size=64, shuffle=False)

pred_batches = trainer.predict(model, predict_loader)
predictions = torch.cat(pred_batches, dim=0)
```

If the model is already trained and no trainer exists, construct a small prediction trainer:

```python
trainer = pl.Trainer(accelerator="cpu", devices=1, logger=False, enable_checkpointing=False)
predictions = torch.cat(trainer.predict(model, predict_loader), dim=0)
```

## Fingerprints and Encodings

Use `model.fingerprint` for learned graph representations and `model.encoding` for predictor hidden representations.

```python
batch = next(iter(data.build_dataloader(dataset, batch_size=2, shuffle=False)))
bmg, V_d, X_d, *_ = batch

model.eval()
with torch.no_grad():
    fp = model.fingerprint(bmg, V_d, X_d)
    hidden = model.encoding(bmg, V_d, X_d, i=-1)
    preds = model(bmg, V_d, X_d)
```

Shape checks:

- `fp.shape[0]` equals the number of molecules in the batch.
- `fp.shape[1]` equals message-passing output width plus any `X_d` descriptor width after `X_d_transform`.
- `preds.shape[0]` equals batch size; later dimensions depend on predictor type.

## Scaling Regression Targets

For regression, normalize train targets and pass the scaler to validation/test datasets. Add an `UnscaleTransform` to the predictor so inference returns original target units.

```python
from chemprop.nn.transforms import UnscaleTransform

output_scaler = train_dataset.normalize_targets()
val_dataset.normalize_targets(output_scaler)

output_transform = UnscaleTransform.from_standard_scaler(output_scaler)
predictor = nn.RegressionFFN(input_dim=mp.output_dim, output_transform=output_transform)
model = models.MPNN(mp, nn.NormAggregation(), predictor)
```

Important behavior:

- `ScaleTransform` and `UnscaleTransform` are no-ops while the module is in training mode.
- During evaluation and prediction, `UnscaleTransform` maps regression outputs back to original units.
- For variance-producing predictors, `UnscaleTransform.transform_variance` scales variance by `scale ** 2`.

## Scaling Extra Descriptors and Features

Use dataset normalization methods for arrays and pass matching transform modules into the model.

### Molecule descriptors `X_d`

`X_d` is concatenated after aggregation, so the predictor input dimension must include `dataset.d_xd`.

```python
from chemprop.nn.transforms import ScaleTransform

x_scaler = train_dataset.normalize_inputs("X_d")
val_dataset.normalize_inputs("X_d", x_scaler)

x_transform = ScaleTransform.from_standard_scaler(x_scaler)
input_dim = mp.output_dim + train_dataset.d_xd
predictor = nn.RegressionFFN(input_dim=input_dim)
model = models.MPNN(mp, nn.MeanAggregation(), predictor, X_d_transform=x_transform)
```

### Atom descriptors `V_d`

`V_d` is concatenated inside message passing finalization. Set `d_vd` on the message passing block and pass a `V_d_transform`.

```python
v_scaler = train_dataset.normalize_inputs("V_d")
val_dataset.normalize_inputs("V_d", v_scaler)

v_transform = ScaleTransform.from_standard_scaler(v_scaler)
mp = nn.BondMessagePassing(d_vd=train_dataset.d_vd, V_d_transform=v_transform)
predictor = nn.RegressionFFN(input_dim=mp.output_dim)
model = models.MPNN(mp, nn.MeanAggregation(), predictor)
```

### Extra atom/bond features `V_f` and `E_f`

`V_f` and `E_f` extend the molgraph featurizer dimensions before message passing. Use a featurizer configured with the extra feature widths, then use `GraphTransform` for scaling.

```python
from chemprop.featurizers import SimpleMoleculeMolGraphFeaturizer
from chemprop.nn.transforms import GraphTransform, ScaleTransform

featurizer = SimpleMoleculeMolGraphFeaturizer(
    extra_atom_fdim=n_extra_atom_features,
    extra_bond_fdim=n_extra_bond_features,
)
train_dataset = data.MoleculeDataset(train_datapoints, featurizer=featurizer)
val_dataset = data.MoleculeDataset(val_datapoints, featurizer=featurizer)

v_f_scaler = train_dataset.normalize_inputs("V_f")
e_f_scaler = train_dataset.normalize_inputs("E_f")
val_dataset.normalize_inputs("V_f", v_f_scaler)
val_dataset.normalize_inputs("E_f", e_f_scaler)

base_atom_dim = featurizer.atom_fdim - featurizer.extra_atom_fdim
base_bond_dim = featurizer.bond_fdim - featurizer.extra_bond_fdim
graph_transform = GraphTransform(
    ScaleTransform.from_standard_scaler(v_f_scaler, pad=base_atom_dim),
    ScaleTransform.from_standard_scaler(e_f_scaler, pad=base_bond_dim),
)
mp = nn.BondMessagePassing(graph_transform=graph_transform)
```

## Metrics and Custom Losses

Pass metrics to `models.MPNN(..., metrics=[...])`. The predictor criterion is always added to the internal metric list for validation loss tracking.

```python
metrics = [nn.RMSE(), nn.MAE(), nn.R2Score()]
predictor = nn.RegressionFFN(criterion=nn.MSE())
model = models.MPNN(nn.BondMessagePassing(), nn.MeanAggregation(), predictor, metrics=metrics)
```

For bounded regression targets, provide `lt_mask` and `gt_mask` arrays on datapoints and use bounded losses/metrics such as `nn.BoundedMSE()`.

For classification:

```python
binary_predictor = nn.BinaryClassificationFFN(input_dim=mp.output_dim, n_tasks=1)
multiclass_predictor = nn.MulticlassClassificationFFN(input_dim=mp.output_dim, n_classes=3, n_tasks=1)
```

Binary classification inference returns sigmoid probabilities; training uses logits internally. Multiclass inference returns class probabilities; training uses raw class logits internally.

## Multicomponent Model Wiring

```python
blocks = [nn.BondMessagePassing(d_h=128), nn.BondMessagePassing(d_h=128)]
multicomponent_mp = nn.MulticomponentMessagePassing(blocks=blocks, n_components=2, shared=False)
aggregation = nn.MeanAggregation()
predictor = nn.RegressionFFN(input_dim=multicomponent_mp.output_dim)
model = models.MulticomponentMPNN(multicomponent_mp, aggregation, predictor)
```

If `shared=True`, pass one block or understand that only the first block is used for every component. If `shared=False`, `len(blocks)` must equal `n_components`.

## Ensembling

Chemprop models can be trained independently and averaged after prediction.

```python
ensemble = [
    models.MPNN(nn.BondMessagePassing(), nn.MeanAggregation(), nn.RegressionFFN())
    for _ in range(3)
]

for member in ensemble:
    trainer = pl.Trainer(accelerator="cpu", devices=1, logger=False, enable_checkpointing=False, max_epochs=1)
    trainer.fit(member, train_loader, val_loader)

pred_loader = data.build_dataloader(predict_dataset, shuffle=False)
member_preds = [torch.cat(trainer.predict(member, pred_loader), dim=0) for member in ensemble]
mean_prediction = torch.stack(member_preds, dim=0).mean(dim=0)
```

For reproducible ensembles, control data split seeds, dataloader seeds, and Torch/NumPy random seeds outside the model construction loop.

## Save, Load, and Output Columns

```python
from chemprop.models import save_model, load_model
from chemprop.models.utils import load_output_columns

save_model("model.pt", model, output_columns=["pIC50"])
loaded = load_model("model.pt")
columns = load_output_columns("model.pt")
```

Use flags for non-plain model types:

```python
loaded_multi = load_model("multi.pt", multicomponent=True)
loaded_mab = load_model("mab.pt", mol_atom_bond=True)
```

Class-level loaders are useful when injecting reconstructed submodules or loading Lightning checkpoint files:

```python
plain = models.MPNN.load_from_file("model.pt")
from_checkpoint = models.MPNN.load_from_checkpoint("last.ckpt")
```

## CPU/GPU Lightning Settings

CPU-safe trainer:

```python
pl.Trainer(accelerator="cpu", devices=1, logger=False, enable_checkpointing=False, max_epochs=1)
```

GPU/auto trainer:

```python
pl.Trainer(accelerator="auto", devices="auto", max_epochs=20)
```

If GPU configuration is failing, first prove the same code path on CPU. Chemprop model files loaded with `load_model` are mapped to CPU by default; Lightning can move the model during training or prediction.
