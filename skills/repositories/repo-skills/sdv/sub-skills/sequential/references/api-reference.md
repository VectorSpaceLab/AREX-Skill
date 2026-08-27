# Sequential API reference

## Imports

```python
from sdv.metadata import Metadata
from sdv.metadata.single_table import SingleTableMetadata
from sdv.sequential import PARSynthesizer
from sdv.utils import get_random_sequence_subset
```

`PARSynthesizer` is for one sequential table. If using unified `Metadata`, it must contain exactly one table; multi-table metadata is not accepted by PAR.

## Metadata sequence helpers

| API | Purpose | Notes |
| --- | --- | --- |
| `Metadata.detect_from_dataframes(data)` | Detect unified metadata from `dict[str, DataFrame]`. | For PAR, pass a dict with one table and then edit sdtypes/keys explicitly. |
| `metadata.update_column(column_name, table_name=None, **kwargs)` | Correct sdtypes such as `id`, `datetime`, `numerical`, or `categorical`. | Sequence keys should normally be `id`; sequence indexes must be `datetime` or `numerical`. |
| `metadata.set_sequence_key(column_name, table_name=None)` | Declare the column that groups rows into sequences. | Required for `PARSynthesizer`. This is not an ordinary primary key because many rows share one sequence key value. |
| `metadata.set_sequence_index(column_name, table_name=None)` | Declare the order/timing column inside each sequence. | Optional, but use it when row order matters. The column cannot be the same as the sequence key. |
| `SingleTableMetadata.set_sequence_key(column_name)` | Same declaration for legacy/single-table metadata. | Use only when a downstream API specifically expects `SingleTableMetadata`. |
| `SingleTableMetadata.set_sequence_index(column_name)` | Same sequence-index declaration for single-table metadata. | The sdtype must be `datetime` or `numerical`. |

## `PARSynthesizer` constructor

```python
PARSynthesizer(
    metadata,
    enforce_min_max_values=True,
    enforce_rounding=True,
    locales=['en_US'],
    context_columns=None,
    segment_size=None,
    epochs=128,
    sample_size=1,
    cuda=True,
    verbose=False,
)
```

| Parameter | Meaning | Operational guidance |
| --- | --- | --- |
| `metadata` | One-table `Metadata` or `SingleTableMetadata` with `sequence_key`. | Constructor raises if no sequence key or if unified metadata has multiple tables. |
| `enforce_min_max_values` | Clip numerical reverse transforms to fitted min/max. | Keep `True` unless extrapolation is intentionally allowed. |
| `enforce_rounding` | Preserve learned rounding for numerical columns. | Keep `True` for integer-like or currency-like columns. |
| `locales` | Locale(s) for anonymized faker transformers. | Use a list or string matching the data locale. |
| `context_columns` | Columns that do not vary inside a sequence. | Must exclude the sequence key. Values must be constant per sequence key in fit data. |
| `segment_size` | Optional maximum segment length used when assembling training sequences. | Useful for very long sequences; preserve enough history for the target pattern. |
| `epochs` | PAR training epochs. | Use `epochs=1` for smoke tests; default is production-oriented and slower. |
| `sample_size` | Number of candidate samples before selecting a high-likelihood sequence. | Higher values may improve quality but cost more. |
| `cuda` | Whether PAR should try CUDA through torch/deepecho. | `True` attempts GPU when available and falls back to CPU if CUDA is unavailable; set `False` for CPU-only work. |
| `verbose` | Progress output during fitting/sampling. | Set `True` for interactive long runs. |

## Core methods

| API | Purpose | Key constraints |
| --- | --- | --- |
| `fit(data)` | Fit on the raw sequential `DataFrame`. | Sort by sequence key/index if order matters; context columns must be constant within each sequence. |
| `sample(num_sequences, sequence_length=None)` | Generate complete synthetic sequences. | `sequence_length=None` samples learned lengths; an integer forces each generated sequence to that length. |
| `sample_sequential_columns(context_columns, sequence_length=None)` | Generate sequential columns for supplied context rows. | Requires constructor `context_columns`. Input is one row per desired sequence; include the sequence key to control output sequence ids. |
| `validate(data)` | Validate data against metadata and PAR context rules. | Catches context columns that change within a sequence. |
| `preprocess(data)` / `fit_processed_data(data)` | Advanced staged fitting path. | Use only when transforming and fitting are intentionally separated. |
| `auto_assign_transformers(data)` | Let SDV assign transformers before optional edits. | PAR keeps sequence keys untransformed and relaxes min/max enforcement for sequence indexes. |
| `get_transformers()` | Inspect learned/assigned transformers. | Requires `auto_assign_transformers` or `fit` first. |
| `update_transformers(mapping)` | Override transformers for selected columns. | Modelable context columns cannot be updated; update non-context columns before fitting. |
| `add_constraints(constraints)` | Attach compatible constraints. | Add before `fit`; each constraint must cover only context columns or only non-context columns, with no overlapping constrained columns. |
| `get_constraints()` | Inspect attached constraints. | Constraint internals belong to the constraints sub-skill. |
| `get_parameters()` | Return constructor parameters excluding metadata. | Includes PAR model kwargs such as `epochs`, `sample_size`, `cuda`, and `verbose`. |
| `get_metadata(version='original')` | Return original or modified metadata. | Use `version='modified'` after constraints when downstream validation needs transformed metadata. |
| `get_info()` | Return fit/save metadata such as class name and fit status. | Useful after load to compare model lifecycle state. |
| `get_loss_values()` | Return PAR training loss values. | Available after fitting; use evaluation sub-skill for quality assessment. |
| `save(filepath)` | Serialize the synthesizer. | Saving before fit is allowed but warns; sample only after fit. |
| `PARSynthesizer.load(filepath)` | Deserialize a saved PAR synthesizer. | Loading GPU-created models on CPU-only hosts can fail; prefer CPU-compatible save/load when portability matters. |

## Sequence subsetting utility

```python
get_random_sequence_subset(
    data,
    metadata,
    num_sequences,
    max_sequence_length=None,
    long_sequence_subsampling_method='first_rows',
)
```

| Argument | Meaning | Notes |
| --- | --- | --- |
| `data` | Sequential `DataFrame`. | Must contain the metadata sequence key column. |
| `metadata` | Unified one-table `Metadata` or `SingleTableMetadata`. | Must declare a sequence key. |
| `num_sequences` | Number of sequence keys to draw. | Set a NumPy random seed outside the function if reproducibility matters, then verify the resulting unique sequence count. |
| `max_sequence_length` | Optional cap per selected sequence. | `None` keeps full selected sequences. |
| `long_sequence_subsampling_method` | One of `'first_rows'`, `'last_rows'`, or `'random'`. | `'random'` preserves the original row order among retained rows. |

Return value: a `DataFrame` containing rows for the selected sequence keys, reset to a simple row index.
