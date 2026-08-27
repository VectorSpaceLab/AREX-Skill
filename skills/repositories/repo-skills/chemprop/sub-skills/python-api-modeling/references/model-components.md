# Chemprop Model Components

Chemprop Python models are assembled from data, message passing, aggregation, predictor, metric/loss, transform, and Lightning training components. Most runtime errors come from incompatible dimensions or task/loss mismatches.

## Plain `MPNN` Data Flow

For a plain molecular `MPNN`:

```text
BatchMolGraph + optional V_d
  -> message_passing(bmg, V_d)
  -> node embeddings H_v
  -> aggregation(H_v, bmg.batch)
  -> graph fingerprint H
  -> optional batch norm
  -> optional concat(X_d_transform(X_d))
  -> predictor(H)
```

Constructor:

```python
model = models.MPNN(
    message_passing=nn.BondMessagePassing(),
    agg=nn.MeanAggregation(),
    predictor=nn.RegressionFFN(),
    batch_norm=False,
    metrics=None,
    warmup_epochs=2,
    init_lr=1e-4,
    max_lr=1e-3,
    final_lr=1e-4,
    X_d_transform=None,
)
```

Dimension rule:

```python
predictor_input_dim = message_passing.output_dim + dataset.d_xd
```

Use only `message_passing.output_dim` when there is no `X_d`.

## Message Passing Blocks

Use `BondMessagePassing` for the common directed-bond Chemprop architecture. Use `AtomMessagePassing` when atom-centered message passing is required.

Important parameters:

- `d_h`: hidden dimension; default is 300.
- `depth`: message-passing iterations; default is 3.
- `dropout`: dropout probability.
- `activation`: string or module; common values include `"relu"` and `"tanh"`.
- `undirected`: averages reverse directed-edge messages at each depth step.
- `d_vd`: width of atom descriptors `V_d` concatenated after message passing.
- `V_d_transform`: `ScaleTransform` for atom descriptors.
- `graph_transform`: `GraphTransform` for extra atom/bond features in the batched graph.

`output_dim` is inferred from the internal final projection. For `d_vd`, output width may include descriptor width according to the configured final descriptor projection.

## Aggregation

Public aggregation classes:

```python
nn.MeanAggregation()
nn.SumAggregation()
n.NormAggregation(norm=100.0)
```

Registered aliases: `mean`, `sum`, `norm`.

Use `MeanAggregation` for a robust default. Use `SumAggregation` when target scale should grow with molecule size. Use `NormAggregation` when you want sum-like behavior normalized by a fixed constant.

## Predictors

Common predictor constructor parameters:

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

`hidden_dim` can be a single integer or a sequence. `n_layers=1` makes a shallow predictor. `output_transform` is most often `UnscaleTransform` for regression outputs.

### Predictor compatibility table

| Task | Class | Registry alias | Target shape | Inference output |
| --- | --- | --- | --- | --- |
| Regression | `RegressionFFN` | `regression` | `(batch, n_tasks)` floats | unscaled/linear values |
| MVE regression | `MveFFN` | `regression-mve` | `(batch, n_tasks)` floats | `(batch, n_tasks, 2)` mean and variance |
| Evidential regression | `EvidentialFFN` | `regression-evidential` | `(batch, n_tasks)` floats | `(batch, n_tasks, 4)` distribution parameters |
| Quantile regression | `QuantileFFN` | `regression-quantile` | `(batch, n_tasks)` floats | `(batch, n_tasks, 2)` mean and interval |
| Binary classification | `BinaryClassificationFFN` | `classification` | `(batch, n_tasks)` 0/1 floats | sigmoid probabilities |
| Binary Dirichlet | `BinaryDirichletFFN` | `classification-dirichlet` | `(batch, n_tasks)` 0/1 floats | positive-class probability plus uncertainty |
| Multiclass | `MulticlassClassificationFFN` | `multiclass` | `(batch, n_tasks)` integer labels | class probabilities |
| Multiclass Dirichlet | `MulticlassDirichletFFN` | `multiclass-dirichlet` | `(batch, n_tasks)` integer labels | class probabilities plus uncertainty-like values |
| Spectral | `SpectralFFN` | `spectral` | spectrum-shaped targets | normalized spectral probabilities |

Uncertainty-specific model interpretation belongs in `uncertainty-advanced`; this reference only covers wiring.

