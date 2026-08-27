# Automation Troubleshooting

Use this guide when ClearML pipelines, HPO, schedulers, or triggers build successfully but behave incorrectly. Start with local/debug modes and static JSON checks before launching remote work.

## Pipeline Parents And Parameter Overrides

Symptoms:

- A step starts before its input-producing step.
- A parameter override arrives as a literal `${...}` string.
- A task-template step reads old defaults instead of pipeline parameters.

Checks and fixes:

- For task-template DAGs, set `parents=["previous_step"]` when a dependency is not inferable from an artifact/model reference.
- For function steps, pass upstream returns through `function_kwargs`, for example `"${preprocess.processed_data}"`, and name returns with `function_return=["processed_data"]`.
- Use `${pipeline.<name>}` only for values registered with `PipelineController.add_parameter()`.
- Use task-template artifact URLs as `${step.artifacts.artifact_name.url}` and function-step returned objects as `${step.return_name}`.
- Use `recursively_parse_parameters=True` when references are nested inside lists, tuples, or dictionaries.
- Match parameter keys to the base task section and name, such as `General/lr`, `Args/batch_size`, or `Hydra/trainer.max_epochs`.

## Local Versus Remote Execution

Symptoms:

- Code works locally but fails on an agent.
- A decorated pipeline unexpectedly creates remote Tasks.
- A controller runs locally but steps wait forever.

Checks and fixes:

- `PipelineDecorator.debug_pipeline()` executes steps as ordinary local functions and is best for pure Python logic.
- `PipelineDecorator.run_locally()` executes steps as local subprocesses with pipeline step semantics.
- `PipelineController.start_locally(run_pipeline_steps_locally=False)` runs the controller locally while steps still follow queues.
- `PipelineController.start_locally(run_pipeline_steps_locally=True)` also runs step Tasks locally for deeper debug.
- `PipelineController.start(queue="services")` sends the controller to a service/controller queue; step queues come from `set_default_execution_queue()` or per-step `execution_queue`.
- Do not mix local-only file paths with remote steps unless the worker has the same path and data.

## Queues, Agents, And Task Types

Symptoms:

- Pipeline or HPO Tasks stay queued.
- Scheduler/trigger service never appears to run.
- Step Tasks run on the wrong machine.

Checks and fixes:

- Confirm a ClearML Agent is listening on the named queue; controller/service queues are often separate from worker queues.
- Use a service/controller queue for pipeline controllers, schedulers, triggers, and long-running orchestration.
- Use worker queues for training/evaluation steps and HPO trial jobs.
- For decorated components, set `PipelineDecorator.set_default_execution_queue("workers")`, component `execution_queue=...`, or pipeline `default_queue=...`.
- For task-template steps, use `pipe.set_default_execution_queue("workers")` and override with per-step `execution_queue` only when needed.
- Use `TaskTypes.controller`, `TaskTypes.service`, `TaskTypes.training`, `TaskTypes.data_processing`, and `TaskTypes.qc` to make task intent clear when authoring function steps or components.

## Cache And Stale Results

Symptoms:

- A step reuses old outputs after code or data changed.
- Pipeline output does not reflect new parameters.

Checks and fixes:

- Disable `cache=True` or `cache_executed_step=True` while debugging.
- Change the pipeline version or step inputs when cached outputs should be invalidated.
- Confirm all meaningful inputs are passed through `function_kwargs`, `parameter_override`, or task configuration so ClearML can compare them.
- Avoid caching steps that depend on external mutable data without a versioned dataset or immutable URI. For dataset versioning details, route to `../../data-storage/SKILL.md`.

## Package Imports And Remote Reproducibility

Symptoms:

- Remote function steps fail with import errors.
- A nested helper is missing in a remote step.
- A worker installs different packages than local development.

Checks and fixes:

- Keep function-step callables importable and top-level; avoid nested closures and lambdas.
- Put step-specific imports inside component/function step bodies so ClearML can infer per-step requirements.
- Pass `helper_functions=[...]` for standalone helpers needed by a function step.
- Use explicit `packages`, `repo`, `repo_branch`, `repo_commit`, `docker`, `docker_args`, or `working_dir` when automatic detection is insufficient.
- For direct task packaging and command-line remote launch problems, route to `../../remote-execution-cli/SKILL.md`.

## Artifacts, Models, And Data References

Symptoms:

- A downstream step cannot find an upstream artifact/model.
- HPO or task-template steps receive a storage URL where local data was expected.
- A pipeline leaks local filenames into remote workers.

