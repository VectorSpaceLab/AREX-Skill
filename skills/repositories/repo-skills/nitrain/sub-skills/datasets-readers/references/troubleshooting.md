# Troubleshooting

## Purpose

Use this for dataset and reader failures that are predictable from the public
API and the repo tests.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No file found at ...` | `ColumnReader.base_file` or `Dataset.base_dir` points to the wrong table path. | Fix the base file, then rerun `Dataset(...)`. |
| `fetch_data` writes to an unexpected cache location | `NITRAIN_DIR` is set or the default `~/.nitrain` cache is not what you expected. | Set `NITRAIN_DIR` explicitly or pass `path=` to `fetch_data(...)`. |
| `No filepaths found that match ...` | The glob pattern did not match any files under `base_dir`. | Check the pattern, the root directory, and any `exclude` filter. |
| `Could not infer a configuration from given value` | `infer_reader()` was given an unsupported object type. | Wrap the object in a supported reader or convert it to a list/dict/array. |
| Length warning during `Dataset(...)` creation | Input and output readers mapped different numbers of records. | Align the file patterns and verify the same split/filter logic on both sides. |
| `You must either supply file to ColumnReader or base_file to Dataset` | A column reader was created without a table path. | Pass `base_file` directly to the reader or to the dataset. |
| `The format value must be integer, onehot, or string` | `FolderNameReader.format` was misspelled or unsupported. | Choose one of the three supported values. |
| `GoogleCloudDataset` 403/404 or credential errors | Missing bucket access, wrong object path, or invalid service-account JSON. | Verify the bucket, path, and credentials before blaming the package. |
| `pip check` reports Google Cloud / protobuf conflicts | The latest `google-cloud-storage` stack pulled protobuf metadata that clashes with TensorFlow 2.17.0. | Pin the verified Google Cloud versions from `references/installation.md`. |
| `fetch_data('openneuro/...')` stalls or fails | `datalad` / `git-annex` or network access is missing. | Install the optional tools and retry only if the user really needs the OpenNeuro path. |

## Recovery steps

1. Start with the smallest local reader that fits the data shape.
2. Verify the table path and glob against the example fixture if possible.
3. Use `Dataset.split(..., random=False)` first when debugging alignment.
4. If cloud access is required, reproduce the same reader setup against a local
   fixture before debugging credentials.

## Good signals

- `Dataset[0]` returns the expected image or scalar pair.
- `Dataset.split()` returns the right subset sizes.
- `example-01` builds successfully and contains the expected synthetic files.

## Hand off when

- the request grows into augmentation or batch loading;
- the issue is really about model training or prediction;
- the data source is cloud-only and the local package logic is already correct.
