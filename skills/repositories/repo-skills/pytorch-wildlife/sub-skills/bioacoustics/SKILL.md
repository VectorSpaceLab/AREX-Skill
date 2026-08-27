---
name: bioacoustics
description: "Prepare, train, and run passive-acoustic wildlife classifiers with
  PytorchWildlife 1.3.0, including YAML configuration, annotated audio windows,
  mel spectrograms, ResNet checkpoints, and CSV interpretation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Bioacoustics

Use this route for passive-acoustic wildlife monitoring: audio annotations,
window construction, mel-spectrogram caches, ResNet spectrogram classifiers,
and binary or multiclass CSV results. The supported package surface is
`PytorchWildlife.data.bioacoustics` and `PytorchWildlife.models.bioacoustics`
from PytorchWildlife 1.3.0, plus the public companion CLI contracts distilled
here.

## Route and boundaries

- Use this skill for YAML domain configuration, environment-variable
  expansion, COCO-like audio annotations, sliding/balanced/customized windows,
  spectrogram generation, `.npy` datasets, checkpoint inference, and the
  companion preparation/training/inference flags.
- Route image detection/classification to `detection` or `classification`.
  Route JSON/image/video serialization, visualization, and general video
  utilities to `data-and-postprocessing`.
- Do not start training, download model weights, download datasets, launch a
  service, or imply that CUDA is required. Training and real inference are
  explicit user-approved operations; parser and tiny-fixture checks are safe.

## Safe operating order

1. Copy a config and set `paths.data_root`, `paths.output_root`, and
   `paths.spectrograms_dir` to user-owned locations. `${VAR}` values are
   expanded by `load_config`; do not rely on an empty default path.
2. Validate `sample_rate > 0`, `window_size_sec > 0`, and
   `0 <= overlap_sec < window_size_sec`. For balanced windows use
   `0 <= negative_proportion < 1`; verify the output directories are writable.
   Use [configuration](references/configuration.md) for the exact nested keys
   and defaults.
3. Validate the annotation JSON and audio paths, then run statistics and
   build windows. The common 5-second/4-second setup has a 1-second hop.
   Choose `sliding` for full coverage, `balanced` for sampled negatives, or
   `customized` only with a supplied builder.
4. Generate missing mel `.npy` files, then create grouped train/validation/test
   CSVs. Keep recordings, not overlapping windows, as the split group to avoid
   leakage. Use the adapted [preparation helper](scripts/prepare_dataset.py);
   it has no checkout-relative imports.
5. Before training, check every CSV has the configured `x_col` (normally
   `spec_name`), `y_col` (`label`), and readable `.npy` files. A missing cache
   is a preparation problem, not a model problem. See [data formats](references/data-formats.md).
6. Train `ResNetClassifier` only after choosing binary (`num_classes == 2`) or
   multiclass (`num_classes > 2`) mode, checking class ids and checkpoint
   provenance. Use the companion flags summarized in [workflows](references/workflows.md).
7. For inference, use a local checkpoint and an audio folder, JSON, or CSV of
   windows. Resolve the device before loading the checkpoint; `cuda` falls
   back to `cpu` in the adapted helper when CUDA is unavailable. Use the
   [audio inference helper](scripts/audio_inference.py) and inspect its output
   schema before aggregation.

## Core contracts

- `DomainConfig` nests `PathConfig`, `AudioConfig`, `SpectrogramConfig`,
  `TrainingConfig`, and `SplitsConfig`. `load_config(path)` reads YAML and
  recursively expands environment variables; it does not fully validate
  numeric ranges, class counts, file existence, or writability.
- `build_windows(...)` returns window dictionaries containing
  `window_id`, `dataset`, `sample_rate`, `sound_id`, `start`, `end`, and
  `label`; multiclass windows also contain `ann_overlap`. `start` and `end`
  are sample indices at the requested target rate.
- `build_inference_windows(source, window_size_sec, overlap_sec, sample_rate)`
  accepts an audio directory or list of files and returns
  `window_id`, `sound_path`, `start`, and `end`. It needs `librosa` to obtain
  durations and rejects neither bad overlap nor missing files by itself, so
  validate first.
- `compute_mel_spectrograms_gpu(...)` is opportunistically accelerated: the
  implementation chooses CUDA when available and otherwise uses CPU. It
  reuses existing `.npy` files and defaults to
  `<audio-basename>_<start>_<end>.npy`, with `float32` storage. CUDA is an
  optional acceleration path, not a verified performance promise.
- `BioacousticsDataset` reads CSV paths and labels; it returns
  `(tensor, integer_label, path)`. `BioacousticsInferenceDataset` needs only
  the configured spectrogram-path column and returns `(tensor, path)`.
  Spectrograms are shaped to `[C,H,W]`, optionally normalized and resized.
- `ResNetClassifier` supports `resnet18`, `resnet34`, and `resnet50`. Binary
  mode emits one logit and uses sigmoid; multiclass mode emits `num_classes`
  logits and uses softmax/argmax. Constructor initialization may request
  ImageNet weights, so checkpoint inference can still require a local cache or
  network unless the dependency weights are already available.

## Output and review rules

Binary inference CSVs contain `audio`, `start(s)`, `end(s)`, `prediction`,
`probability`, and `confidence`. Multiclass CSVs contain `file_path`, `audio`,
`start(s)`, `end(s)`, `prediction`, one `<ClassName>_prob` per class (spaces
become underscores), and no binary confidence column in the companion writer.
Per-second binary aggregation produces `audio`, `second`, `count_overlaps`,
`prediction`, `avg_prediction`, `avg_probability`, and `avg_confidence`; it is
weighted by overlap duration and is not a multiclass reducer.

Treat a config with `num_classes` 0 or 1, too few/many class names, labels
outside `0..num_classes-1`, a missing `spec_name` column, missing `.npy` files,
or an invalid window geometry as a hard preflight failure. Keep original
recording identity and sample-rate units when interpreting timestamps. For
predictable failures, use [troubleshooting](references/troubleshooting.md).
