# Execution Troubleshooting

Use this reference when `kedro run`, `KedroSession.run()`, or a runner fails, skips unexpected nodes, or behaves differently under concurrency. Prefer diagnosing with `SequentialRunner` first, then reintroduce slicing, async mode, and concurrent runners one change at a time.

## Quick Triage

1. Set telemetry opt-out for automated reruns: `KEDRO_DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1`.
2. Confirm the command is running inside a Kedro project or that programmatic code called the project bootstrap/session setup. Route project detection issues to `../project-cli-and-sessions/SKILL.md`.
3. Re-run the smallest meaningful slice with `--runner=SequentialRunner`.
4. If the failure mentions missing datasets, credentials, catalog factories, versioned datasets, or config loading, route to `../data-catalog-and-config/SKILL.md`.
5. If the failure mentions invalid node names, tags, namespaces, duplicate outputs, or empty slices, route graph analysis to `../pipelines-and-nodes/SKILL.md`.
6. If hooks or plugins are involved, check whether the selected runner supports the needed hook behavior and route implementation details to `../hooks-and-extensions/SKILL.md`.

## Error and Signal Map

| Signal | Likely cause | Fix |
| --- | --- | --- |
| `Pipeline contains no nodes` | Empty default pipeline, no registered nodes, or filters removed everything. | Check `register_pipelines()`, selected `--pipelines`, and overlapping filter flags. |
| `Pipeline contains no nodes after applying all provided filters` | Combined `--tags`, `--nodes`, `--from-*`, `--to-*`, or `--namespaces` filters do not intersect. | Test one filter at a time; verify exact node/tag/namespace/dataset names. |
| `Failed to find the pipeline named ...` | `--pipelines` name is not returned by `register_pipelines()`. | Use a registered name or add the pipeline to the registry. |
| `Options '--pipeline' and '--pipelines' cannot be used together` | Deprecated single-pipeline flag combined with the current multi-pipeline flag. | Use only `--pipelines=<name>` or `--pipelines=name1,name2`. |
| `KedroSession expect an instance of Runner instead of a class` | Programmatic code passed `SequentialRunner` instead of `SequentialRunner()`. | Instantiate the runner before passing it to `KedroSession.run()`. |
| `A run has already been completed as part of the active KedroSession` | Reusing a session after a successful run. | Create a new `KedroSession` per successful run. |
| `Pipeline input(s) ... not found in the DataCatalog` | Required external input is absent from the catalog or namespace prefix changed the dataset name. | Add the catalog entry, expose/remap namespaced inputs, or correct the slice. |
| `Data for MemoryDataset has not been saved yet` | A memory dataset exists in the catalog but no value was saved before the run. | Save the value first, make it a real persisted dataset, or run upstream producer nodes. |
| `Saving 'None' to a 'Dataset' is not allowed` | Node returned `None` for an output dataset. | Fix the node function to return a value for each declared output or declare no output. |
| `The following nodes cannot be serialised` | `ParallelRunner` saw lambdas, nested functions, closures, or decorators without `functools.wraps`. | Use top-level importable functions and properly wrapped decorators, or use `ThreadRunner`/`SequentialRunner`. |
| `The following datasets cannot be used with multiprocessing` | Dataset is single-process-only or not serializable for `ParallelRunner`. | Use a process-safe dataset, `SharedMemoryDataCatalog`, or a non-process runner. |
| `max_workers should be positive` | `ThreadRunner` or `ParallelRunner` was created with `max_workers <= 0`. | Pass a positive integer or `None`. |
| `ThreadRunner doesn't support loading and saving ... asynchronously` | `ThreadRunner(is_async=True)` or `kedro run --runner=ThreadRunner --async`. | Remove `--async`; choose `SequentialRunner` or `ParallelRunner` if async load/save is required. |
| Node/dataset hooks do not fire under multiprocessing | `ParallelRunner` does not execute node/dataset hooks in worker processes. | Use `SequentialRunner` or `ThreadRunner`; keep only pipeline-level hooks around a `ParallelRunner` run. |
| Spark datasets fail or behave unexpectedly under `ParallelRunner` | Spark objects and sessions do not fit multiprocessing expectations. | Use `ThreadRunner` for Spark workflows. |
| `Expected the form of 'load_versions' ...` | Invalid `--load-versions` syntax. | Use `dataset_name:YYYY-MM-DDThh.mm.ss.sssZ` pairs separated by commas. |
| `Version string ... is not allowed` | Version contains a path separator, is empty, or is `.`/`..`. | Use a single safe version component. |
| `Invalid format of params option` | `--params` item lacks `=` or has an empty key. | Use `key=value` and `nested.key=value` forms. |
| `Key ... in provided configuration is not valid` | Run config YAML uses a bad key or dashed CLI spelling. | Use Python option names such as `from_nodes`, `node_names`, and `only_missing_outputs`. |

## Missing Inputs and Namespaces

A common namespace failure is a catalog entry named `Input1` while the namespaced pipeline expects `test.Input1`. Kedro reports the prefixed name in the missing-input error.

Fix by choosing one of these approaches:

- Add a catalog entry for the fully prefixed dataset name, such as `test.Input1`.
- Expose the input when creating the reusable pipeline so Kedro does not prefix it.
- Correct the selected namespace or pipeline slice if the wrong namespaced branch is running.
- Route reusable pipeline namespace design to `../pipelines-and-nodes/SKILL.md` and catalog entry updates to `../data-catalog-and-config/SKILL.md`.

