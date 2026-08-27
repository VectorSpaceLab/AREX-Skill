# Dataset and File I/O

## Onboard datasets

Onboard loaders are offline-friendly and useful for smokes:

```python
from sktime.datasets import load_airline, load_arrow_head, load_basic_motions, load_tecator
```

Use forecasting loaders for `Series`, classification/regression loaders for
`Panel`, and generated toy data for data-format debugging.

## Downloaded dataset surfaces

Loaders such as remote UCR/UEA, M5, or forecasting repository loaders may need
network access, cache directories, and optional packages. Treat them as external
resource workflows: ask for cache/output location and verify connectivity before
running.

## File formats

Common public functions include:

- `load_from_tsfile_to_dataframe(full_file_path_and_name, return_separate_X_and_y=True, ...)`.
- `write_dataframe_to_tsfile(data, path, problem_name='sample_data', class_label=None, ...)`.
- `load_tsf_to_dataframe`, `load_from_arff_to_dataframe`, `load_from_ucr_tsv_to_dataframe`, and long-table loaders/writers.

Prefer tiny generated fixtures for tests. Do not require original example files.
