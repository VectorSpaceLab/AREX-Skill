# Kedro Run Options

Use this reference to build `kedro run` commands or equivalent `KedroSession.run()` calls. `kedro run` executes project code and can read/write datasets, so set telemetry opt-out variables for automated checks and verify the target project/configuration before running.

## Minimal Commands

```bash
KEDRO_DISABLE_TELEMETRY=1 kedro run
KEDRO_DISABLE_TELEMETRY=1 kedro run --runner=SequentialRunner
KEDRO_DISABLE_TELEMETRY=1 kedro run --runner=ThreadRunner
KEDRO_DISABLE_TELEMETRY=1 KEDRO_MP_CONTEXT=spawn kedro run --runner=ParallelRunner
```

`kedro run` uses `SequentialRunner` when `--runner` is omitted. The CLI loads a runner object from `kedro.runner` by default, so built-ins can be named as `SequentialRunner`, `ThreadRunner`, or `ParallelRunner`. Custom runners can be passed as an import path such as `project_package.runner.DryRunner` when that object can be imported in the project environment.

## Flag Reference

| Need | CLI option | `KedroSession.run()` argument | Notes |
| --- | --- | --- | --- |
| Choose runner | `--runner` or `-r` | `runner=SequentialRunner()` | Pass a runner instance to the API, not the class. |
| Async load/save | `--async` | runner constructor `is_async=True` | Applies to `SequentialRunner` and `ParallelRunner`; `ThreadRunner` warns and resets to sync. |
| Select tags | `--tags` or `-t` | `tags=(...)` | A tag match is OR-style before intersection with other filters. |
| Select nodes | `--nodes` or `-n` | `node_names=(...)` | Use node names; default auto-generated names can contain commas inside brackets. |
| Start from nodes | `--from-nodes` | `from_nodes=(...)` | Includes selected nodes and their downstream dependencies. |
| Stop at nodes | `--to-nodes` | `to_nodes=(...)` | Includes selected nodes and their upstream dependencies. |
| Start from datasets | `--from-inputs` | `from_inputs=(...)` | Includes nodes directly or transitively depending on the given input datasets. |
| Stop at outputs | `--to-outputs` | `to_outputs=(...)` | Includes nodes needed to produce the given output datasets. |
| Load versioned inputs | `--load-versions` or `-lv` | `load_versions={...}` | CLI form is `dataset:version,dataset2:version2`. |
| Run one pipeline | `--pipeline` or `-p` | `pipeline_name=...` | Deprecated in favor of `--pipelines` and `pipeline_names`. |
| Run pipelines | `--pipelines` | `pipeline_names=[...]` | Comma-separated CLI names; defaults to `__default__` when omitted. |
| Select namespaces | `--namespaces` or `-ns` | `namespaces=(...)` | Selects node namespaces; use with care when dataset names are namespace-prefixed. |
| Use config file | `--config` or `-c` | Not a direct API argument | YAML keys use Python option names such as `from_nodes`, not `from-nodes`. |
| Override config source | `--conf-source` | `KedroSession.create(conf_source=...)` | Local paths must exist; remote URLs may require credentials/network. |
| Runtime params | `--params` | `KedroSession.create(runtime_params=...)` | CLI form is `key=value,nested.key=value`; avoid printing secrets. |
| Resume missing outputs | `--only-missing-outputs` | `only_missing_outputs=True` | Skips nodes whose persistent outputs already exist and are not needed by running children. |

## Slicing Rules

Kedro applies run filters through `Pipeline.filter(...)`. When multiple filters are supplied, the result is the intersection of all matching sub-pipelines, not a left-to-right chain. This makes combined flags precise but easy to overconstrain.

- `--tags=training,scoring` selects nodes that have any listed tag, then intersects with other filters.
- `--nodes=train_model,predict` selects exactly those named nodes, then intersects with other filters.
- `--from-nodes=train_model` includes `train_model` and all downstream nodes.
- `--to-nodes=report_accuracy` includes `report_accuracy` and all upstream nodes required for it.
- `--from-inputs=model_input` starts from a dataset edge and includes downstream consumers.
- `--to-outputs=metrics` includes upstream producers needed for that output.
- `--namespaces=feature_engineering` selects nodes in the namespace; pipeline-level namespaces may prefix dataset names unless inputs/outputs/parameters were explicitly exposed in the reusable pipeline.

If filtering yields no nodes, Kedro raises an error similar to `Pipeline contains no nodes after applying all provided filters`. Recheck spelling, pipeline registration, namespace prefixes, and whether combined filters overlap.

## Pipeline Selection

Use `--pipelines` for registered pipeline names returned by the project's `register_pipelines()` function.

