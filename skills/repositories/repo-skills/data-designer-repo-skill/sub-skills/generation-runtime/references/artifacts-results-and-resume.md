# Artifacts, Results, and Resume

This reference explains what lands on disk, what the result objects read back, and how resume behaves.

## Dataset artifact tree

A standard generation run writes a dataset tree under the active artifact root:

```text
<artifact_path>/<dataset_name>/
  builder_config.json
  metadata.json
  parquet-files/
    batch_00000.parquet
    batch_00001.parquet
    ...
  dropped-columns-parquet-files/
    batch_00000.parquet
    ...
  processors-files/
    <processor_name>/...
  tmp-partial-parquet-files/
    ...
  scheduler_events.jsonl   # only when write_scheduler_events=True
```

Notes:

- `builder_config.json` is the human-readable run config snapshot.
- `metadata.json` is the resume and progress checkpoint.
- `parquet-files/` holds the main data batches.
- `dropped-columns-parquet-files/` exists only when dropped columns are preserved.
- `processors-files/` stores processor outputs.
- `tmp-partial-parquet-files/` is an in-flight scratch area for interrupted runs.

If a dataset directory already exists and the run is not resuming, the storage layer may choose a timestamped sibling directory instead of overwriting the previous run.

## Workflow artifact tree

Composite workflows add a workflow-level directory:

```text
<artifact_path>/<workflow_name>/
  workflow-metadata.json
  stage-0-<stage_name>/
    builder_config.json
    metadata.json
    parquet-files/
    processors-files/
    callback-outputs/
    output-processors/
  stage-1-<stage_name>/
    ...
```

Workflow metadata tracks stage fingerprints, reuse status, output selection, and downstream dependencies.

## `PreviewResults` semantics

`DataDesigner.preview()` returns an in-memory `PreviewResults` object.

Public fields:

- `dataset`: preview `DataFrame`
- `analysis`: profiler output
- `processor_artifacts`: processor outputs as records, not files
- `dataset_metadata`: metadata attached to the preview run
- `task_traces`: task traces when tracing is enabled

Public method:

- `to_config_builder(columns=None)` — seed a new builder from the preview dataset

Preview results are meant for interactive iteration. They are not the persisted artifact tree.

## `DatasetCreationResults` semantics

`DataDesigner.create()` returns `DatasetCreationResults`.

Constructor signature:

```python
DatasetCreationResults(
    *,
    artifact_storage: ArtifactStorage,
    analysis: DatasetProfilerResults,
    config_builder: DataDesignerConfigBuilder,
    dataset_metadata: DatasetMetadata,
    task_traces: list[TaskTrace] | None = None,
)
```

Important behaviors:

- `load_dataset()` reads the full dataset from the current `parquet-files/` directory.
- `load_analysis()` returns the profiler result object captured during the run.
- `count_records()` reads parquet metadata only; it does not load data pages.
- `load_processor_dataset(processor_name)` loads a processor output written as parquet.
- `get_path_to_processor_artifacts(processor_name)` returns the on-disk processor artifact path.
- `export()` streams batch files one at a time.
- `push_to_hub()` uploads the base dataset path and supporting artifacts.
- `task_traces` only covers the current invocation.

Because the disk-backed methods read the current file tree, they see any later-added parquet files as well. That is useful for resumed runs and for debugging unexpected artifact edits.

## `export()` behavior

Supported export formats:

- `jsonl`
- `csv`
- `parquet`

Behavior summary:

- If `format=` is omitted, the suffix is used.
- The suffix is case-insensitive.
- An explicit `format=` overrides the suffix.
- JSONL streams one record per line.
- CSV writes one header row and appends each batch in order.
- Parquet unifies batch schemas permissively before writing.

Caveats:

- The output directory must already exist.
- Unsupported suffixes or format overrides raise `InvalidFileFormatError`.
- If no batch files exist, `ArtifactStorageError` is raised.

## `push_to_hub()` behavior

`push_to_hub()` uploads the dataset via the Hugging Face hub client.

It requires:

- network access
- a valid token or cached Hugging Face auth
- a dataset tree that is fully materialized on disk

The upload includes:

- main parquet batches
- processor outputs
- `builder_config.json`
- `metadata.json`
- the generated dataset card

Workflow caveat:

- `CompositeWorkflowResults.push_to_hub()` only works when the final selected output is the raw final-stage dataset.
- If the workflow selected a processor artifact or a callback output, use `export()` or push the stage result directly.

## Resume modes

### `ResumeMode.NEVER`

- Always starts fresh.
- If a non-empty dataset folder already exists, the storage layer may move to a timestamped sibling directory instead of reusing the old one.

### `ResumeMode.ALWAYS`

- Reuses the existing dataset or workflow directory only when the stored state is compatible.
- Rejects mismatched config fingerprints, buffer sizes, dropped-column policies, or workflow stage fingerprints.
- If the previous run died before the first durable checkpoint, the builder can restart from the beginning.

### `ResumeMode.IF_POSSIBLE`

- Reuses state when the fingerprint and artifact policy match.
- Falls back to a fresh run when compatibility is unclear or stale metadata is encountered.

## Resume scope

Resume changes what is read from disk, not what is remembered in memory.

- Disk-backed methods reflect the full accumulated dataset.
- `task_traces` and runtime telemetry only cover the current invocation.
- Workflow reuse is stage-by-stage, not just dataset-by-dataset.

## What to check when a resumed run looks wrong

1. Compare the current `RunConfig` with the original run.
2. Confirm `buffer_size` and `preserve_dropped_columns` did not change.
3. Confirm the config hash and workflow fingerprint still match.
4. Inspect `metadata.json` and `workflow-metadata.json` for corruption or stale fields.
5. Re-export the selected dataset output to confirm the on-disk files are the source of truth.

## Short version

- `preview` is memory-only.
- `create` is artifact-backed.
- `load_dataset`, `count_records`, `export`, and `push_to_hub` read the current artifact tree.
- `resume` is controlled by artifact compatibility, not by in-memory state.
