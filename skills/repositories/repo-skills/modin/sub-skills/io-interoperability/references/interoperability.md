# Modin interoperability reference

## Public conversion helpers

The main conversion helpers live in `modin.pandas.io` and on the `.modin` accessor.

| Direction | API | Backend/dependency notes |
| --- | --- | --- |
| pandas -> Modin | `modin.pandas.DataFrame(pandas_df)` | Works for ordinary pandas objects; large pandas inputs are already local. |
| Modin -> pandas | `modin_df.modin.to_pandas()` or `modin.pandas.io.to_pandas(obj)` | Materializes on the driver. Use only on bounded data. |
| Modin -> NumPy | `modin_df.to_numpy()` or `modin.pandas.io.to_numpy(obj)` | Materializes array data locally. |
| Arrow Table -> Modin | `from_arrow(pyarrow_table)` | Requires pyarrow. |
| dataframe interchange -> Modin | `from_dataframe(df.__dataframe__())` | Useful for objects implementing the dataframe interchange protocol. |
| Ray Dataset -> Modin | `from_ray(ray_dataset)` | Requires Ray engine and Ray Data. |
| Modin -> Ray Dataset | `modin_df.modin.to_ray()` | Requires Ray engine. |
| Dask DataFrame -> Modin | `from_dask(dask_df)` | Requires Dask engine and `dask.dataframe`. |
| Modin -> Dask DataFrame | `modin_df.modin.to_dask()` | Requires Dask engine. |
| map -> Modin | `from_map(func, iterable, *args, **kwargs)` | Creates a row-partitioned DataFrame. Expected engines are Ray, Dask, or Unidist. |

## Dataframe interchange

```python
import pandas
import modin.pandas as pd
from modin.pandas.io import from_dataframe

source = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
protocol_obj = source.__dataframe__()
round_trip = from_dataframe(protocol_obj)
pandas.testing.assert_frame_equal(round_trip.modin.to_pandas(), source.modin.to_pandas())
```

The protocol is useful for integration, but it can warn or default to pandas depending on dtype support. Validate on a tiny fixture first.

## Ray and Dask conversions

Ray and Dask conversions are engine-specific. Set the engine before import and use a main guard in scripts.

```python
import os
os.environ["MODIN_ENGINE"] = "Ray"


def main():
    import ray
    import pandas
    import modin.pandas as pd
    from modin.pandas.io import from_ray

    ray.init(num_cpus=2, include_dashboard=False, ignore_reinit_error=True)
    pandas_df = pandas.DataFrame({"x": [1, 2, 3]})
    modin_df = from_ray(ray.data.from_pandas(pandas_df))
    ray_dataset = pd.DataFrame(pandas_df).modin.to_ray()
    pandas.testing.assert_frame_equal(ray_dataset.to_pandas(), pandas_df)


if __name__ == "__main__":
    main()
```

For Dask, use `MODIN_ENGINE=Dask`, `dask.dataframe.from_pandas(...)`, `from_dask(...)`, and `modin_df.modin.to_dask().compute()`.

## Low-level partition APIs

`modin.distributed.dataframe.pandas.unwrap_partitions` exposes the underlying Ray object refs / Dask futures / Unidist refs. `from_partitions` rebuilds a Modin DataFrame from those partitions. Use them only when an integration truly needs direct partition ownership.

Important notes:

- `unwrap_partitions(obj, axis=None)` returns the current 2D partition layout.
- `axis=0` unwraps row partitions; `axis=1` unwraps column partitions.
- `get_ip=True` returns `(ip_ref, partition_ref)` pairs for supported engines.
- `from_partitions(..., index=..., columns=..., row_lengths=..., column_widths=...)` can avoid extra metadata computation.
- These APIs are lower-level than ordinary readers/converters and can break if the engine or partition manager changes.

## Validation pattern

When converting between systems, compare a tiny fixture both directions, normalize index/order, and only then try the production-size object.
