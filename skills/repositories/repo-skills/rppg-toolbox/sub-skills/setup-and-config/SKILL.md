---
name: setup-and-config
description: "Install, configure, run, diagnose, and safely extend the
  rPPG-Toolbox command-line pipeline."
disable-model-invocation: true
metadata: { disco-role: operating }
license: NOASSERTION
---

# Setup and configuration

Use this sub-skill when a Researcher needs to prepare an rPPG-Toolbox checkout, choose a YAML experiment, invoke `main.py`, explain a missing cache or checkpoint, or add a dispatch route. It is an operating guide, not a replacement for the dataset-loader, model, unsupervised-method, or evaluation implementations.

## Operating contract

- Work from a repository checkout (normally its root) and use a user-owned environment. The program imports `config`, `dataset`, `neural_methods`, and `unsupervised_methods`; if invoked elsewhere, provide an explicit `PYTHONPATH` and make every relative config/data/checkpoint path intentional.
- Treat the repository's `setup.sh` as evidence, not as a harmless probe: its conda route removes and recreates an environment, and its uv route removes `.venv`. Confirm before running either route.
- Select an existing config under `configs/infer_configs/` for inference or `configs/train_configs/` for training. Replace all raw-data, cache, file-list, and checkpoint placeholders before a real run.
- Validate a YAML without importing the research pipeline with the bundled read-only helper:
  `python scripts/validate_config.py path/to/config.yaml` from this sub-skill directory.
  Add `--check-paths` to report missing user paths; the helper never downloads, creates, or deletes files.
- Run only after checking the mode, dataset paths, `DO_PREPROCESS`, `USE_LAST_EPOCH`, `INFERENCE.MODEL_PATH`, `DEVICE`, and `LOG.PATH`. See [the CLI reference](references/cli-reference.md), [configuration reference](references/configuration.md), and [troubleshooting](references/troubleshooting.md).

## Quick routing

1. **Install**: use an isolated Conda or uv environment. The source-era setup targets Python 3.8, installs PyTorch 2.1.2 with the CUDA 12.1 wheel route, then installs the pinned requirements and the local Mamba extension. It is not a Python distribution: there is no `setup.py` or `pyproject.toml` at the repository root.
2. **Choose a mode**: `train_and_test` trains and then tests; `only_test` loads `INFERENCE.MODEL_PATH` and tests; `unsupervised_method` builds one unsupervised loader and runs every method in `UNSUPERVISED.METHOD`.
3. **Prepare data**: on the first run set the applicable `DO_PREPROCESS: true`; after a successful preprocess, set it to `false` and retain the derived cache and CSV file list. A false flag with no cache fails in `BaseLoader`; a missing list may be generated retroactively when the cache exists.
4. **Run**: from the checkout root, use `python main.py --config_file path/to/config.yaml`. The config path is the only CLI option consumed by `config.update_config`; use YAML for operational settings.
5. **Diagnose before rerunning**: read the printed merged configuration, then compare the expected derived paths with the actual cache, CSV, model, and log paths. Do not delete caches or checkpoints as a first response.

## Required decisions by mode

### `train_and_test`

Set `TRAIN.DATA.DATASET` and `TRAIN.DATA.DATA_PATH` for the training loader, and `TEST.DATA.DATASET` and `TEST.DATA.DATA_PATH` for testing. Set `TRAIN.MODEL_FILE_NAME`, model settings, and training parameters. The main dispatcher constructs a validation-loader class even when `TEST.USE_LAST_EPOCH: true`; keep `VALID.DATA.DATASET` set to a supported dataset name in a normal training config. With `USE_LAST_EPOCH: true`, the validation `DataLoader` is `None` and testing uses the last epoch; with `false`, supply a real validation dataset/path and its cache.

### `only_test`

Set `TEST.DATA.DATASET`, `TEST.DATA.DATA_PATH`, and a readable `INFERENCE.MODEL_PATH`; use an inference config as the starting point. The selected trainer checks the model path and raises an inference-model-path error if it is absent. A false `TEST.USE_LAST_EPOCH` also causes the config updater to require validation settings, even though `main.py` does not build a validation loader for `only_test`.

### `unsupervised_method`

