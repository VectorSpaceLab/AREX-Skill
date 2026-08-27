# Experimental Batch Pipeline

`modin.experimental.batch.PandasQueryPipeline` pipelines row-parallel queries over a Modin DataFrame. It is currently implemented for `PandasOnRay` only.

## Minimal shape

```python
import os
os.environ["MODIN_ENGINE"] = "Ray"


def main():
    import modin.pandas as pd
    from modin.experimental.batch import PandasQueryPipeline

    def add_total(partition):
        partition = partition.copy()
        partition["total"] = partition["a"] + partition["b"]
        return partition

    df = pd.DataFrame({"a": [1, 2], "b": [10, 20]})
    pipeline = PandasQueryPipeline(df, num_partitions=2)
    pipeline.add_query(add_total, is_output=True, output_id="with_total")
    outputs = pipeline.compute_batch()
    print(outputs["with_total"])


if __name__ == "__main__":
    main()
```

## Important rules

- The input DataFrame must be backed by `PandasOnRay`; configure Ray before import.
- Query functions receive pandas partition objects, not full Modin DataFrames. Use `pandas` for module-level operations inside callback functions.
- `PandasQueryPipeline(df, num_partitions=None)` defaults to `NPartitions.get()`.
- `add_query(func, is_output=False, repartition_after=False, fan_out=False, pass_partition_id=False, reduce_fn=None, output_id=None)` builds the DAG.
- If any output node uses `output_id`, all output nodes must use `output_id`; then `compute_batch()` returns a dict keyed by output id.
- `compute_batch(postprocessor=..., pass_output_id=True, pass_partition_id=True)` can pass metadata into the postprocessor in the order `partition`, `output_id`, `partition_id`.
- `fan_out=True` requires `reduce_fn` and is intended for the one-partition input case. Repartitioning support is limited.
- `compute_batch()` with no output nodes returns an empty list and warns.

## Safe verification

Use the bundled `batch_pipeline_smoke.py`. It creates a tiny DataFrame, adds two output nodes, passes output/partition metadata through a postprocessor, and verifies both outputs. It does not use network, cloud storage, or large data.

## Scaling guidance

After the smoke passes, scale one variable at a time: rows, partition count, callback cost, and output count. Keep callback functions top-level, deterministic, and free of open file handles or non-pickleable state. If a callback writes files, write to a temporary or explicitly chosen output directory and handle cleanup.
