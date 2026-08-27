# Data Formats

## Scitypes and mtypes

`sktime` separates abstract scientific data types from concrete containers.

| Scitype | Meaning | Common mtypes |
| --- | --- | --- |
| `Series` | one time series | `pd.Series`, `pd.DataFrame`, `np.ndarray` variants |
| `Panel` | collection of series instances | `numpy3D`, `pd-multiindex`, list of DataFrames |
| `Hierarchical` | grouped collection of series | hierarchical pandas MultiIndex layouts |
| `Table` | non-temporal feature table | pandas DataFrame/Series, numpy 1D/2D |

## Public validation APIs

Verified signatures:

- `check_is_mtype(obj, mtype, scitype=None, return_metadata=False, var_name='obj', msg_return_dict='dict')`.
- `convert_to(obj, to_type, as_scitype=None, store=None, store_behaviour=None, return_to_mtype=False)`.

Use `return_metadata=True` to inspect properties such as univariate/multivariate,
number of instances, equal length, missing values, feature names, and inferred
mtype/scitype.

## Panel MultiIndex checklist

A `pd-multiindex` panel should have rows indexed by instance and time levels;
columns are variables/channels. Sort the index, keep one row per instance-time
combination, and align labels `y` to the number of panel instances.

## Conversion guidance

Convert only after choosing the estimator workflow. Some estimators prefer
`numpy3D`; others accept pandas panels. Do not discard time indexes when a
forecasting or temporal evaluation task needs them.
