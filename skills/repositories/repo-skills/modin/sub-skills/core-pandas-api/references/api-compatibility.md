# API compatibility and validation

## What Modin promises

Modin presents a pandas-compatible API through `modin.pandas`. Most user code starts by changing one import, but compatibility and performance are not the same. Some pandas methods are implemented in distributed form, some are partially implemented, and some default to pandas internally.

## Default-to-pandas behavior

A warning that an operation is `not currently supported` and is `defaulting to pandas implementation` means Modin collected data for a pandas implementation and then wrapped the result back into Modin. The result may be correct but slow or memory intensive. Use this warning to identify hot paths and materialization points.

## Equality checks

Use pandas testing utilities on bounded data:

```python
import pandas

expected = pandas_result.sort_index()
actual = modin_result.modin.to_pandas().sort_index()
pandas.testing.assert_frame_equal(actual, expected, check_dtype=False)
```

For groupby or join results, explicitly sort by keys or index. For floating results, use tolerances. For string and nullable dtypes, decide whether exact dtype is part of the contract.

## Schema and dtype caveats

- Parallel CSV partitions can see different values. Supply `dtype` for columns that mix integers, strings, missing values, or identifiers with leading zeroes.
- Date parsing should be explicit with `parse_dates` or a post-read conversion whose failure handling is tested.
- Category handling may differ when categories are inferred per partition; normalize categories if exact category ordering matters.
- Index semantics can matter for joins and comparisons. Create a stable index after reading if later code assumes one.

## Materialization points

`to_pandas()`, `to_numpy()`, iteration over rows, unsupported pandas operations, and many third-party libraries can collect distributed data on the driver. For production-scale data, validate on samples and use aggregate checks rather than full materialization.

## Execution-specific differences

The same pandas-like code can run over Ray, Dask, Python, or Native/Pandas backends. Engine startup, serialization, and worker errors are engine issues rather than core API semantics; route them to the engine sub-skill. If an operation behaves differently across engines, reproduce it with a tiny fixture under each engine and record the active `Engine`, `StorageFormat`, and `Backend`.

## Unsupported or experimental areas

Do not treat `modin.experimental`, `modin.numpy`, or `modin.polars` as stable `modin.pandas`. They have separate routing and version caveats. If a task crosses those APIs, start with the stable pandas-compatible data step here, then route the extension step to the advanced sub-skill.
