---
name: braindecode
description: "Routes EEG, ECoG, MEG, and related electrophysiology deep-learning
  workflows through the braindecode Python package, including dataset
  construction, preprocessing, model training, augmentation, and
  interpretation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Braindecode

Use this skill when a task names **braindecode**, or asks for deep learning on
EEG, ECoG, MEG, or similar electrophysiological recordings with MNE-shaped
objects, windowed datasets, skorch wrappers, or Braindecode model families.

## Operating sequence

1. Establish the input signal contract: channels, sampling frequency, units,
   recording/epoch layout, targets, and whether data are local or need a
   network-backed dataset.
2. Install PyTorch first, then `braindecode`; add only the optional extras that
   the selected workflow needs. The minimal check is:

   ```python
   import braindecode, torch
   print(braindecode.__version__, torch.__version__)
   print(torch.cuda.is_available())  # acceleration probe only
   ```

3. Route to exactly one primary workflow below. Workflows commonly compose in
   this order: datasets and windowing -> preprocessing -> models and training;
   add augmentation or interpretation only when requested.
4. Keep units and preprocessing identical between training and inference. Never
   infer a model's final temporal shape from the model name; use its signal
   parameters and a tiny forward check.
5. Treat MOABB, BIDS/OpenNeuro, TUH, Sleep Physionet, Hugging Face Hub,
   EEGPrep, and pretrained checkpoints as optional integrations requiring their
   own dependencies, data, network, credentials, or storage.

## Focused routes

- **Datasets and windows**: Construct datasets from NumPy/MNE objects, attach
  descriptions and targets, create event/fixed/target-channel windows, split,
  concatenate, or serialize data. Read
  [datasets-and-windowing](sub-skills/datasets-and-windowing/SKILL.md).
- **Preprocessing**: Apply MNE-backed or array-backed preprocessors, filters,
  resampling, channel operations, scaling, windowing order, parallel execution,
  or serialized preprocessing. Read
  [preprocessing](sub-skills/preprocessing/SKILL.md).
- **Models and training**: Select/configure a model, infer signal parameters,
  train `EEGClassifier`/`EEGRegressor`, use cropped decoding, score/predict, or
  load a local/pretrained model. Read
  [models-and-training](sub-skills/models-and-training/SKILL.md).
- **Augmentation and sampling**: Compose signal transforms, use
  `AugmentedDataLoader`, or construct sequence, relative-positioning, or
  self-supervised samplers. Read
  [augmentation-and-sampling](sub-skills/augmentation-and-sampling/SKILL.md).
- **Interpretation and visualization**: Compute Captum attributions, frequency
  gradients, topomaps, confusion/metric plots, or sanity checks. Read
  [interpretation-and-visualization](sub-skills/interpretation-and-visualization/SKILL.md).

## Shared guardrails

- Use float32 tensors shaped `(batch, channels, time)` unless a selected model
  explicitly documents another shape. Preserve channel order and sampling rate.
- Split by subject/session before overlapping windows when evaluating
  generalization. Do not leak windows from the same recording across splits.
- Keep runtime scripts self-contained and local-data-only by default. Do not
  run long gallery examples, download datasets, upload private recordings, or
  log in to a model/data Hub without explicit authorization.
- For missing optional integrations, report the exact extra or package and
  continue with a local synthetic fixture where behavior is equivalent.
- Read [API reference](references/api-reference.md) for the verified public
  surface, [troubleshooting](references/troubleshooting.md) for cross-cutting
  failures, and [provenance](references/repo-provenance.md) before deciding
  whether this graph is stale for a checkout.
