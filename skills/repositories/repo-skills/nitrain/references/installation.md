# Installation and dependency matrix

## Purpose

Read this before installing or refreshing Nitrain support. The repository snapshot exposes several workflows that do not share one tiny dependency set, so future agents should install only the packages needed for the selected workflow family.

## What the repo metadata does and does not cover

- `pyproject.toml` declares the base package name `nitrain`, version `0.3.1`, Python `^3.9`, and core dependencies such as `antspyx`, `parse`, `pydot`, and `tqdm`.
- The source imports additional runtime packages that are not declared in `pyproject.toml` alone: `pandas`, `google-cloud-storage`, `google-auth`, `antspynet`, `tensorflow`, `tf-keras`, `torch`, and `monai`.
- There are no optional extras in the packaging metadata, so workflow-specific dependencies must be installed explicitly.

## Verified CPU stack for this snapshot

The following CPU-only combination imported cleanly and passed `pip check` in the inspection environment:

| Package | Verified version |
| --- | --- |
| `nitrain` | `0.3.1` |
| `antspyx` | `0.5.4` |
| `antspynet` | `0.2.9` |
| `tensorflow` | `2.17.0` |
| `tf-keras` | `2.17.0` |
| `torch` | `2.8.0+cpu` |
| `monai` | `1.6.0` |
| `google-cloud-storage` | `2.14.0` |
| `google-api-core` | `2.15.0` |
| `googleapis-common-protos` | `1.62.0` |
| `proto-plus` | `1.23.0` |

## Recommended install layers

### 1) Base data and reader workflows

Use this for `Dataset`, `ImageReader`, `ColumnReader`, `FolderNameReader`, `MemoryReader`, `ComposeReader`, `fetch_data`, and `GoogleCloudDataset`:

```bash
pip install nitrain==0.3.1 pandas google-cloud-storage==2.14.0 google-auth antspyx==0.5.4
```

### 2) Keras/TensorFlow model workflows

Add this when you need `fetch_architecture`, `list_architectures`, `Trainer`, `Loader.to_keras`, `Predictor`, or any Keras-backed workflow:

```bash
pip install antspynet==0.2.9 tensorflow==2.17.0 tf-keras==2.17.0
```

### 3) Torch training workflows

Add this when you need `nitrain.trainers.TorchTrainer` or MONAI-based smoke checks:

```bash
pip install --index-url https://download.pytorch.org/whl/cpu torch==2.8.0+cpu
pip install --no-deps monai==1.6.0
```

### 4) Optional network/cloud workflows

- `fetch_data('openneuro/...')` needs `datalad` plus `git-annex` and network access.
- `GoogleCloudDataset` needs a service-account JSON or equivalent credentials with access to the target bucket.

These paths are useful to document, but they are not required for the default CPU smoke path.

## Why the pins matter

Two compatibility traps showed up during inspection:

- The newest `antspynet` release on PyPI expects a newer `antspyx` than the current `nitrain` metadata allows. The safe snapshot pair was `antspynet==0.2.9` with `antspyx==0.5.4`.
- `monai` wants a recent `torch`; the CPU wheel `torch==2.8.0+cpu` satisfied the verified path.

If a fresh install pulls a newer stack and `pip check` fails, align to the verified pins above before assuming the package is broken.

## Verification step after install

First run `python -m pip check` in the target environment, then run the bundled
smoke helper after installation:

```bash
python scripts/check_install.py --mode all
```

Use `--mode base`, `--mode datasets`, `--mode preprocess`, `--mode models`, or `--mode predictor` when you only need one workflow family.