Set `UNSUPERVISED.DATA.DATASET`, `UNSUPERVISED.DATA.DATA_PATH`, preprocessing settings, and a non-empty `UNSUPERVISED.METHOD` list. The current dispatch tokens are `POS`, `CHROM`, `ICA`, `GREEN`, `LGI`, `PBV`, and `OMIT`. Pseudo PPG labels are rejected for this mode. There is no supervised checkpoint requirement.

## Configuration discipline

YACS starts from the schema in `config.py`, recursively merges `BASE` files relative to the config file, derives experiment paths, and freezes the result. Keep new keys declared in the schema before using them in YAML. Use `DATA_PATH` for raw input, `CACHED_PATH` for preprocessed data, and `FILE_LIST_PATH` for a directory or an explicit `.csv`; do not confuse a raw path with a cache path. `DO_PREPROCESS` is per data split. `DEVICE` defaults to `cuda:0`; `LOG.PATH` defaults to `runs/exp`. The full path formula, key table, mode matrix, and checkpoint cautions are in [configuration.md](references/configuration.md).

## Fast diagnostic decision tree

- If Python cannot import a dependency, stop at environment setup; do not debug YAML yet.
- If YAML parsing or schema merge fails, run the bundled validator and compare nesting/case with a nearby config.
- If the printed derived cache is absent, decide whether this is a first preprocess or a path/identity mismatch; never fake an empty cache.
- If a CSV is absent, check whether the configured path is a directory (allowing generation) or an explicit file (which must already be valid when preprocessing is off).
- If a checkpoint is absent, inspect `INFERENCE.MODEL_PATH` for `only_test`; `MODEL.MODEL_DIR` is a training output directory, not a substitute.
- If dispatch rejects a name, compare its exact spelling with the mode-specific branch table before editing source.
- If outputs cannot be found, resolve `LOG.PATH` relative to the current working directory and remember ignored paths are still real files.

When handing off a run, record the config path, mode, device, active dataset/path for each split, `DO_PREPROCESS`, printed derived cache/file-list paths, checkpoint path (if any), and the first error. This makes a retry reproducible without embedding private filesystem paths in the skill.

## Stop conditions

- Do not launch `setup.sh` until the user confirms that environment removal/recreation is acceptable.
- Do not set `DO_PREPROCESS: false` merely to skip a failure; first prove the matching cache exists.
- Do not use `MODEL.MODEL_DIR` as an inference checkpoint or assume a release checkpoint matches a new preprocessing identity.
- Do not add a dataset/model/method token only to YAML; the explicit dispatcher branch is part of the extension contract.
- Do not resolve a missing output by searching the source tree; inspect `LOG.PATH` and the printed derived output directory.

## Safe extension route

- **Dataset**: implement the dataset loader's preprocessing, video-reading, and waveform-reading contract; add any schema keys; create YAML; then add the dataset class branch for every intended `TRAIN`, `VALID`, `TEST`, and/or `UNSUPERVISED` dispatch site in `main.py`. Keep loader algorithms in the data-preparation skill.
- **Supervised model**: add a model and trainer with constructor, `train`, `valid`, `test`, and save behavior; add the exact `MODEL.NAME` branch to both `train_and_test` and `test`; add a config. Keep architecture details in supervised-models.
- **Unsupervised method**: add the method implementation, add its exact token branch in `unsupervised_method_inference`, add a YAML token, and explicitly reject empty or misspelled tokens. Keep formulas in unsupervised-methods.

After an extension, smoke-test dispatch with a minimal valid configuration or a mocked loader boundary before using real data. Do not silently fall back to another dataset/model/method: the source dispatcher raises `ValueError` for unsupported names.

## Boundaries and evidence

This sub-skill intentionally does not explain loader algorithms, model architecture tables, unsupervised formulas, or plotting implementation; route those questions to `data-preparation`, `supervised-models`, `unsupervised-methods`, and `evaluation-and-visualization`. Its facts were distilled from the setup/configuration/extension sections of `README.md`, `requirements.txt`, `setup.sh`, the full `config.py`, representative train/infer YAMLs, `main.py`, `neural_methods/trainer/BaseTrainer.py`, `dataset/data_loader/BaseLoader.py`, and the root `.gitignore`. Source line ranges and known quirks are recorded in the bundled references; no source checkout path is required at runtime.