## Losses and Metrics

Losses available through Chemprop include:

- Regression: `MSE`, `MAE`, `RMSE`, and bounded variants.
- Uncertainty/interval: `MVELoss`, `EvidentialLoss`, `QuantileLoss` and point/pinball variants.
- Classification: `BCELoss`, `CrossEntropyLoss`, `BinaryMCCLoss`, `MulticlassMCCLoss`, `DirichletLoss`.
- Spectral/distribution: `SID`, `Wasserstein`/earthmovers, `nlogprob_enrichment`.

Metrics include `MSE`, `MAE`, `RMSE`, bounded variants, `R2Score`, binary/multiclass MCC, binary AUROC, binary AUPRC, binary accuracy, and binary F1.

Pattern:

```python
predictor = nn.RegressionFFN(criterion=nn.BoundedMSE())
model = models.MPNN(mp, agg, predictor, metrics=[nn.RMSE(), nn.MAE()])
```

Chemprop masks missing targets with `targets.isfinite()` inside training/evaluation. Missing targets should be `np.nan`, not empty strings or `None` inside a fixed target vector.

## Transforms and Scaling

### Target scaling

```python
output_scaler = train_dataset.normalize_targets()
val_dataset.normalize_targets(output_scaler)
predictor = nn.RegressionFFN(
    input_dim=mp.output_dim,
    output_transform=nn.UnscaleTransform.from_standard_scaler(output_scaler),
)
```

`UnscaleTransform` is no-op during training and active during evaluation/inference.

### Molecule descriptor scaling

```python
x_scaler = train_dataset.normalize_inputs("X_d")
val_dataset.normalize_inputs("X_d", x_scaler)
model = models.MPNN(
    mp,
    agg,
    nn.RegressionFFN(input_dim=mp.output_dim + train_dataset.d_xd),
    X_d_transform=nn.ScaleTransform.from_standard_scaler(x_scaler),
)
```

`X_d_transform` is applied after aggregation and before predictor input concatenation.

### Atom descriptor scaling

```python
v_scaler = train_dataset.normalize_inputs("V_d")
val_dataset.normalize_inputs("V_d", v_scaler)
mp = nn.BondMessagePassing(
    d_vd=train_dataset.d_vd,
    V_d_transform=nn.ScaleTransform.from_standard_scaler(v_scaler),
)
```

`V_d` arrays are concatenated across atoms by the dataloader, so the descriptor length must match every atom in every molecule.

### Graph feature scaling

Use `GraphTransform(V_transform, E_transform)` for batched graph tensors. The transforms often need padding for the base atom/bond feature dimensions so only extra features are scaled.

## Multicomponent Components

```python
blocks = [nn.BondMessagePassing(), nn.BondMessagePassing()]
mc_mp = nn.MulticomponentMessagePassing(blocks=blocks, n_components=2, shared=False)
predictor = nn.RegressionFFN(input_dim=mc_mp.output_dim)
model = models.MulticomponentMPNN(mc_mp, nn.MeanAggregation(), predictor)
```

Rules:

- `shared=False`: `len(blocks)` must equal `n_components`.
- `shared=True`: one block can be reused for all components; if multiple blocks are supplied, Chemprop keeps the first block.
- `mc_mp.output_dim` is the sum of component block widths.

## Save/Load Components

`save_model` records class objects and constructor hparams for message passing, aggregation, predictor, transforms, criterion, and metrics. Custom components must be importable and reconstructible in the runtime process if you expect `load_model` to rebuild them automatically.

```python
save_model("model.pt", model, output_columns=["task_a", "task_b"])
loaded = load_model("model.pt")
```

When `output_columns` are present, use `load_output_columns` to preserve task ordering in downstream DataFrames.

## Lightning Integration

`MPNN`, `MulticomponentMPNN`, and `MolAtomBondMPNN` are Lightning modules.

Training:

```python
trainer.fit(model, train_loader, val_loader)
```

Validation/test:

```python
trainer.validate(model, val_loader)
trainer.test(model, test_loader)
```

Prediction:

```python
preds = torch.cat(trainer.predict(model, pred_loader), dim=0)
```

For small smoke tests, use:

```python
pl.Trainer(accelerator="cpu", devices=1, logger=False, enable_checkpointing=False, max_epochs=1)
```
