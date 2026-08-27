# Troubleshooting

## Hugging Face download and network failures

### Symptoms
- `DatasetNotFoundError`
- the CLI says the dataset could not be found or network access is unavailable
- `FederatedDataset` stalls or fails while loading the Hub dataset

### Likely cause
- The dataset identifier is wrong.
- The machine has no Hugging Face network access.
- The dataset is remote and has not been cached locally.

### What to do
- Re-check the dataset name and subset exactly as written on the Hub.
- Confirm basic network access before retrying.
- For offline work, switch to local files or a cached `datasets.Dataset` and assign the partitioner directly.

## Invalid split names or split selection

### Symptoms
- `The given split: '...' is not present in the dataset's splits: ...`
- `Please set the split argument`

### Likely cause
- The split name does not exist in the loaded dataset.
- More than one partitioner was configured, so `load_partition` needs an explicit `split=`.

### What to do
- Use the exact split names from the Hub dataset or from your `Divider`/`Merger` output.
- Pass `split=` whenever there is more than one partitioner.
- Remember that `load_dataset("imagefolder", ...)` and `load_dataset("audiofolder", ...)` return a `DatasetDict`; select a split before partitioning.

## Local-data shape and cast mistakes

### Symptoms
- image or audio paths remain plain strings
- partitioning works on one column but not the expected media column
- a partitioner refuses the assigned dataset

### Likely cause
- The local CSV/JSON column was not cast to `Image()` or `Audio()`.
- A `DatasetDict` was assigned where a `Dataset` was expected.

### What to do
- Cast the column before partitioning:
  - `dataset = dataset.cast_column("path", Image())`
  - `dataset = dataset.cast_column("path", Audio())`
- If you loaded from a directory, select the split first.
- Assign the partitioner a single `datasets.Dataset`, not the whole `DatasetDict`.

## Partition-count and class-constraint errors

### Symptoms
- `The specified num_classes_per_partition ... is greater than the number of unique classes ...`
- a label-specific partitioner fails because one label does not have enough samples
- a class-constrained partition looks too sparse or missing

### Likely cause
- `PathologicalPartitioner` was configured with too many classes per partition.
- There are not enough rows for the requested number of partitions and class assignment mode.

### What to do
- Lower `num_classes_per_partition`.
- Lower `num_partitions` if each label is too small.
- Try `class_assignment_mode="deterministic"` or a different dataset.
- For tiny sanity checks, start with one class per partition and a tiny balanced dataset.

## Missing vision or audio extras

### Symptoms
- imports fail for image or audio helpers
- `PIL`, `torchcodec`, or similar packages are missing
- vision or audio notebook cells fail at install time

### Likely cause
- The optional extras were not installed.

### What to do
- Install the right extra for the workload:
  - `python -m pip install "flwr-datasets[vision]"`
  - `python -m pip install "flwr-datasets[audio]"`
- Use the base package only for non-media workloads.

## Visualization dependency issues

### Symptoms
- plotting imports fail
- Matplotlib or Seaborn errors appear in a notebook or headless environment

### Likely cause
- `matplotlib`, `seaborn`, or `pandas` is missing or misconfigured.

### What to do
- Reinstall the base `flwr-datasets` dependencies.
- In headless environments, choose a non-interactive Matplotlib backend before plotting.
- Use the helper script or a notebook cell that imports the plotting functions before debugging plot code.

## Example wiring failures

### Symptoms
- the example module import path fails
- `serverapp` or `clientapp` cannot be imported from `tool.flwr.app.components`
- the example uses the wrong dependency family for its model stack

### Likely cause
- The `pyproject.toml` component path is stale or misspelled.
- The runtime dependencies do not match the example family.

### What to do
- Verify the import strings in `[tool.flwr.app.components]`.
- Compare the dependency list with the example family.
- Use `scripts/catalog_examples.py` to see the current catalog and wiring pattern.

## CLI create workflow notes

- `flwr-datasets create` currently supports IID demo partitions only.
- `--num-partitions` must be a positive integer.
- The command writes one `partition_<id>/` directory per partition.
- If you need skewed partitions on disk, create them in Python first and save them yourself.
