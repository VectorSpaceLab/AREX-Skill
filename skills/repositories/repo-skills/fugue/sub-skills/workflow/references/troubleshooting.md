# Workflow troubleshooting

## Function wrapper signatures do not match

**Symptoms**
- `FugueInterfacelessError`
- `module(...)` or `transform(...)` refuses a function

**Likely cause**
- The function is missing the workflow/dataframe annotations Fugue expects.

**Fix**
- Check the accepted shapes in `references/workflow-reference.md`.
- For `module`, include `wf`, `df`, or `dfs` in a supported position, and return `WorkflowDataFrame`, `WorkflowDataFrames`, or `None` depending on the module type.

## String-path helpers reject your file type

**Symptoms**
- A one-shot `transform(...)` or `out_transform(...)` call fails on a CSV or JSON path

**Likely cause**
- The express helpers only accept parquet paths as strings.

**Fix**
- Use a dataframe object instead of a string path.
- Or switch to `FugueWorkflow.load(...)` / `save(...)` for the file format you need.

## Callback code runs after the receiver has gone away

**Symptoms**
- A callback is invoked too late or sees a closed receiver

**Likely cause**
- The transform was still lazy when the callback executed.

**Fix**
- Add `persist=True` or `as_local=True` so the result materializes before the callback receiver shuts down.

## Checkpoint and save confusion

**Symptoms**
- A checkpoint lands in a different file each run
- `save_and_use(...)` and `save(...)` appear to behave differently

**Likely cause**
- `checkpoint()` and `deterministic_checkpoint()` have different persistence semantics, and `save_and_use(...)` returns a reusable dataframe whereas `save(...)` writes and stops.

**Fix**
- Use `deterministic_checkpoint(...)` when you need stable checkpoint paths.
- Use `save_and_use(...)` when you want to keep working with the saved result.

## Partitioning looks wrong

**Symptoms**
- A `transform(...)` runs on the wrong number of groups
- You expected row-wise behavior but got grouped behavior

**Likely cause**
- The partition spec is missing `by`, `num`, or `algo`, or `per_row()` / `per_partition_by(...)` was not used when intended.

**Fix**
- Read the partition section of `references/workflow-reference.md` and make the partition intent explicit.
