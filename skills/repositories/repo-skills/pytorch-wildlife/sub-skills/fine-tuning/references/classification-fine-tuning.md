# Classification fine-tuning contract

This is the legacy/experimental image-classification companion workflow. It
is useful for documenting a reproducible run, but it is not the primary core
PytorchWildlife classifier API.

## Dataset contract

The source dataset is a flat image directory: do not rely on nested image
folders for the annotation-driven training input. Keep the annotation CSV
outside the image directory and make `path` values relative to the CSV's
location/dataset root as configured by the run. Each row must contain:

| Column | Meaning | Requirement |
|---|---|---|
| `path` | image path | required; must resolve to one readable image |
| `classification` | numeric class id | required; use one stable id per class |
| `label` | human-readable class name | required; must agree with the id mapping |

The documented layout calls the dataset `Custom_Crop`. The source launcher
first writes split annotations, then invokes detector-based crop preparation
for train/validation (and a separate crop step for test). That crop stage
uses a core detector and can require model weights, compute, and a compatible
core environment. It is not performed by the bundled safe splitter. If
already-cropped data is available, verify the companion dataset's expected
crop annotation names and paths before launching the trainer rather than
assuming a generic ImageFolder layout.

The source dataset accepts common image extensions including JPG/JPEG, PNG,
PPM, BMP, PGM, TIF/TIFF, and WebP. Images are read as RGB. Training applies a
224x224 random-resized crop, horizontal/vertical flips, and color jitter,
then ImageNet normalization. Validation uses a 224x224 resize and the same
normalization. These augmentations can change the interpretation of small
animals or already-cropped boxes, so record them in the run notes.

## Split semantics and leakage control

`split_data: false` expects the required train/val/test artifacts to already
exist. With `split_data: true`, `split_path` identifies the single source CSV
and the launcher writes `train_annotations.csv`, `val_annotations.csv`, and
`test_annotations.csv` under the annotation output directory.

The accepted split types are:

- `random`: stratified by `classification`, with a fixed seed of 42 in the
  source random utility. This is a baseline only. Camera traps commonly emit
  bursts of nearly identical frames; random frame-level splitting can put
  those frames into different partitions and leak scene/animal identity.
- `location`: groups all rows with the same `Location` value into one
  partition. It does not guarantee class balance and requires the exact
  `Location` column in the source implementation.
- `sequence`: parses `Photo_Time` as a datetime and groups timestamps into
  30-second time bins before assigning whole groups to partitions. It does
  not guarantee class balance and requires `Photo_Time`; some prose uses the
  spelling `Photo_time`, so normalize that spelling before using the source
  utility or use the bundled helper, which reports the mismatch.

`test_size` and `val_size` are proportions of the full dataset in the config
concepts. Check that they are non-negative and sum to less than 1. The source
location/sequence functions declare arguments as `(val_size, test_size)`,
while the launcher passes the two config values positionally in the opposite
order. Equal values hide this issue. Use explicit keyword arguments or inspect
the generated row counts and group assignments before a real run.

The splitter in this skill keeps groups intact and refuses unsafe output
replacement unless explicitly enabled. It is a preflight aid, not a promise
that a small dataset has enough locations/sequences or per-class support for
stratification.

## Config concepts

The companion `configs/config.yaml` concepts are:

- Training: `conf_id`, `algorithm` (`Plain`), `log_dir`, `num_epochs`,
  `log_interval`, and `parallel`.
- Data: `dataset_root`, `dataset_name` (`Custom_Crop`), `annotation_dir`,
  `split_path`, `test_size`, `val_size`, `split_data`, `split_type`,
  `batch_size`, and `num_workers`.
- Model: `num_classes`, `model_name` (`PlainResNetClassifier`), `num_layers`
  (18 or 50), and `weights_init` (`ImageNet`).
- Optimization: `lr_feature`, `momentum_feature`, `weight_decay_feature`,
  `lr_classifier`, `momentum_classifier`, `weight_decay_classifier`,
  `step_size`, and `gamma`.

The supplied algorithm constructs separate feature and classifier parameter
sets and uses SGD with a StepLR scheduler. The model implementation downloads
ResNet-18 or ResNet-50 ImageNet state data when the model is constructed; a
first run therefore needs a local cache or an approved network action. Do not
use config parsing as evidence that weights are locally available.

Only the documented Plain ResNet classifier path should be considered
supported. Do not silently substitute an architecture: checkpoint structure,
feature dimensions, and class count must remain aligned.

## Typer launcher orientation

The launcher exposes a Typer command with these options and defaults:

| Option | Default | Purpose |
|---|---:|---|
| `--config` | `./configs/config.yaml` | YAML config path |
| `--project` | `Custom-classification` | logger/project label |
| `--gpus` | `0` | comma-separated GPU ids |
| `--logger-type` | `csv` | `csv`, `tensorboard`, `comet`, or `wandb` |
| `--evaluate` | unset | checkpoint for evaluation |
| `--np-threads` | `32` | numeric thread environment setting |
| `--session` | `0` | logger/checkpoint version |
| `--seed` | `0` | global seed |
| `--dev` | false | use `log_dev`/`weights_dev` roots |
| `--val` | false | validation mode with `--evaluate` |
| `--test` | false | test mode; also selects test crop handling |
| `--predict` | false | prediction mode |
| `--predict-root` | empty | root of prediction images |

Flags are modes, not independent training stages. With `--evaluate`, select
one of validation, test, or prediction; without it the launcher calls fit.
The source creates a Lightning trainer with a GPU accelerator setting even
when it has converted an unavailable CUDA device list to `None`. Treat CPU as
a structural preflight path, not as proof that the unmodified trainer will
complete on CPU; a local compatibility edit may be needed and must be recorded.

`csv` logging is the least credential-bound choice. TensorBoard writes local
logs. Comet and W&B require their respective credentials and network policy;
keep them disabled during construction and tiny checks.

## Outputs and integration

Normal logs are under a relative `log/<log_dir>/<algorithm>` tree, or
`log_dev/...` with development mode. Checkpoints are directed to
`weights/<log_dir>/<algorithm>`, or `weights_dev/...`, with a filename based
on `conf_id`, `session`, epoch, and `valid_mac_acc`. A test evaluation derives
an `eval.npz` beside the evaluated checkpoint. Prediction derives `_predict.npz`
and `_predict.json`; these contain companion-specific arrays/metadata rather
than the core PytorchWildlife result schema.

The classification README describes weight integration as a future feature.
Therefore, after a successful run, test the exact checkpoint with the core
classifier wrapper only if its loader contract is documented and a local
weight is available. Preserve the class-id-to-label mapping and preprocessing
parameters. If loading fails, do not rename or reshape the checkpoint as a
blind fix; route core inference to the classification sub-skill and report
the companion/core format gap.
