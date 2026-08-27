---
name: models-and-training
description: "Guides braindecode model selection, signal-parameter
  initialization, skorch classifier or regressor training, cropped decoding,
  prediction, and local checkpoint use."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Models and training

Use this route when a task asks for a Braindecode model, model registry lookup,
`EEGClassifier`, `EEGRegressor`, cropped decoding, fine-tuning, evaluation,
regression, or local pretrained weights.

## Workflow

1. Start with a validated dataset/window contract: channels, samples, `sfreq`,
   dtype, target type, and output count. Run a model forward before training.
2. Choose a representative model family from the overview, then pass explicit
   `n_chans`/`n_times`/`n_outputs`/`sfreq` or let the skorch wrapper infer signal
   parameters from a compatible dataset. Use `final_conv_length="auto"` only
   when the model supports it and verify the resulting shape.
3. Configure `EEGClassifier` or `EEGRegressor` with an optimizer, criterion,
   split, batch size, callbacks, and explicit `device`. `module` may be a class,
   name from the registry, or initialized module depending on the route; verify
   the wrapper's accepted form.
4. Distinguish trialwise output from dense/cropped output. Use `CroppedLoss` and
   compatible aggregation only for window/crop workflows; inspect predictions
   and targets before reporting a metric.
5. For pretrained models, validate checkpoint keys and tensor shapes locally,
   keep the classification head distinction explicit, and never download or
   upload a checkpoint without authorization.

Read [model overview](references/model-overview.md), [API reference](references/api-reference.md),
[training workflows](references/training-workflows.md), [pretrained models](references/pretrained-models.md),
and [troubleshooting](references/troubleshooting.md). Run the bounded local
[training smoke](scripts/smoke_train.py) before an expensive experiment.