## Empty or Unexpected Slices

Kedro intersects all supplied filter conditions. A command such as this can be empty if the selected nodes are not inside the selected namespace or do not have the selected tag:

```bash
KEDRO_DISABLE_TELEMETRY=1 kedro run \
  --pipelines=model_training \
  --tags=train \
  --nodes=evaluate_model \
  --namespaces=feature_engineering
```

Debug by running in this order:

```bash
KEDRO_DISABLE_TELEMETRY=1 kedro run --pipelines=model_training
KEDRO_DISABLE_TELEMETRY=1 kedro run --pipelines=model_training --tags=train
KEDRO_DISABLE_TELEMETRY=1 kedro run --pipelines=model_training --nodes=evaluate_model
```

If each individual filter works but the combination fails, the filters do not overlap. Use `Pipeline.describe()` or graph inspection from `../pipelines-and-nodes/SKILL.md` to confirm exact node names and tags.

## Resume and Missing Outputs

When a node fails after earlier nodes succeeded, Kedro logs a resume suggestion when it can infer persisted inputs:

```bash
KEDRO_DISABLE_TELEMETRY=1 kedro run --from-nodes "node_a,node_b"
```

The suggestion is conservative: it starts from the nearest nodes whose required inputs are persisted or can be recreated. If no nodes ran, Kedro warns to repeat the previous command.

`--only-missing-outputs` is different from failure resume. It filters the selected pipeline before execution based on persistent output existence. Troubleshoot with log messages:

- `Skipping all ... nodes (all persistent outputs exist)` means every required persistent output already exists.
- `Skipping ... nodes with existing outputs: ...` means those nodes' persistent outputs exist and are not needed by running children.
- `Running ... out of ... nodes` means missing persistent outputs or ephemeral dependencies require a subset to run.

If `--only-missing-outputs` skips work that should rerun, delete or invalidate the relevant persistent outputs, check dataset `exists()` behavior, or run a narrower explicit slice. If it reruns upstream work, check whether intermediate datasets are ephemeral/memory datasets that must be recreated for downstream missing outputs.

## ParallelRunner Serialization Failures

`ParallelRunner` uses multiprocessing and validates nodes and catalog entries before execution. Common fixes:

- Replace lambdas and nested functions with top-level functions importable from a module.
- Wrap custom decorators with `functools.wraps()` so Kedro can serialize the original callable metadata.
- Avoid passing open file handles, active clients, locks, generators, or unpickleable objects through memory datasets.
- Use `SharedMemoryDataCatalog` when calling `ParallelRunner` directly; the CLI/session path selects it automatically.
- Switch to `ThreadRunner` if the workload needs shared process state, Spark sessions, node/dataset hooks, or non-pickleable clients.
- Set `KEDRO_MP_CONTEXT=spawn` for safer process startup when libraries manage internal threads, while remembering that `spawn` is stricter about importability.

## Async I/O Problems

Async mode loads inputs and saves outputs with threads around node execution. It is useful when nodes have multiple expensive inputs or outputs and datasets are thread-safe.

Do not use async mode when datasets or clients are not thread-safe. Symptoms include race conditions, intermittent client errors, corrupt writes, or missing data after a successful-looking run. Disable `--async` first, then debug the dataset implementation or move to a safer runner.

`ThreadRunner` already uses threads for node concurrency and does not support async load/save; Kedro warns and sets async to false.

## CLI Config and Runtime Parameter Mistakes

For `kedro run --config=run_config.yml`, YAML keys must match Python option names:

```yaml
run:
  from_nodes: train_model
  to_outputs: metrics
  load_versions: raw_data:2024-01-01T00.00.00.000Z
  only_missing_outputs: true
```

Do not use dashed keys such as `from-nodes` or `only-missing-outputs` in YAML. CLI options override config-file values when both are supplied.

For `--params`, use equals signs:

```bash
KEDRO_DISABLE_TELEMETRY=1 kedro run --params model.learning_rate=0.1,batch_size=64
```

If parameters include secrets, move them to credentials/config handling and avoid printing them in command logs.

## Optional Dependency Confusion

Core Kedro runners are available from the base `kedro` package. Failures around concrete datasets, Spark, notebooks, server, or platform plugins usually come from optional dependencies or separate packages, not from runner imports.

- `from kedro.runner import SequentialRunner, ThreadRunner, ParallelRunner` should work with base Kedro.
- `kedro-datasets` implementations, Spark integrations, and deployment plugins may require separate installs.
- Route dataset import errors to `../data-catalog-and-config/SKILL.md` and plugin/deployment extension errors to `../hooks-and-extensions/SKILL.md`.

## Safe Escalation Pattern

When a complex run fails and the root cause is unclear:

1. Run `kedro run --runner=SequentialRunner` without `--async`.
2. Add `--pipelines` or one slice flag at a time.
3. Add `--only-missing-outputs` only after confirming persistent dataset `exists()` behavior.
4. Add `--runner=ThreadRunner` for shared-process concurrency.
5. Add `--runner=ParallelRunner` only after serialization and hook constraints are acceptable.
6. Add `--async` last for `SequentialRunner` or `ParallelRunner` after confirming dataset thread safety.
