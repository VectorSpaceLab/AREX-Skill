# CLI Reference

Read this file when the user wants `pypots-cli` commands, config files, data
conversion, model listing, prediction/evaluation, tuning, or benchmark runs.
The CLI is built with Click and lazy-loads command modules so top-level help and
basic inspection stay fast.

## Top-Level Commands

Installed command:

```bash
pypots-cli --help
```

Verified command names:

- `benchmark`
- `data`
- `dev`
- `doc`
- `env`
- `evaluate`
- `info`
- `model`
- `predict`
- `recommend`
- `train`
- `tune`

Use `dev`, `doc`, and `env` only for maintainer-style repository operations;
they can mutate the current environment or checkout and may run long commands.

## Safe Inspection Commands

```bash
pypots-cli info
pypots-cli model list
pypots-cli model list --task imputation
pypots-cli model describe --name SAITS --task imputation
pypots-cli model config --name SAITS --task imputation
```

`info` prints the PyPOTS version, Python version, PyTorch/CUDA/MPS status,
model counts per task, and optional dependency status.

`model` subcommands:

| Subcommand | Purpose | Important options |
| --- | --- | --- |
| `list` | list models by task | `--task` optional |
| `describe` | show docstring and constructor parameters | `--name`, `--task` |
| `config` | generate a YAML/JSON config template | `--name`, `--task`, `--output` |
| `inspect` | inspect a saved `.pypots` checkpoint | `--path` |

## Training Command

```bash
pypots-cli train --config train.yaml
pypots-cli train --config train.yaml --epochs 1 --device cpu
```

Important options:

- `--config`: required YAML or JSON config.
- `--task`: override task in the config.
- `--model`: override model name in the config.
- `--train_set`, `--val_set`: override HDF5 data paths.
- `--epochs`, `--batch_size`, `--device`, `--saving_path`, `--seed`.

Minimal config shape:

```yaml
task: imputation
model:
  name: SAITS
  n_steps: 8
  n_features: 5
  n_layers: 1
  d_model: 8
  n_heads: 1
  d_k: 8
  d_v: 8
  d_ffn: 8
training:
  epochs: 1
  batch_size: 32
data:
  train_set: train.h5
  val_set: val.h5
```

The command filters constructor kwargs against the selected model signature, so
extra keys may be skipped with a warning rather than passed blindly.

## Prediction Command

```bash
pypots-cli predict \
  --model_path model.pypots \
  --test_set test.h5 \
  --config train.yaml \
  --output predictions.h5
```

Important options:

- `--model_path`: saved `.pypots` checkpoint.
- `--test_set`: HDF5 test set.
- `--config`: recommended, so the model architecture can be rebuilt before
  loading the checkpoint.
- `--task`, `--model`: override task/model when no config is available.
- `--output`: optional HDF5 output for the prediction dict.
- `--device`, `--file_type`.

## Evaluation Command

```bash
pypots-cli evaluate \
  --predictions predictions.h5 \
  --ground_truth ground_truth.h5 \
  --task imputation \
  --metrics mse,mae \
  --output eval.json
```

Supported task choices:

- `imputation`
- `classification`
- `forecasting`
- `anomaly_detection`
- `clustering`

Metric groups:

- Imputation/forecasting: `mse`, `mae`, `rmse`, `mre`.
- Classification/anomaly detection: `accuracy`, `precision`, `recall`, `f1`,
  `pr_auc`, `roc_auc`.
- Clustering: `rand_index`, `adjusted_rand_index`, `nmi`, `cluster_purity`,
  `silhouette`, `chs`, `dbs`.

For imputation/forecasting, the command looks for the task result key in
predictions and `X_ori` plus optionally `indicating_mask` in ground truth.

## Hyperparameter Tuning

```bash
pypots-cli tune --config tune.yaml --n_trials 5 --device cpu
```

Tuning uses Optuna. Configs include a normal `task`, `model`, `training`, and
`data` section plus:

```yaml
search_space:
  n_layers: {type: int, low: 1, high: 2}
  d_model: {type: categorical, choices: [32, 64]}
tuner:
  sampler: TPE
  n_trials: 20
  direction: minimize
```

Supported sampler names in the current CLI are `TPE`, `Random`, `CmaEs`, and
`Grid`. Supported pruner names include `MedianPruner`, `PercentilePruner`,
`HyperbandPruner`, and `NopPruner`.

## Recommendations

```bash
pypots-cli recommend --task imputation --model SAITS --n_steps 24 --n_features 10 --n_samples 500
pypots-cli recommend --task classification --model TimesNet --data data.csv
pypots-cli recommend --task imputation --data train.h5 --output config.yaml
```

The command can infer dimensions from HDF5 or CSV data, or accept explicit
`--n_steps`, `--n_features`, `--n_samples`, and `--n_classes`. If `--model` is
omitted, the command chooses a task-appropriate default.

## Benchmarking

```bash
pypots-cli benchmark --config benchmark.yaml --seed 2023 --output benchmark.json
```

Benchmark configs use a `models` list with per-model `params`, a shared `task`,
data paths, and metrics. A small imputation example:

```yaml
task: imputation
models:
  - name: Mean
    params: {}
  - name: Median
    params: {}
data:
  train_set: train.h5
  val_set: val.h5
  test_set: test.h5
metrics: [mse, mae]
```

## Data Commands

```bash
pypots-cli data describe --input train.h5
pypots-cli data describe --input samples.csv --json
pypots-cli data prepare --input train.csv --output train.h5 --task imputation --set_type train
pypots-cli data prepare --train train.csv --val val.csv --test test.csv --output_dir h5_sets --task imputation --missing_rate 0.1
pypots-cli data convert --input data.npy --output data.h5
pypots-cli data split --input data.h5 --output_dir split_data --train_ratio 0.7 --val_ratio 0.1 --test_ratio 0.2
pypots-cli data list
pypots-cli data load --dataset physionet_2012 --output_dir data --subset set-a --rate 0.1
```

Verified `data` subcommands:

| Subcommand | Purpose | Notes |
| --- | --- | --- |
| `profile` | analyze CSV with AI4TS DataProfile | requires `ai4ts` |
| `prepare` | CSV to PyPOTS HDF5 train/val/test format | single-file or batch mode |
| `reconstruct` | reconstruct original-shape CSV from windowed predictions | needs a window registry |
| `convert` | convert csv/npy/npz/pkl to h5/npy/pkl | safe for local files |
| `split` | split an HDF5 dataset into train/val/test | ratios must sum to 1 |
| `describe` | inspect HDF5 or CSV statistics | supports `--json` |
| `list` | list available benchmark datasets | no dataset download |
| `load` | download/load a benchmark dataset and write HDF5 splits | may need network/data cache |

Read `data-formats.md` before preparing CSV files; the data command detects
`SAMPLE_ID`, `TIMESTAMP`, and label columns containing `CLAF_TARGET`.

## Maintainer Commands

- `pypots-cli env --install {dev,full,doc,test,optional} --tool {conda,pip}`
  installs dependencies into the current Python environment. Do not run it in a
  user-owned environment without approval.
- `pypots-cli dev` can build, clean, run tests, show coverage, or lint. It
  requires the PyPOTS repository root and may delete build/test caches.
- `pypots-cli doc` can build or regenerate documentation. Some modes download
  code from GitHub or remove docs build outputs.

These commands are exposed by the package but are not ordinary modeling
workflows. Prefer direct package installation and the safe inspection commands
above unless the user explicitly asks for repository maintenance.
