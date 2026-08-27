# Chemprop Python API Troubleshooting

Use this guide when Python Chemprop workflows fail before or during Lightning training, prediction, or model loading.

## RDKit molecule construction fails

Symptoms:

- `MoleculeDatapoint.from_smi(...)` raises an RDKit or Chemprop molecule-construction error.
- Later featurization fails because `mol` is invalid.

Fixes:

- Validate SMILES before creating datapoints.
- Use the relevant `from_smi` options when chemistry assumptions require them: `keep_h`, `add_h`, `ignore_stereo`, and `reorder_atoms`.
- For prediction-only data, omit `y` but still provide valid molecules.
- Do not pass `None` as the molecule to `MoleculeDatapoint`; use `from_smi` or an RDKit `Mol`.

## Dataloader batch shape errors

Symptoms:

- `ValueError` about number of molecules and descriptors/targets having different lengths.
- `InvalidShapeError` for `V_d`.
- Runtime concatenation errors in collate or message passing.

Checks:

- `len(dataset)` equals the number of target rows and descriptor rows.
- Every `y` has length `n_tasks`.
- Every `x_d` has the same molecule descriptor width.
- Every atom in a molecule has a `V_d` row when using atom descriptors.
- `V_d.shape[1]` equals `d_vd` supplied to `BondMessagePassing` or `AtomMessagePassing`.
- Extra atom/bond feature arrays match the molecule atom/bond order and are provided through a featurizer configured with matching extra dimensions.

Batch unpacking for plain models must match:

```python
bmg, V_d, X_d, targets, weights, lt_mask, gt_mask = batch
```

MolAtomBond and multicomponent loaders have different batch signatures; do not feed their batches into a plain `MPNN` unless the model type matches.

## Predictor input dimension mismatch

Symptoms:

- Matrix multiplication errors in the predictor MLP.
- `mat1 and mat2 shapes cannot be multiplied`.

Fixes:

- For plain models without `X_d`, use `nn.RegressionFFN(input_dim=mp.output_dim)`.
- With molecule descriptors, use `input_dim=mp.output_dim + dataset.d_xd` and pass `X_d_transform` if the descriptors were normalized.
- For multicomponent models, use `input_dim=multicomponent_message_passing.output_dim` plus any `X_d` width.
- If you change `d_h`, `d_vd`, or component count, rebuild the predictor with the new input dimension.

Quick assertion:

```python
batch = next(iter(data.build_dataloader(dataset, batch_size=2, shuffle=False)))
bmg, V_d, X_d, *_ = batch
fingerprint = model.fingerprint(bmg, V_d, X_d)
assert fingerprint.shape[1] == model.predictor.input_dim
```

## Predictor, loss, or target mismatch

Symptoms:

- Loss function raises shape/type errors.
- Classification metrics produce invalid values.
- Multiclass training fails around class dimensions.

Fixes:

- Regression targets: float matrix `(n_samples, n_tasks)`; use `RegressionFFN`, `MveFFN`, `EvidentialFFN`, or `QuantileFFN` with matching regression losses.
- Binary classification targets: 0/1 values with shape `(n_samples, n_tasks)`; use `BinaryClassificationFFN` or `BinaryDirichletFFN`.
- Multiclass targets: integer class labels per task; use `MulticlassClassificationFFN(n_classes=...)`.
- Spectral targets: spectrum-shaped nonnegative distributions; use spectral predictors/losses.
- Missing target values should be `np.nan` so Chemprop can mask them with `targets.isfinite()`.
- Bounded losses require appropriate `lt_mask` and `gt_mask` arrays.

## Lightning CPU/GPU configuration fails

Symptoms:

- Trainer cannot initialize accelerator/devices.
- CUDA is unavailable or device count is wrong.
- A loaded model has CPU tensors while the trainer expects GPU tensors.

Fixes:

- First prove the workflow with `pl.Trainer(accelerator="cpu", devices=1, ...)`.
- Use `accelerator="auto", devices="auto"` only after the CPU path works.
- `chemprop.models.load_model` maps model files to CPU by default; Lightning moves the model during `fit`, `test`, or `predict`.
- Keep batches on the dataloader/model path instead of manually moving partial batch fields to devices.
- For tiny examples, set `logger=False`, `enable_checkpointing=False`, and `log_every_n_steps=1` to reduce noise.

## Batch normalization drops or changes small batches

Symptoms:

- A final datapoint disappears from a training epoch.
- Validation/test behavior differs with batch size 1.
- Metrics differ between manual forward calls and Lightning evaluation.

Fixes:

- `build_dataloader(..., drop_last=None)` may drop a final batch of size 1 to avoid batch normalization issues.
- Set `batch_norm=False` for tiny smoke tests, or choose a batch size that avoids a final singleton batch.
- Use Lightning `Trainer` methods for validation/test so `eval()` state is handled consistently.

## Save/load output columns missing or misordered

Symptoms:

- Predictions are numerically available but task names are lost.
- Loaded model predictions are assigned to the wrong DataFrame columns.

Fixes:

- Save task names with `save_model(path, model, output_columns=[...])`.
- Recover names with `load_output_columns(path)`.
- Make sure the number and order of `output_columns` match the predictor task order.
- For MolAtomBond models, `output_columns` may be a tuple for molecule, atom, and bond outputs.

## Model file fails to load

Symptoms:

- `KeyError` about missing `hyper_parameters` or `state_dict`.
- Error message indicates an older v2.0 checkpoint.
- Custom metric/predictor cannot be rebuilt.

Fixes:

- Prefer Chemprop `save_model` for portable `.pt` files.
- Use `models.MPNN.load_from_checkpoint` only for Lightning checkpoint files.
- For multicomponent or MolAtomBond saved files, pass the correct flags to `load_model`.
- Convert legacy v2.0 checkpoints with Chemprop conversion tooling before loading in v2.2.x.
- If using custom components, ensure their Python classes are importable when loading.

## Scaling transforms appear inactive

Symptoms:

- `ScaleTransform` returns the original tensor.
- `UnscaleTransform` does not change predictions during an inspection snippet.

Explanation and fixes:

- Chemprop transforms intentionally return input unchanged while the module is in training mode.
- Call `model.eval()` or use `Trainer.predict`/`Trainer.test` to activate evaluation behavior.
- For target scaling, attach `UnscaleTransform` to the predictor, not to the dataset.
- For `X_d`, normalize dataset descriptors and pass `X_d_transform` to `MPNN`.
- For `V_d`, normalize dataset descriptors and pass `V_d_transform` to the message-passing block with matching `d_vd`.

## Prediction order changes

Symptoms:

- Output rows do not correspond to input rows.
- Lightning warns about shuffled prediction dataloaders.

Fixes:

- Always build prediction dataloaders with `shuffle=False`.
- Preserve `dataset.names` or an external ID column alongside predictions.
- Avoid class-balanced samplers for prediction.

## Minimal diagnostic checklist

1. Can RDKit parse every SMILES?
2. Does `len(dataset)` match targets, weights, and descriptors?
3. Does the first batch unpack into the expected signature?
4. Does `model.fingerprint(...).shape[1]` equal `predictor.input_dim`?
5. Does a CPU `Trainer(..., max_epochs=1)` run?
6. Can `save_model` and `load_model` round-trip the model?
7. Do `output_columns` match the expected task names and count?
