# Training workflows

## Synthetic classification

Create a small local MNE `EpochsArray` or `BaseConcatDataset`, infer signal
properties, instantiate `ShallowFBCSPNet`/`EEGNet`, and run one bounded epoch
with `EEGClassifier`. Use a deterministic seed, CPU device, small batch, and a
validation split. Confirm that `history` contains train/valid losses and that
`predict` has one row per input trial.

## Cropped decoding

Use a continuous recording or compatible window dataset and set model/output
window parameters consistently. A dense prediction model emits multiple crop
predictions; `CroppedLoss` and `aggregate_predictions` determine how these map
to trial-level targets. Verify crop count and aggregation on a tiny dataset
before running a full recording.

## Regression

Use `EEGRegressor` with a model whose output dimension matches the regression
target. Keep target dtype/shape explicit, avoid class encodings, and compare
`predict(X)` against the target shape before selecting MAE/MSE or a custom score.

## Splits and evaluation

Partition by subject/session/recording before overlapping windows. Use
`predefined_split` when a separate validation dataset is available; otherwise
use a deterministic `ValidSplit`. Report the split unit and whether predictions
were crop- or trial-aggregated.

## Fine-tuning

For a pretrained module, instantiate with checkpoint-compatible signal facts,
load local weights with `map_location`, inspect missing/unexpected keys, replace
or freeze the task head, and run a forward pass. Only then construct the
skorch wrapper. Hub download and login remain optional, network-bound actions.
