# Runtime Workflows

This reference gives the recommended order for running DataDesigner through Python without falling into API, logging, or resume traps.

## 1) Safe local smoke flow

Use this order when you want a sampler-only local check with no remote model calls:

1. Build or load a `DataDesignerConfigBuilder`.
2. Create `DataDesigner` with a non-empty provider list, even if the config has no model aliases. The registry cannot be empty.
3. Call `set_run_config()` before generation if you need quieter logs or a smaller row-group size.
4. Call `validate()` first.
5. Call `check_models()` only when model aliases or MCP tool aliases are referenced.
6. Call `preview()` for a tiny in-memory sample.
7. Call `create()` when you want on-disk artifacts.
8. Inspect the returned result object with `load_dataset()`, `count_records()`, `load_analysis()`, and `export()`.

A good local smoke runtime config is:

- `buffer_size` small enough to exercise more than one row group if desired
- `display_tui=False`
- `otel_metrics_port=None`
- `write_scheduler_events=False`
- `async_trace=False`

That keeps the run local, quiet, and deterministic.

## 2) Validate vs check_models

Use these in this order:

- `validate()` checks whether the configuration is structurally valid and compilable.
- `check_models()` checks whether external model and MCP dependencies are responsive.

This means:

- A sampler-only config can still pass `validate()` even if there are no usable model aliases.
- `check_models()` is the first place to look when a model-backed workload fails because of API keys, provider connectivity, or MCP readiness.
- If you only need to confirm that a sampler-only config is well formed, `validate()` is enough.

If you need to temporarily bypass model health probes while triaging, the engine also honors `DATA_DESIGNER_SKIP_MODEL_HEALTH_CHECKS=1`.

## 3) Preview flow

`preview()` is the fast, in-memory iteration path.

Use it when you want to:

- confirm the config compiles and generates rows
- inspect a few sample rows without writing a full artifact tree
- look at `analysis`, `dataset_metadata`, or `processor_artifacts`
- seed a new builder from `PreviewResults.to_config_builder()`

Preview rules:

- it does not write dataset artifacts
- it is safer than `create()` when you only need a quick check
- it still goes through the runtime compiler and processor stack

## 4) Create flow

Use `create()` when you want persisted artifacts, resume support, export, or hub upload.

Recommended pattern:

1. `validate(builder)`
2. `check_models(builder)` if external aliases exist
3. `preview(builder, num_records=...)`
4. `set_run_config(...)` with the desired runtime settings
5. `create(builder, num_records=..., dataset_name=..., resume=...)`

Important `create()` notes:

- `artifact_path` can be overridden per call.
- `on_batch_complete` is synchronous and should stay lightweight.
- `resume=ResumeMode.NEVER` starts fresh.
- `resume=ResumeMode.ALWAYS` is strict and expects compatible prior state.
- `resume=ResumeMode.IF_POSSIBLE` reuses only when the stored state matches.

## 5) Async usage

`acreate()` is a thread offload wrapper around `create()`.

Use it when:

- you are inside an async application
- you want the event loop to stay responsive while generation runs
- you want to launch multiple DataDesigner runs concurrently

It does **not** serialize calls for you. Concurrent `acreate()` calls can overlap just like concurrent `create()` calls in separate threads.

## 6) Workflow chaining

`compose_workflow(name=...)` creates the experimental linear workflow API.

### Minimal model of a workflow

- Each stage is added with `add_stage(...)`.
- Each stage gets its own artifact subdirectory.
- Downstream stages seed from the selected output of the previous stage.
- `run()` executes the chain or the requested subset of it.

### Stage output selection

A stage can hand off one of three output shapes downstream:

- the main stage output (`output="final"`)
- a named processor artifact (`output="processor:<name>"`)
- a callback output returned from `on_success`

### Common workflow controls

- `targets`: run only up to a given stage or stage set
- `rerun_from`: force one stage and all descendants to rebuild
- `stage_output_overrides`: replace a stage's selected output with an external parquet directory
- `resume=ResumeMode.IF_POSSIBLE`: reuse compatible stages when the fingerprint matches
- `resume=ResumeMode.ALWAYS`: require reusable metadata and fail on mismatch

### When to use workflow output helpers

- Use `load_stage_output(stage_name)` to inspect the selected output handed to the next stage.
- Use `export_stage(stage_name, path)` when you want a specific stage output.
- Use `push_to_hub()` only when the final selected output is the raw final-stage dataset.

If the final selected output is a processor-selected or overridden output, `push_to_hub()` is not the right path; export the selected output or push the stage result directly.

## 7) TTY and logging

`display_tui` only produces the throughput panel when the terminal is interactive.

Practical rules:

- In a non-TTY shell, `display_tui=True` falls back to log lines.
- `preview()` is log-based and does not use the throughput panel.
- For CI or script-driven smoke checks, set `display_tui=False` so the output stays predictable.
- The first generation log line also records the selected Jinja rendering engine.

## 8) Practical resume checklist

Before resuming a run, confirm:

- `dataset_name` is the same logical dataset or workflow name
- `buffer_size` matches the original run
- dropped-column policy has not changed
- the config fingerprint still matches
- workflow stage names and stage fingerprints still match

If any of those changed, `IF_POSSIBLE` is the safer fallback than `ALWAYS`.
