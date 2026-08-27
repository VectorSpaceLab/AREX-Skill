# Troubleshooting

## Purpose

Use this reference when a dataset folder fails validation or BasicTS cannot load it.

## Common failures

### 1) Missing forecasting split files

**Symptoms**
- `FileNotFoundError` for `train_data.npy`, `val_data.npy`, or `test_data.npy`
- `BasicTSForecastingDataset` cannot open the folder

**Likely cause**
- the folder path is wrong
- the dataset was converted with a different naming convention

**Recovery**
- Check the exact dataset root and split filenames.
- If you are validating a temporary fixture, rerun the tiny fixture helper.

### 2) Missing timestamp arrays

**Symptoms**
- the model or dataset fails only when `use_timestamps=True`
- missing `*_timestamps.npy` files

**Likely cause**
- the fixture was created without timestamp arrays
- the config enables timestamps but the dataset does not provide them

**Recovery**
- Add the timestamp arrays.
- Or set `use_timestamps=False` when the model does not need them.

### 3) Forecasting and imputation layouts are confused

**Symptoms**
- a run expects `targets` but the dataset only supplies inputs
- a validation helper complains about the wrong file family

**Likely cause**
- the wrong task family was selected

**Recovery**
- Forecasting and imputation share the split-file family, but imputation creates targets at runtime.
- Re-check whether the model is forecasting or masked reconstruction.

### 4) UEA labels do not match the inputs

**Symptoms**
- label-count mismatch
- shape mismatch between `*_inputs.npy` and `*_labels.npy`

**Likely cause**
- preprocessing converted one file but not the other
- the labels were not remapped into class ids consistently

**Recovery**
- Confirm that each split has a matching inputs/labels pair.
- Check the processed `desc.json` for the number of classes and sequence shape.

### 5) BLAST memmap shape mismatch

**Symptoms**
- NumPy memmap errors
- `shape.npy` and `data.dat` disagree
- the merge step appears to produce the wrong final shape

**Likely cause**
- shard counts do not add up
- the merge script was interrupted
- the wrong mode directory was validated

**Recovery**
- Recompute the expected shape from `shape.npy`.
- Regenerate the merged BLAST files if the cache is partial.
- Treat BLAST separately from the forecasting split-file layouts.

### 6) Graph-model adjacency confusion

**Symptoms**
- a user expects graph data but the dataset folder has no `adj_mx.pkl`
- validation passes but the graph model still fails later

**Likely cause**
- graph connectivity is an optional extra, not part of every dataset family

**Recovery**
- Check whether the selected model actually requires graph adjacency.
- If it does, verify the optional adjacency artifact separately.

## What to check first

1. The folder name.
2. The split filenames.
3. Whether timestamps are required.
4. Whether the task is forecasting, imputation, classification, or BLAST.
5. The first dimension of the saved arrays.

## When to switch sub-skills

- If the dataset is valid but the launch still fails, go to `training-evaluation`.
- If the task needs masks or custom preprocessing, go to `pipeline-extension`.
- If the model expects a different input shape or extra fields, go to `model-development`.
