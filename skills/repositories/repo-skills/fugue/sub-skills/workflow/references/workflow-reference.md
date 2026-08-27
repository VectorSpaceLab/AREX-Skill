# Workflow reference

## Core objects

- `FugueWorkflow(compile_conf=None)` creates a workflow DAG.
- `WorkflowDataFrame` is the workflow-edge object. It is not a materialized dataframe until you run the workflow.
- `WorkflowDataFrames` groups multiple workflow outputs.

## Main workflow pattern

```python
import pandas as pd
from fugue import FugueWorkflow

pdf = pd.DataFrame({"a": [0, 1], "b": [2, 3]})

def add_total(df: pd.DataFrame, inc: int = 1) -> pd.DataFrame:
    return df.assign(total=df.a + df.b + inc)

with FugueWorkflow() as dag:
    df = dag.df(pdf)
    out = df.transform(add_total, schema="*,total:int", params={"inc": 1})
    out.yield_dataframe_as("result", as_local=True)

res = dag.run()
print(res["result"].as_array())
```

## Workflow-building methods

| API | What it does |
| --- | --- |
| `dag.df(data, schema=None, data_determiner=None)` | Wrap native data or a dataframe-like object |
| `dag.create(using, schema=None, params=None)` | Create a workflow dataframe from a creator |
| `dag.load(path, fmt='', columns=None, **kwargs)` | Load a file into the workflow |
| `dag.select(...)` | Run ad hoc SQL-style selection inside the workflow |
| `dag.join(...)` | Join workflow dataframes |
| `dag.run(engine=None, conf=None, **kwargs)` | Execute the DAG and return yielded outputs |

## `WorkflowDataFrame` methods that matter most

| API | What to use it for |
| --- | --- |
| `partition(...)` / `partition_by(...)` | Set partition rules before the next step |
| `per_row()` / `per_partition_by(...)` | Convenience partition shortcuts |
| `transform(...)` / `process(...)` / `out_transform(...)` | Run user-defined functions |
| `output(...)` | Run a side-effect outputter |
| `persist()` / `broadcast()` | Materialize or broadcast intermediate data |
| `checkpoint()` / `strong_checkpoint()` / `weak_checkpoint()` / `deterministic_checkpoint()` | Persist checkpoints with different semantics |
| `save(...)` / `save_and_use(...)` | Write files and optionally continue using the saved result |
| `yield_dataframe_as(...)` / `yield_file_as(...)` | Expose workflow outputs under a name |
| `assert_eq(...)` | Compare against another dataframe inside the DAG |
| `zip(...)` | Combine multiple workflow dataframes |

## Decorator and wrapper conventions

| Decorator | Expected shape |
| --- | --- |
| `creator(schema=None)` | `func(wf: FugueWorkflow, ...) -> WorkflowDataFrame` or `WorkflowDataFrames` |
| `processor(schema=None, **validation_rules)` | `func(df: pandas.DataFrame, ...) -> pandas.DataFrame` or equivalent |
| `transformer(schema, **validation_rules)` | `func(df: pandas.DataFrame, ...) -> pandas.DataFrame` |
| `outputter(**validation_rules)` | `func(df: pandas.DataFrame, ...) -> None` |
| `cotransformer(schema, **validation_rules)` | a function that consumes multiple dataframes and returns a dataframe |
| `output_transformer(**validation_rules)` / `output_cotransformer(...)` | output-only variants |
| `module(func=None, as_method=False, name=None, on_dup='overwrite')` | Wrap a workflow helper as a reusable workflow module or method |

## Partitioning notes

- Use `PartitionSpec`-style arguments through `partition(...)` or `partition_by(...)`.
- Common knobs: `by`, `presort`, `num`, and `algo`.
- `algo="even"`, `algo="hash"`, `algo="rand"`, and `algo="coarse"` appear in the supported workflow surface.
- `per_row()` is the quickest way to force row-wise execution.

## Return-type notes

- `as_fugue=True` keeps Fugue dataframe objects in the one-shot helpers.
- `as_local=True` materializes to a local dataframe when the helper supports it.
- For string paths in the one-shot helpers, use parquet only; use `load(...)` / `save(...)` for other file formats.

## Read next

- `references/troubleshooting.md`
- `scripts/workflow_smoke.py`
