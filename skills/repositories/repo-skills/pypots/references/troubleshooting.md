# Troubleshooting

Read this file when an install, import, backend, data, CLI, model-training, or
checkpoint workflow fails. Start with the smallest reproducible check before
running a long training job.

## Install and Import Failures

### `ModuleNotFoundError: No module named 'pypots'`

Likely cause: PyPOTS is not installed in the active Python environment.

Recovery:

```bash
pip install pypots
python -c "import pypots; print(pypots.__version__)"
```

For a local checkout:

```bash
pip install -e .
```

Then run the bundled check:

```bash
python scripts/check_install.py
```

### Missing Runtime Dependencies

The package expects scientific Python, PyTorch, transformers, HDF5, and the
PyPOTS ecosystem packages (`tsdb`, `pygrinder`, `benchpots`, `ai4ts`) for the
broad public surface. If import errors name one of these packages, reinstall the
base package in the target environment.

### YAML Config Import Errors

Symptoms:

- `ImportError: PyYAML is required to load YAML config files.`
- CLI config commands work for JSON but not YAML.

Recovery:

```bash
pip install pyyaml
```

## Optional Backend Failures

### Raindrop and GNN Dependencies

Symptoms include errors mentioning `torch_geometric`, `torch_scatter`, or
`torch_sparse` when using `Raindrop`.

Recovery:

- Install the PyG stack compatible with the active PyTorch build.
- For pip installs, use the wheel index recommended by PyTorch Geometric for
  the exact `torch` and CUDA/CPU variant.
- For conda installs, use the `pyg` channel variants documented by PyG.
- If you do not need `Raindrop`, choose another classification model such as
  `TS2Vec`, `TimesNet`, `BRITS`, `CSAI`, `GRUD`, `SAITS`, or `TEFN`.

### CUDA Requested but Unavailable

Symptoms:

- `You are trying to use CUDA for model training, but CUDA is not available in your environment.`
- `torch.cuda.is_available()` is `False`.

Recovery:

- Use `device="cpu"` for correctness checks.
- Install a PyTorch build compatible with the host driver and GPU.
- Do not treat a CPU import as proof that CUDA-specific performance or
  multi-GPU behavior is verified.

### LLM / Foundation-Model Downloads

LLM-oriented models such as `TimeLLM`, `GPT4TS`, or some foundation-style
workflows can require tokenizer/model downloads or optional tokenizer packages.
If the workflow fails with network/cache/model-card errors, first verify that
the user actually wants the LLM model family; otherwise choose a non-LLM task
model.

## Data Key and Shape Failures

### Missing `X`

Symptoms:

- `The given dataset dictionary doesn't contains X.`
- `The given dataset file doesn't contains X.`

Recovery: ensure every train/validation/test dict or HDF5 file includes `X`
with shape `[n_samples, n_steps, n_features]`.

### Missing `X_ori`

Symptoms:

- Errors requiring `X_ori` during imputation validation or evaluation.

Recovery: include `X_ori` only when the workflow needs the original values for
loss/evaluation. It must have the same shape as `X`.

### Missing `X_pred`

Symptoms:

- Forecasting model training or validation errors that require `X_pred`.

Recovery: split the source sequence into an observed prefix and a future target
segment:

```python
train_set = {"X": train_X[:, :n_steps], "X_pred": train_X[:, n_steps:]}
```

### Missing `y`

Symptoms:

- Classification or representation training complains about labels.
- CLI evaluation for binary classification/anomaly paths complains that `y` is
  absent.

Recovery: save labels under `y` unless a native detector test specifically uses
`anomaly_y` for metrics.

### Wrong Dimensionality

Symptoms:

- `input should have 3 dimensions [n_samples, seq_len, n_features]`.
- `X and X_ori must have matched shape`.
- `X and X_pred must have the same number of samples`.

Recovery: convert 2D continuous series into fixed windows with
`pypots.data.sliding_window()` or `pypots-cli data prepare`, then verify the
HDF5 keys with `pypots-cli data describe --input file.h5`.

## Model API Misuse

### Wrong Result Key

Use the task's documented result key:

| Task | Correct result key |
| --- | --- |
| imputation | `imputation` |
| forecasting | `forecasting` |
| classification | `classification_proba`, `classification` |
| anomaly detection | `anomaly_detection` |
| clustering | `clustering` |
| representation | `representation` |

Do not copy placeholder keys from template code without checking the task base.

### Constructor Parameter Drift

PyPOTS models are task-specific even when the class name is reused. For example,
`TEFN` has different constructor requirements for imputation, forecasting, and
anomaly detection. Use `pypots-cli model describe --name MODEL --task TASK` or
`pypots-cli model config --name MODEL --task TASK` before writing configs.

### Save/Load Confusion

- Rule-based imputers such as `Mean`, `Median`, and `LOCF` do not need normal
  checkpoint saving.
- Stateful neural models can save `.pypots` files and reload through `load()`.
- Rebuild the same architecture before loading a checkpoint through the CLI.

## CLI-Specific Failures

### `pypots-cli train` Fails on Config

Check:

- YAML requires `pyyaml`.
- `task` is one of `imputation`, `classification`, `forecasting`,
  `anomaly_detection`, `clustering`, or `representation`.
- `model.name` is present and exists for the selected task.
- `data.train_set` points to an HDF5 file containing required keys.

### `pypots-cli predict` Fails Loading a Checkpoint

Check:

- `--model_path` points to a saved `.pypots` file.
- `--config` matches the architecture used during training.
- `--task` and `--model` are provided when no config is available.
- `--test_set` points to an HDF5 file containing `X`.

### `pypots-cli data load` Hangs or Fails

This command may download benchmark data or use cache-backed ecosystem packages.
If the user has no network, credentials, or disk budget for the dataset, do not
retry indefinitely; use a local CSV/HDF5 route instead.

### `pypots-cli env`, `dev`, or `doc` Mutates State

These are maintainer-style commands:

- `env` installs dependencies into the current Python environment.
- `dev --cleanup` removes build/test cache directories.
- `doc` can download source archives or remove docs build outputs.

Ask before using them in a user-owned checkout or environment.

## When to Stop and Ask

Stop rather than guessing when:

- A requested model requires unavailable hardware or a missing optional backend
  and no CPU-equivalent model is acceptable.
- A workflow needs external dataset downloads, Hugging Face model downloads, or
  service access that the user has not authorized.
- The user asks for `TimeSeriesAI` service workflows rather than local PyPOTS
  package usage.
- A checkpoint cannot be loaded because the model architecture/config is
  unknown.
