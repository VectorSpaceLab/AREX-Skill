# Troubleshooting

## Missing `dataset_path`

**Symptoms**
- Dataset constructors raise a `KeyError` or `TypeError` about `dataset_path`.

**Likely causes**
- The dataset constructor was called without a root path.
- A config file or command-line override did not propagate the path.

**Recovery**
- Confirm the root path before constructing the dataset.
- Re-check the config merge order if you are using config-driven training.

## Empty split

**Symptoms**
- `len(split) == 0`
- Training or visualization exits early because the split has no data.

**Likely causes**
- The split directory is empty.
- The split name is misspelled.
- The dataset is pointed at the wrong root.

**Recovery**
- Verify the split names and directory contents with
  `scripts/check_dataset_layout.py`.
- Make sure the files are in the expected train/val/test directories.

## Malformed `.npy` file

**Symptoms**
- Array load failures.
- Shape mismatches when a custom dataset is inspected.

**Likely causes**
- A `.npy` file is not 2D.
- The file does not include the expected label column for train/val.
- A file is missing point columns or has ragged contents.

**Recovery**
- Re-save the file as a 2D NumPy array.
- Validate the split with the bundled layout checker.
- Check that train/val and test follow the correct column conventions.

## Label mismatch

**Symptoms**
- The labels in a custom dataset do not line up with expected classes.
- Saved predictions or training metrics look nonsensical.

**Likely causes**
- The dataset's label IDs do not match the model's label map.
- A custom `label_to_names` mapping was not documented.

**Recovery**
- Document the mapping in the dataset reference.
- Verify that the class IDs used by the model match the dataset labels.

## Dataset SDK or download dependency missing

**Symptoms**
- Preprocessing or conversion scripts mention dataset-specific SDKs.
- A workflow needs an external dataset devkit or a large download.

**Likely causes**
- Some upstream datasets need vendor SDKs or private/raw source files.

**Recovery**
- Treat those workflows as optional and reference-only unless the user
  specifically provides the required SDK or data.
- Use the bundled layout checker for local fixture validation instead of
  starting the expensive conversion path immediately.

## Cache or path confusion

**Symptoms**
- Split loading works once and fails after moving the dataset.
- Cached results appear stale.

**Likely causes**
- Dataset paths changed after cache creation.
- A dataset-specific cache folder was reused with different inputs.

**Recovery**
- Clear or relocate the cache only after the underlying dataset path is
  stable.
- Prefer a fresh validation run for a moved dataset root.
