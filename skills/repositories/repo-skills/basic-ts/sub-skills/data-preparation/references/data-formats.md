# BasicTS Data Formats

## Purpose

Read this reference when you need to inspect or create a BasicTS dataset folder, or when you want to validate that an existing folder matches the expected schema.

## Forecasting dataset layout

Used by `BasicTSForecastingDataset`.

### Files

```text
<dataset-root>/
  train_data.npy
  val_data.npy
  test_data.npy
  train_timestamps.npy        # optional, only when timestamps are used
  val_timestamps.npy          # optional
  test_timestamps.npy         # optional
  meta.json                   # recommended
```

### Array shapes

- `*_data.npy`: typically a 2D array shaped `[num_time_steps, num_features]`
- `*_timestamps.npy`: typically a 2D array shaped `[num_time_steps, num_timestamp_features]`

The smoke fixture used in this repository follows the ETTh-style shape reported in `tests/smoke_test/datasets/ETTh1_mini/meta.json`:

- data shape: `[720, 7]`
- timestamp shape: `[720, 4]`

### Runtime behavior

- `__getitem__` returns sliding windows with `inputs` and `targets`.
- `use_timestamps=True` requires the timestamp files to exist.
- `data_file_path` can point directly to the dataset folder.

## Imputation dataset layout

Used by `BasicTSImputationDataset`.

### Files

```text
<dataset-root>/
  train_data.npy
  val_data.npy
  test_data.npy
  train_timestamps.npy        # optional
  val_timestamps.npy          # optional
  test_timestamps.npy         # optional
  meta.json                   # recommended
```

### Notes

- The file layout is the same family as forecasting, but the taskflow creates the reconstruction target at runtime.
- The data arrays are treated as the observed input sequence.
- `mask_ratio` is not a file-layout setting; it is a training-time config setting.

## UEA classification layout

Used by `UEADataset`.

### Files

```text
<dataset-root>/
  train_inputs.npy
  train_labels.npy
  test_inputs.npy
  test_labels.npy
  desc.json                    # recommended
```

### Shapes

The processed mini fixture in `tests/smoke_test/datasets/UEA/ArticularyWordRecognition_mini/meta.json` reports:

- `seq_len: 144`
- `num_nodes: 9`
- `num_features: 1`
- `shape: [num_samples, seq_len, num_nodes, num_features]`

`UEADataset` squeezes the last axis when the stored array is 4D with a singleton feature dimension.

### Notes

- The validation split is not stored separately; the dataset implementation maps the BasicTS validation mode to test data.
- Labels are stored as integer class ids after preprocessing.

## BLAST layout

Used by `BLAST`.

### Files

```text
<dataset-root>/
  train/
    shape.npy
    data.dat
  val/
    shape.npy
    data.dat
  test/
    shape.npy
    data.dat
```

### Notes

- `shape.npy` stores the memmap shape used to open `data.dat`.
- The BLAST merge script in `scripts/data_preparation/BLAST/merge_data.py` merges per-shard arrays into `data.dat` and writes the final `shape.npy`.
- The dataset code reads the `mode` subdirectory directly.
- This layout is different from the forecasting/imputation `.npy` split layout.

## Metadata fields that are useful but not strictly required

### Forecasting / imputation `meta.json`

Useful fields seen in the mini fixture:

- `name`
- `shape`
- `timestamps_shape`
- `regular_settings`

### UEA `desc.json`

Useful fields seen in the mini fixture:

- `name`
- `num_classes`
- `class_names`
- `seq_len`
- `num_nodes`
- `num_features`
- `missing`
- `filling_missing`
- `norm_each_channel`

## Raw conversion scripts

The repository includes dataset-preparation scripts under `scripts/data_preparation/`.

- Many dataset-specific scripts read raw CSV or `.ts` inputs and write the layouts above.
- `run.sh` chains many dataset-specific converters and is not bundled as a safe runtime helper because it assumes raw data and can write large outputs.
- `merge_data.py` is BLAST-specific and destructive if its cache-cleaning flag is used, so the reusable knowledge is the layout and merge behavior, not the script verbatim.

## Practical validation checklist

1. Confirm the folder name and split files.
2. Confirm whether timestamps are required.
3. Confirm whether the task is forecasting, imputation, classification, or BLAST.
4. Check the first dimension of every split file.
5. Check label counts for classification.
6. Check `shape.npy` / `data.dat` consistency for BLAST.

## Evidence sources

- `docs/dataset_design.md`
- `src/basicts/data/*.py`
- `scripts/data_preparation/*.py`
- `tests/smoke_test/datasets/*/meta.json`
- `tests/smoke_test/datasets/UEA/*/meta.json`