```bash
KEDRO_DISABLE_TELEMETRY=1 kedro run --pipelines=data_processing
KEDRO_DISABLE_TELEMETRY=1 kedro run --pipelines=data_processing,data_science
```

If neither `--pipelines` nor the deprecated `--pipeline` is provided, Kedro runs the `__default__` pipeline. `--pipeline` and `--pipelines` cannot be used together. When a pipeline name is missing, `KedroSession.run()` raises a `ValueError` telling the user the pipeline must be generated and returned by `register_pipelines()`; close matches may be suggested.

## Load Versions

`--load-versions` pins one or more versioned datasets to existing saved versions:

```bash
KEDRO_DISABLE_TELEMETRY=1 kedro run \
  --load-versions=raw_customers:2024-01-01T00.00.00.000Z,model_input:2024-01-02T00.00.00.000Z
```

The CLI parser expects `dataset_name:version` pairs separated by commas. Version strings must be a single path component: not empty, not `.` or `..`, and with no `/` or `\` separators. Programmatically, pass `load_versions={"raw_customers": "2024-01-01T00.00.00.000Z"}`.

## Runtime Params

Use `--params` for runtime parameter overrides:

```bash
KEDRO_DISABLE_TELEMETRY=1 kedro run --params learning_rate=0.1,model.depth=6
```

The CLI parser splits items by comma and requires `key=value`. Nested keys use dot notation and are converted to nested dictionaries. Runtime parameters are supplied when the session is created for the standard `KedroSession` path. Treat parameter values as sensitive when they may include credentials or tokens.

## Config File Runs

A run config file lets repeated commands stay readable:

```yaml
run:
  tags: train, score
  pipelines: model_training
  runner: ParallelRunner
  node_names: train_model, evaluate_model
  env: prod
  only_missing_outputs: true
```

Run it with:

```bash
KEDRO_DISABLE_TELEMETRY=1 kedro run --config=run_config.yml
```

Use underscores in config keys because they map to Python option names. For example, use `from_nodes`, `to_outputs`, `load_versions`, `node_names`, and `only_missing_outputs`, not dashed CLI spellings. If the same value is supplied in the config file and on the command line, the command-line option takes precedence. Invalid config keys raise a CLI error with suggestions.

## Only Missing Outputs

`--only-missing-outputs` filters the selected pipeline before execution:

```bash
KEDRO_DISABLE_TELEMETRY=1 kedro run --only-missing-outputs
```

Rules to remember:

- Nodes with no outputs always run.
- A node runs when any persistent output exists in the catalog but `catalog.exists(output)` is false.
- A node runs when its output is ephemeral or missing and a downstream child is scheduled to run.
- A node can be skipped when all persistent outputs already exist and none are needed by a running child.
- Outputs not defined in the catalog behave like ephemeral memory datasets for dependency purposes.

Expected log signals include `Skipping all ... nodes (all persistent outputs exist)`, `Skipping ... nodes with existing outputs: ...`, or `Running ... out of ... nodes`. If too much is skipped, check whether persistent dataset `exists()` methods return true and whether the requested output is actually missing. If too much reruns, check for ephemeral intermediate datasets that must be recreated for a downstream missing output.

## Programmatic Execution

Use `KedroSession.run()` when code already has a bootstrapped Kedro project:

```python
from kedro.framework.session import KedroSession
from kedro.runner import SequentialRunner

with KedroSession.create(project_path=project_root, runtime_params={"learning_rate": 0.1}) as session:
    result = session.run(
        pipeline_names=["model_training"],
        tags=("train",),
        runner=SequentialRunner(is_async=True),
        load_versions={"raw_customers": "2024-01-01T00.00.00.000Z"},
        only_missing_outputs=True,
    )
```

Pass a runner instance, not `SequentialRunner` without parentheses. A `KedroSession` is one-successful-run only; create a new session for each separate successful run. `runner.run()` returns a dictionary of output dataset names to dataset objects, not raw data. Load output data through the catalog or the returned dataset objects when needed.

## Deployment-Oriented Runs

For scheduled or distributed systems, prefer parameterized runs over code changes:

```bash
KEDRO_DISABLE_TELEMETRY=1 kedro run --nodes=score_batch
KEDRO_DISABLE_TELEMETRY=1 kedro run --tags=daily
KEDRO_DISABLE_TELEMETRY=1 kedro run --pipelines=feature_engineering
```

Use stable node names and tags when a scheduler will map Kedro nodes to external tasks. Keep catalog outputs on storage visible to the scheduler workers. Platform-specific conversion to Airflow, Batch, Dask, or Spark primitives belongs to extension/deployment guidance, but runner selection and run flag construction stay here.