Checks and fixes:

- Task-template artifacts use `${step.artifacts.name.url}`; output models use `${step.models.output.-1.url}`.
- Function-step returns use `${step.return_name}` and require `function_return=["return_name"]`.
- If step code needs to download a remote artifact, use ClearML storage/data APIs inside the step. For asset versioning and storage behavior, route to `../../data-storage/SKILL.md`.
- Do not pass machine-local temporary paths to remote steps unless they are created within that same remote step.
- For experiment artifacts logged from a step with `Task.upload_artifact()` or logger calls, route to `../../experiment-tracking/SKILL.md`.

## HPO Objective Metric Title, Series, And Sign

Symptoms:

- HPO starts jobs but reports no objective.
- The wrong trial is considered best.
- `clearml-param-search` rejects the objective sign.

Checks and fixes:

- Match `objective_metric_title` and `objective_metric_series` exactly to `Logger.report_scalar(title=..., series=...)` in the base task.
- Use `min` for lower final loss, `max` for higher final accuracy, `min_global` for the lowest value over all iterations, and `max_global` for the highest value over all iterations.
- For multi-objective Python HPO, pass title, series, and sign as lists of equal length and use an optimizer backend that supports multi-objective search.
- Ensure each trial reports the objective scalar before stopping; jobs without the scalar cannot rank correctly.

## HPO Parameter JSON

Symptoms:

- `clearml-param-search` exits before launching.
- JSON is accepted by a shell but rejected by the CLI.
- Search parameters do not affect the training code.

Checks and fixes:

- Validate with `python scripts/hpo_search_space_check.py --params-search ... --objective-sign ...` before launching.
- Quote each `--params-search` and `--params-override` JSON object as one shell argument.
- Use supported search types: `UniformParameterRange`, `UniformIntegerParameterRange`, `LogUniformParameterRange`, and `DiscreteParameterRange`.
- Use numeric `min_value`/`max_value`; require integer values for `UniformIntegerParameterRange`; require a non-empty `values` list for `DiscreteParameterRange`.
- Prefer explicit names with sections. The CLI prefixes names without `/` as `General/<name>`, which may miss parameters stored under `Args/`, `Hydra/`, or another section.
- Use `--params-override` for fixed values and `--args key=value` only for script arguments in CLI launch mode.

## Scheduler Recurring Time Validation

Symptoms:

- `TaskScheduler.add_task()` raises a time validation error.
- A job runs more often or less often than expected.

Checks and fixes:

- Times are UTC, not local wall-clock time.
- `minute=15` means every 15 minutes.
- `hour=1, minute=30` means every hour at minute 30.
- `day=1, hour=22, minute=30` means every day at 22:30 UTC.
- `weekdays` values must be lowercase full names: `monday` through `sunday`.
- If `weekdays` is used with `day`, `day` must be `None`, `0`, or `1`.
- `task_parameters` and `task_overrides` cannot be used with `reuse_task=True`.
- `start()` does not return; run scheduler services in an appropriate service context.

## Trigger Filters And Duplicate Launches

Symptoms:

- A trigger never fires.
- A trigger fires repeatedly for the same model/dataset/task.
- A metric threshold trigger fires in the wrong direction.

Checks and fixes:

- Match `trigger_project`, `trigger_name`, tags, required tags, status, metric, and variant filters to actual ClearML objects.
- For task metric triggers, `trigger_on_metric` is the scalar title and `trigger_on_variant` is the series.
- Use `trigger_on_sign="max"` or `"maximum"` for above-threshold events and `"min"` or `"minimum"` for below-threshold events.
- Use `single_instance=True` and trigger tags to reduce duplicate launches.
- `schedule_function` receives a single ID and runs in the trigger service process; `schedule_task_id` launches a ClearML Task on `schedule_queue`.
- `start()` and `start_remotely()` are long-running service actions and should not be called during static code generation.

## Callback Failures

Symptoms:

- A callback prevents a step from running.
- A retry loop never stops.
- Callback code works locally but fails remotely.

Checks and fixes:

- `pre_execute_callback(pipeline, node, parameters)` must return `True` to continue; returning `False` skips the node and dependent subtree.
- `post_execute_callback(pipeline, node)` should not raise; catch/report non-critical errors inside the callback.
- `status_change_callback(pipeline, node, previous_status)` should be lightweight and side-effect safe.
- `retry_on_failure(pipeline, node, retries)` should have a clear finite condition such as `return retries < 2`.
- Keep callback functions importable and available wherever the controller runs.
