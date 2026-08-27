# Troubleshooting

Use the smallest diagnostic that distinguishes a bad environment, a bad YAML, a missing derived artifact, or an unsupported dispatch token. These checks are read-only unless the user explicitly chooses a setup command.

## Installation and import failures

**`ModuleNotFoundError` for yacs, torch, OpenCV, Mamba, or another requirement**

- Confirm the active interpreter: `python -c "import sys; print(sys.executable); print(sys.version)"`.
- Check the environment against `requirements.txt`; the repository targets a Python 3.8-era stack and `setup.sh` installs PyTorch 2.1.2/torchvision 0.16.2/torchaudio 2.1.2 from the CUDA 12.1 wheel index before the pinned requirements.
- The root is not packaged as a normal installable distribution: no root `setup.py` or `pyproject.toml` was present. Run from the checkout root or expose it with an explicit `PYTHONPATH`; do not infer that `pip install .` is supported.
- `setup.sh` separately enters `tools/mamba` and installs its local `setup.py`. That is an extension build step, not evidence that the root can be installed with `pip install .`.

**Mamba build/compiler failure**

The README calls out compiler-related uv failures around Mamba. Check `which clang++` and install the appropriate system compiler only with the user's approval. The setup script's Conda route removes/recreates the named environment; the uv route removes `.venv`, so never run either blindly in an environment containing unrelated work.

**Windows or unsupported host**

The README specifically suggests WSL and following the setup steps independently. Do not promise native compatibility from the inspected source.

## CLI and YAML failures

**Config file not found or imports fail when launched**

Use an explicit path from the checkout root:

```bash
python main.py --config_file configs/infer_configs/PURE_UBFC-rPPG_TSCAN_BASIC.yaml
```

If invoking from another directory, set `PYTHONPATH` to the checkout and use an absolute config path. Do not copy an absolute path from a sample config; the repository contains machine-specific examples that must be replaced.

**Unknown YAML key / merge error**

YACS only accepts keys declared in `config.py`. Check spelling, nesting, and capitalization (`DATASET`, `DATA_PATH`, `DO_PREPROCESS`, `FILE_LIST_PATH`, `USE_LAST_EPOCH`, `MODEL_PATH`, and `DEVICE` are not interchangeable). Start from the closest existing config and run `validate_config.py` before the full program.

**`TOOLBOX_MODE only supports...` or unsupported mode**

Use exactly one of `train_and_test`, `only_test`, or `unsupervised_method`. The mode is read from YAML, not a CLI flag. Do not use `only_train`; some old comments mention it, but the dispatcher does not implement it.

**Unsupported dataset or model**

Names are case-sensitive and selected by explicit `if/elif` branches. Confirm that the name belongs to the mode's dispatch set in [cli-reference.md](cli-reference.md). A dataset available in supervised train/test may not be available in the unsupervised branch. Add a branch for a new route rather than silently renaming it to an existing loader.

**Unsupported unsupervised method / empty method list**

Use a non-empty list containing only `POS`, `CHROM`, `ICA`, `GREEN`, `LGI`, `PBV`, and `OMIT` in the inspected revision. Empty lists and misspelled tokens are explicit errors.

## Cache and file-list failures

**`Please set DO_PREPROCESS to True. Preprocessed directory does not exist!`**

This means the active split has `DO_PREPROCESS: false` but its derived `CACHED_PATH` is missing. Choose one of these deliberate fixes:

1. Point `CACHED_PATH` and `FILE_LIST_PATH` at the cache created by the same preprocessing identity; or
2. Set `DO_PREPROCESS: true`, verify the raw `DATA_PATH`, and run preprocessing once.

Do not merely create an empty directory: the loader needs valid preprocessed artifacts.

**`File list does not exist... generating now...`**

With preprocessing disabled and a cache present, `BaseLoader` attempts to build a list retroactively from the raw data path. If this is unexpected, inspect the printed `FILE_LIST_PATH`, verify the raw path, and confirm that the cache belongs to the same dataset/split and preprocessing settings.

**Split-specific `FILE_LIST_PATH` error**

- No extension: interpreted as a directory and expanded to `<EXP_DATA_NAME>_<BEGIN>_<END>[_<FOLD_NAME>].csv`.
- `.csv`: accepted as an explicit file-list path.
- Any other extension: rejected.
- Explicit `.csv` plus `DO_PREPROCESS: true`: rejected by `config.py`; use a directory-style path for generated lists or turn preprocessing off after the list exists.

The updater appends `EXP_DATA_NAME` to `CACHED_PATH`, and relative paths resolve under the process working directory. Compare the printed frozen config with disk rather than reconstructing a guessed path. Remember that train/valid/unsupervised name generation uses width for both size fragments, while test uses width and height separately.

**Preprocessing repeats unexpectedly or reads the wrong cache**

`EXP_DATA_NAME` is derived from preprocessing settings when empty. A changed resize, chunk length, data type, augmentation, label type, face backend, crop/detection setting, or split identity changes the derived namespace. Preserve the old cache, inspect the new printed name, and either restore matching YAML values or intentionally preprocess into a new namespace.

## Validation, checkpoint, and device failures

**`VALIDATION dataset is not provided despite USE_LAST_EPOCH being False!`**

Set `TEST.USE_LAST_EPOCH: true` if validation selection is intentionally not used, or provide `VALID.DATA.DATASET` and its complete path/cache/preprocess block when it is false. In `train_and_test`, the main loader selector still expects a supported validation dataset name even when the validation DataLoader is skipped for last-epoch testing; use a normal supported validation block rather than leaving the default blank.

**Checkpoint path error during `only_test`**

Check `INFERENCE.MODEL_PATH`, not `MODEL.MODEL_DIR`. It must point to the actual checkpoint file and be compatible with `MODEL.NAME` and the model's preprocessing shape. Release examples use repository-relative paths, but user configs should use a path that exists in their checkout. If the file is present but state-dict loading fails, route the architecture/preprocessing mismatch to `supervised-models`.

**CUDA/device error**

`DEVICE` defaults to `cuda:0`; there is no inspected auto-selection policy. Check `python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"`, then choose a device supported by that installation (for example, `cpu` for a CPU-only diagnostic). A CUDA 12.1 wheel does not make a missing/incompatible driver available.

**Output appears missing**

Inspect `LOG.PATH` and the derived `TEST.OUTPUT_SAVE_DIR`, `UNSUPERVISED.OUTPUT_SAVE_DIR`, or `MODEL.MODEL_DIR` printed in the configuration. Relative output paths are relative to the current working directory. The root `.gitignore` ignores common cache/model/log/output directories, so git status is not an existence check.

## Extension failures

**New dataset never reaches the loader**

Add the loader, schema/YAML settings, and the exact dataset branch for each mode intended. A branch added only to training does not make the dataset available to test or unsupervised inference.

**New model works in training but fails in inference**

The current source duplicates model dispatch in `train_and_test` and `test`. Add and smoke-test both exact-name branches, then provide the model-specific config node and checkpoint route.

**New unsupervised method is ignored or rejected**

Add its implementation, add its exact token branch in `unsupervised_method_inference`, and include the same token in YAML. Keep token spelling and case stable. Do not put formula or signal-processing details in this setup sub-skill.

## Evidence

Failure wording and path behavior are from `config.py`, `main.py`, and `dataset/data_loader/BaseLoader.py`; install/compiler caveats are from `README.md`, `requirements.txt`, and `setup.sh`; ignored output names are from the root `.gitignore`.
