# Data Utilities Troubleshooting

## Named Variable Missing

Check `df.columns`, spelling, and `data=`. A string `x="col"` is interpreted as a column name only when `data=df` is present.

## DataFrame Passed to `load_dataset`

`sns.load_dataset` accepts a string dataset name, not a DataFrame. Plot existing data directly with `data=df`.

## Network or Cache Failure

`load_dataset` and `get_dataset_names` require network unless the CSV is already cached. Use `data_home=` or `SEABORN_DATA` for cache control. Prefer synthetic data in robust scripts.

## Long vs Wide Mistake

If semantic mappings are ignored or variables cannot be interpreted, reshape wide data to long form with pandas (`melt`, `pivot`, or `stack`) and name variables explicitly.

## Null or Non-numeric Data

Drop/impute nulls before statistical summaries when appropriate. For numeric axes, check pandas dtypes and convert strings to numeric intentionally.

## Heatmap Mask Mismatch

The mask must match the final matrix shape and labels. Build masks from the same DataFrame index/columns where possible.
