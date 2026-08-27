# Configuration reference

The schema is a YACS `CfgNode` declared in `config.py`. `get_config(args)` clones defaults, recursively merges the selected YAML (and any `BASE` files relative to that YAML), derives paths, freezes the result, and returns it. Unknown YAML keys are therefore rejected by YACS rather than silently becoming arbitrary settings. Keep new keys declared in the schema before using them.

## Minimal mode matrix

| Mode | Required data blocks | Checkpoint | Main action |
|---|---|---|---|
| `train_and_test` | `TRAIN.DATA` and `TEST.DATA`; normal training configs also provide `VALID.DATA` | Usually empty for a new run; trainer saves under the derived model directory | Train, then test |
| `only_test` | `TEST.DATA` | `INFERENCE.MODEL_PATH` must point to a readable model | Test only |
| `unsupervised_method` | `UNSUPERVISED.DATA` | None | Run every token in `UNSUPERVISED.METHOD` |

For every active data block, set a supported `DATASET` string and real `DATA_PATH`. `main.py` uses the presence of dataset and path to decide whether to construct supervised train/test loaders; the unsupervised loader is constructed directly. A blank path is not a safe placeholder for a real run.

## High-value keys

### Mode, data, and cache

- `TOOLBOX_MODE`: exactly `train_and_test`, `only_test`, or `unsupervised_method`.
- `DATASET`: case-sensitive loader selector. The key occurs under `TRAIN.DATA`, `VALID.DATA`, `TEST.DATA`, or `UNSUPERVISED.DATA`, not at the root.
- `DATA_PATH`: raw input path passed to a loader.
- `DO_PREPROCESS`: if `true`, the loader reads raw data and writes its preprocessed cache and file list; if `false`, the loader expects the cache. The README recommends preprocessing once, then turning this off.
- `CACHED_PATH`: root for preprocessed data. The updater appends the split's `EXP_DATA_NAME`.
- `FILE_LIST_PATH`: either a directory (no extension) from which the updater derives a CSV name, or an explicit `.csv`. Other extensions are rejected.
- `EXP_DATA_NAME`: if empty, the updater builds a long deterministic name from preprocessing settings; if non-empty, it uses the supplied name.
- `BEGIN` and `END`: fractional split bounds. `BaseLoader` asserts `BEGIN < END`, `BEGIN >= 0`, and `END <= 1`.
- `FOLD.FOLD_NAME`: when a directory-style file-list path is used, a non-empty fold name is added to the generated CSV filename.

A common split skeleton is:

```yaml
DATA:
  DATASET: PURE
  DATA_PATH: /path/to/raw-data
  CACHED_PATH: /path/to/cache
  FILE_LIST_PATH: /path/to/cache/DataFileLists
  DO_PREPROCESS: false
  BEGIN: 0.0
  END: 1.0
```

Use a real local path in the user's copy. The generated skill deliberately contains no machine-specific research paths.

### Preprocessing identity

The derived experiment name incorporates the split's `PREPROCESS.RESIZE.W`, height, `CHUNK_LENGTH`, joined `DATA_TYPE`, joined `DATA_AUG`, `LABEL_TYPE`, crop-face flag, face backend, large-face settings, dynamic-detection flag and frequency, and median-face-box flag. The unsupervised name also ends in `unsupervised`. This means changing preprocessing settings while retaining an old cache can select a different cache/file-list identity; compare the printed configuration rather than guessing.

The current implementation has an asymmetry worth knowing when diagnosing paths:

- TRAIN and VALID use `PREPROCESS.RESIZE.W` for both the `SizeW` and `SizeH` fragments of the generated name.
- TEST uses `RESIZE.W` for `SizeW` and `RESIZE.H` for `SizeH`.
- UNSUPERVISED uses `RESIZE.W` for both fragments and appends `unsupervised`.

This is source behavior, not a recommendation to hand-recreate names. Leave `EXP_DATA_NAME: ""` unless a stable custom identity is needed, then inspect the printed result.

## Exact derived paths

The updater captures the schema defaults before merging the YAML. If a split's `FILE_LIST_PATH` is still the default, it first resets it to `<split CACHED_PATH>/DataFileLists`. It then appends the derived experiment name to `CACHED_PATH`:

```text
<configured CACHED_PATH>/<EXP_DATA_NAME>
```

For a directory-style file-list path, the final CSV is:

```text
<configured-or-default FILE_LIST_PATH>/<EXP_DATA_NAME>_<BEGIN>_<END>[_<FOLD_NAME>].csv
```

If `FILE_LIST_PATH` is already a `.csv`, it remains that exact path. A non-CSV extension raises a split-specific error. An explicit `.csv` combined with `DO_PREPROCESS: true` raises an error because the code treats that as an existing user file; set preprocessing false or use a directory path/remove the existing CSV as appropriate. Do not delete files without confirming they can be regenerated.

The updater creates these output identities after the data paths:

```text
MODEL.MODEL_DIR = <LOG.PATH>/<TRAIN EXP_DATA_NAME>/PreTrainedModels
TEST.OUTPUT_SAVE_DIR = <LOG.PATH>/<TEST EXP_DATA_NAME>/saved_test_outputs
UNSUPERVISED.OUTPUT_SAVE_DIR = <LOG.PATH>/<UNSUPERVISED EXP_DATA_NAME>/saved_outputs
```

`MODEL.MODEL_DIR` defaults to `PreTrainedModels` before it is joined to `LOG.PATH`. `LOG.PATH` defaults to `runs/exp`, so all relative outputs are relative to the process working directory. The root `.gitignore` ignores `PreprocessedData`, `PreTrainedModels`, `runs`, `preprocessed`, `preprocess`, and several output/debug patterns; an output that is not visible in `git status` may still exist on disk.

## Checkpoints and device

- `INFERENCE.MODEL_PATH` is the checkpoint path used by supervised inference trainers. In `only_test`, use an existing file and keep its model/config pairing compatible.
- `MODEL.RESUME` is present in the YACS schema as a resume setting, but the inspected entry point does not use it to replace `INFERENCE.MODEL_PATH`; follow the selected trainer's documented behavior before relying on it.
- `DEVICE` defaults to `cuda:0` and is passed into dataset loaders. Choose a device string supported by the installed PyTorch build and hardware; use `cpu` deliberately when CUDA is unavailable rather than assuming automatic fallback.
- `NUM_OF_GPU_TRAIN`, `TRAIN.BATCH_SIZE`, `INFERENCE.BATCH_SIZE`, `TRAIN.EPOCHS`, `TRAIN.LR`, and `LOG.PATH` are YAML settings. The command-line `--lr` and `--model_file_name` flags are registered but are not applied by the current config updater; put values in YAML.

## Validation and split rules

- With `train_and_test` and `TEST.USE_LAST_EPOCH: true`, `main.py` prints that validation is not required and passes `valid: None` to the DataLoader dictionary. The config still needs a supported `VALID.DATA.DATASET` to pass the loader-selector branch; a blank default is not accepted.
- With `TEST.USE_LAST_EPOCH: false`, `config.py` requires a validation dataset and expands validation cache/file-list paths. Supply `VALID.DATA.DATASET`, path, and preprocessing settings. `main.py` then constructs the validation loader when dataset, path, and the false flag are all present.
- `TEST.USE_LAST_EPOCH` defaults to `true`; inference configs commonly keep it true when no validation selection is needed, while some model-release configs use false and provide a validation block.
- `DATA_FORMAT`, `FS`, `PREPROCESS.DATA_TYPE`, `PREPROCESS.LABEL_TYPE`, resize, chunk, and face-crop settings must match the dataset/model expectation. This sub-skill only routes those choices; algorithm-specific semantics belong to data-preparation and model skills.
- `UNSUPERVISED.DATA.PREPROCESS.USE_PSUEDO_PPG_LABEL: true` is rejected by `config.py` in unsupervised mode.

## Safe YAML workflow

1. Copy the nearest existing train or inference config, not a private path from a README snippet.
2. Change `TOOLBOX_MODE`, active dataset blocks, raw/cache paths, `DO_PREPROCESS`, split bounds, model/checkpoint, device, and log path.
3. Run the bundled validator. It checks YAML shape, mode-specific blocks, required keys, split bounds, file-list extension, and optional local paths without writing.
4. For first preprocessing, prefer a directory-style `FILE_LIST_PATH`; after it succeeds, inspect the generated CSV and printed derived cache path, then set `DO_PREPROCESS: false` for repeat runs.
5. Keep `EXP_DATA_NAME` empty while iterating unless you intentionally need a stable custom namespace. Separate experiments with distinct `LOG.PATH` values to avoid output collisions.

## Extension route

Dataset: add the loader and its required preprocessing/video/waveform methods, declare new schema keys in `config.py`, add YAML, and add exact dataset branches at each intended mode's loader-selection site in `main.py`.

Supervised model: add the model and trainer contract, add the exact case-sensitive model branch to both `train_and_test` and `test`, and add YAML fields.

Unsupervised method: add the method implementation, add its exact token branch in `unsupervised_method_inference`, and add the token to a YAML list. Test unknown and empty tokens deliberately. Details of each implementation belong to the routed skills, not here.

## Evidence

- `README.md` setup, examples, YAML, and extension sections (lines 307-488 in the inspected revision).
- `requirements.txt` pinned dependency list.
- `setup.sh` Conda/uv commands and local Mamba build step.
- `config.py` schema and `update_config` path/mode validation.
- Representative `configs/train_configs/PURE_PURE_UBFC-rPPG_TSCAN_BASIC.yaml`, `configs/train_configs/SCAMPS_SCAMPS_PURE_TSCAN_BASIC.yaml`, `configs/infer_configs/PURE_UBFC-rPPG_TSCAN_BASIC.yaml`, and `configs/infer_configs/PURE_UNSUPERVISED.yaml`.
- `main.py` parser and mode/dataset/model/method dispatch.
- Root `.gitignore` output/path cautions.
