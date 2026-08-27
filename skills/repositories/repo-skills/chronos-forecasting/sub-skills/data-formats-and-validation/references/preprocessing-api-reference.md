# Preprocessing API reference

The signatures below are the verified public helpers used by Chronos data
preparation paths.

## Shared output schema

`chronos.chronos2.preprocess` returns `PreparedInput` values with this shape:

```python
{
    "context": torch.Tensor,           # (n_targets + n_covariates, history_length)
    "future_covariates": torch.Tensor, # (n_targets + n_covariates, prediction_length)
    "n_targets": int,
    "n_covariates": int,
    "n_future_covariates": int,
}
```

Important row-order rule:
- target rows come first
- past-only covariates come before known-future covariates
- the future tensor is NaN-padded for target rows and for covariates whose future values are unavailable

## Verified helper signatures

```python
chronos.df_utils.infer_freq_from_df(
    df: pandas.DataFrame,
    id_column: str = 'item_id',
    timestamp_column: str = 'timestamp',
) -> str

chronos.df_utils.make_future_df(
    df: pandas.DataFrame,
    prediction_length: int,
    freq: str | None = None,
    id_column: str = 'item_id',
    timestamp_column: str = 'timestamp',
) -> pandas.DataFrame

chronos.df_utils.normalize_df(
    df: pandas.DataFrame,
    id_column: str = 'item_id',
    timestamp_column: str = 'timestamp',
    order: numpy.ndarray | None = None,
) -> pandas.DataFrame

chronos.df_utils.validate_df(
    df: pandas.DataFrame,
    future_df: pandas.DataFrame | None,
    target_columns: list[str],
    known_covariates_names: list[str] | None,
    prediction_length: int,
    id_column: str,
    timestamp_column: str,
) -> None

chronos.df_utils.validate_and_normalize_df(
    df: pandas.DataFrame,
    future_df: pandas.DataFrame | None,
    target_columns: list[str],
    prediction_length: int,
    known_covariates_names: list[str] | None = None,
    id_column: str = 'item_id',
    timestamp_column: str = 'timestamp',
) -> tuple[pandas.DataFrame, pandas.DataFrame | None]

chronos.df_utils.convert_df_input_to_list_of_dicts_input(
    df: pandas.DataFrame,
    future_df: pandas.DataFrame | None,
    target_columns: list[str],
    prediction_length: int,
    id_column: str = 'item_id',
    timestamp_column: str = 'timestamp',
    validate_inputs: bool = True,
) -> tuple[list[dict[str, numpy.ndarray | dict[str, numpy.ndarray]]], numpy.ndarray, dict[str, pandas.DatetimeIndex]]

chronos.chronos2.preprocess.from_tensor(
    data: torch.Tensor | np.ndarray,
    prediction_length: int,
) -> list[PreparedInput]

chronos.chronos2.preprocess.from_list_of_tensors(
    data: list[torch.Tensor | np.ndarray],
    prediction_length: int,
) -> list[PreparedInput]

chronos.chronos2.preprocess.from_data_frame(
    df: pandas.DataFrame,
    target_columns: list[str],
    prediction_length: int,
    future_df: pandas.DataFrame | None = None,
    known_covariates_names: list[str] | None = None,
    id_column: str = 'item_id',
    timestamp_column: str = 'timestamp',
    use_target_encoding: bool = True,
    validate_inputs: bool = True,
) -> list[PreparedInput]

chronos.chronos2.preprocess.from_list_of_dicts(
    data: list[dict],
    prediction_length: int,
    known_covariates_names: list[str] | None = None,
    use_target_encoding: bool = True,
    validate_inputs: bool = True,
) -> list[PreparedInput]
```

## Decision guide

### Use `from_data_frame` when...
- your source data is already in long-format pandas form
- you need automatic schema validation and timestamp normalization
- you want Chronos to split past-only vs known-future covariates for you
- you may need categorical encoding for object/bool columns

### Use `from_list_of_dicts` when...
- each series is already stored as a dict of arrays
- you need to preserve a custom per-series source layout
- future covariate availability differs by key but is consistent across series

### Use `from_tensor` or `from_list_of_tensors` when...
- you only have target tensors/arrays
- there are no covariates
- every variate should be treated as a target

### Use `convert_df_input_to_list_of_dicts_input` only when...
- you need the legacy AutoGluon-compatible output contract
- you accept the deprecation warning and the older adapter semantics

## Helper behavior that matters

- `from_data_frame` forbids providing both `future_df` and
  `known_covariates_names`.
- `from_list_of_dicts` accepts `future_covariates` values of `None` or empty to
  mean “known into the future, but values unavailable”.
- `use_target_encoding=True` only enables target encoding when there is a
  single target; multivariate inputs fall back to ordinal encoding.
- Boolean covariates are handled as categorical, not as raw 0/1 floats.
- `validate_inputs=False` means the caller must already satisfy the documented
  ordering, shape, and alignment assumptions.
