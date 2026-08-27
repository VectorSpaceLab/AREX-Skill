# Data Setup Troubleshooting

## Missing data and schema problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Missing-column error | A selected column is absent from reference or analysis data | Intersect the requested column list with the actual dataframe columns before fitting. |
| Empty dataframe error | A filter, join, or read step produced no rows | Inspect shapes after every load/join/filter before calling `fit` or `calculate`. |
| Time-based chunking fails | `chunk_period` or `PeriodBasedChunker` needs a parseable timestamp column | Add `timestamp_column_name`, verify the column exists, and confirm pandas can parse it. |
| Too few chunks warning | The chosen chunking strategy produced very few chunks | Reduce `chunk_size`, increase data volume, or choose a different chunking approach. |
| Invalid `chunk_size` / `chunk_number` | Non-positive or non-integer chunk settings | Use positive integers only. |
| Unexpected chunk ordering | Timestamp-based chunks are sorted by the timestamp column | Ensure timestamps are correct and consistently formatted. |

## Chunker-specific problems

### `SizeBasedChunker`

- `chunk_size` must be a positive integer.
- `incomplete` must be one of `keep`, `drop`, or `append`.
- Use `append` when you want the final remainder merged into the last full chunk.

### `CountBasedChunker`

- `chunk_number` must be a positive integer.
- The derived chunk size depends on the number of rows in the dataset.
- Very uneven row counts can produce small leftover chunks.

### `PeriodBasedChunker`

- A timestamp column is required.
- The timestamp column must be parseable by pandas.
- Use this only when calendar alignment matters.

## Data-quality calculator problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `MissingValuesCalculator` is too noisy | You expected counts but are using rates, or vice versa | Choose `normalize=True` for rates or `normalize=False` for counts. |
| `UnseenValuesCalculator` rejects columns | One or more columns are not categorical after dtype inference | Convert the columns to categorical or choose `treat_as_*` behavior at the data-prep stage. |
| `NumericalRangeCalculator` rejects columns | A selected column is categorical | Use only continuous columns; if the column is a code or label, monitor it with unseen-values or categorical drift instead. |
| Summary-stat calculator rejects columns | Categorical columns were included in avg/median/std/sum | Remove categorical columns or cast them appropriately before selection. |

## Threshold problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Threshold validation error | Lower/upper threshold values are invalid or reversed | Use numeric values, keep `lower < upper` when both are set, and choose the right threshold class. |
| Custom threshold seems ignored | The calculator does not support that threshold override path | Check the calculator-specific docs and fall back to the default or a supported threshold type. |
| Alerts seem inverted | The threshold semantics are not what you expected | Remember that many data-quality metrics alert on values above an upper bound, while `row_count` can alert on both sides when using a custom threshold. |

## Dataset selection problems

- Use car-loan datasets for compact binary examples.
- Use car-price datasets for regression and summary-stat examples.
- Use the data-quality car-loan dataset when you need missing/unseen/range signals.
- Use multiclass datasets only when you truly need multiclass probability mappings.

If the user is actually trying to run performance estimation or drift detection, route to the neighboring sub-skill rather than trying to force the data-prep calculator to do the job.
