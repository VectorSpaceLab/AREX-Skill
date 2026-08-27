# Automation API Reference

This reference covers ClearML `2.1.9` automation APIs that are relevant to pipeline controllers, decorated pipelines, hyperparameter search, schedulers, triggers, and automation CLI use.

## Imports

```python
from clearml import PipelineController, PipelineDecorator, TaskTypes
from clearml.automation import (
    DiscreteParameterRange,
    GridSearch,
    HyperParameterOptimizer,
    LogUniformParameterRange,
    RandomSearch,
    TaskScheduler,
    TriggerScheduler,
    UniformIntegerParameterRange,
    UniformParameterRange,
)
```

`PipelineController` and `PipelineDecorator` are also exported from `clearml`. HPO strategies and scheduling helpers are exported from `clearml.automation`.

## PipelineController

`PipelineController` builds a pipeline controller Task that owns a DAG of cloned ClearML Tasks or function-created step Tasks.

```python
PipelineController(
    name: str,
    project: str,
    version: str | None = None,
    pool_frequency: float = 0.2,
    add_pipeline_tags: bool = False,
    target_project: str | bool | None = True,
    auto_version_bump: bool | None = None,
    abort_on_failure: bool = False,
    add_run_number: bool = True,
    retry_on_failure: int | callable | None = None,
    docker: str | None = None,
    docker_args: str | None = None,
    docker_bash_setup_script: str | None = None,
    packages: bool | str | list[str] | None = None,
    repo: str | None = None,
    repo_branch: str | None = None,
    repo_commit: str | None = None,
    always_create_from_code: bool = True,
    artifact_serialization_function: callable | None = None,
    artifact_deserialization_function: callable | None = None,
    output_uri: str | bool | None = None,
    skip_global_imports: bool = False,
    working_dir: str | None = None,
    enable_local_imports: bool = True,
)
```

Key setup methods:

```python
pipe.set_default_execution_queue(default_execution_queue: str | None) -> None
pipe.set_pipeline_execution_time_limit(max_execution_minutes: float | None) -> None
pipe.add_parameter(name: str, default=None, description=None, param_type=None) -> None
pipe.get_parameters() -> dict
```

Decision notes:

- `name`, `project`, and optionally `version` identify the pipeline controller Task/template.
- `pool_frequency` is in minutes and controls monitoring cadence.
- `target_project=True` lets ClearML place cloned step Tasks under the pipeline-related project; pass a string to force a project, `False`/`None` to avoid target-project rewriting.
- `abort_on_failure=True` stops the entire pipeline immediately on a step failure; default behavior can continue independent branches but still mark the pipeline failed unless a failed node is configured to continue.
- `packages`, `repo`, `docker`, and `working_dir` are remote reproducibility controls for function-created steps and controller execution.
- Pipeline parameters live under the pipeline Task's `Pipeline` hyperparameter section and are referenced as `${pipeline.<name>}`.

## Task-Based DAG Steps

Use `add_step()` when the step is an existing ClearML Task template to clone/enqueue.

```python
pipe.add_step(
    name: str,
    base_task_id: str | None = None,
    parents: list[str] | None = None,
    parameter_override: dict | None = None,
    configuration_overrides: dict | None = None,
    task_overrides: dict | None = None,
    execution_queue: str | None = None,
    monitor_metrics: list[tuple] | None = None,
    monitor_artifacts: list[str | tuple[str, str]] | None = None,
    monitor_models: list[str | tuple[str, str]] | None = None,
    time_limit: float | None = None,
    base_task_project: str | None = None,
    base_task_name: str | None = None,
    clone_base_task: bool = True,
    continue_on_fail: bool = False,
    pre_execute_callback: callable | None = None,
    post_execute_callback: callable | None = None,
    cache_executed_step: bool = False,
    base_task_factory: callable | None = None,
    retry_on_failure: int | callable | None = None,
    status_change_callback: callable | None = None,
    recursively_parse_parameters: bool = False,
    output_uri: str | bool | None = None,
    continue_behaviour: dict | None = None,
    stage: str | None = None,
) -> bool
```

Important `parameter_override` references:

- `${pipeline.<param>}` for a controller parameter created with `add_parameter()`.
- `${<step>.id}` for a previously executed step Task ID.
- `${<step>.artifacts.<artifact_name>.url}` for output artifact URLs.
- `${<step>.models.output.-1.url}` for the latest output model URL.
- `${<step>.parameters.<section>/<name>}` for a step parameter.

Use `recursively_parse_parameters=True` when references are nested inside lists, tuples, or dictionaries. Use `configuration_overrides` for Task configuration objects and `task_overrides` for task metadata such as script branch, commit, Docker image, or requirements.

Callback signatures:

```python
def pre_execute_callback(pipeline, node, parameters) -> bool: ...
def post_execute_callback(pipeline, node) -> None: ...
def status_change_callback(pipeline, node, previous_status: str) -> None: ...
def retry_on_failure(pipeline, node, retries: int) -> bool: ...
```

Return `False` from `pre_execute_callback` to skip a node and its dependent subtree.

## Function-Based DAG Steps

Use `add_function_step()` when the step is a Python function and ClearML should create step Tasks from code.

```python
pipe.add_function_step(
    name: str,
    function: callable,
    function_kwargs: dict | None = None,
    function_return: list[str] | None = None,
    project_name: str | None = None,
    task_name: str | None = None,
    task_type: str | None = None,
    auto_connect_frameworks: dict | None = None,
    auto_connect_arg_parser: dict | None = None,
    packages: bool | str | list[str] | None = None,
    repo: str | None = None,
    repo_branch: str | None = None,
    repo_commit: str | None = None,
    helper_functions: list[callable] | None = None,
    docker: str | None = None,
    docker_args: str | None = None,
    docker_bash_setup_script: str | None = None,
    parents: list[str] | None = None,
    execution_queue: str | None = None,
    monitor_metrics: list[tuple] | None = None,
    monitor_artifacts: list[str | tuple] | None = None,
    monitor_models: list[str | tuple] | None = None,
    time_limit: float | None = None,
    continue_on_fail: bool = False,
    pre_execute_callback: callable | None = None,
    post_execute_callback: callable | None = None,
    cache_executed_step: bool = False,
    retry_on_failure: int | callable | None = None,
    status_change_callback: callable | None = None,
    tags: str | list[str] | None = None,
    output_uri: str | bool | None = None,
    draft: bool | None = False,
    working_dir: str | None = None,
    continue_behaviour: dict | None = None,
    stage: str | None = None,
) -> bool
```

Function-step rules:

- `function` should be importable/global, not a nested closure.
- Put remote-only imports inside the function so per-step dependency detection sees them.
- `function_kwargs` exposes input values or artifact references; ClearML can infer parents from artifact references such as `${preprocess.processed_data}`.
- `function_return` names returned artifacts. If it is omitted, returned values are not stored as artifacts.
- `helper_functions` supplies extra functions available to the standalone step code.

## Starting And Debugging Pipelines

```python
pipe.start(queue: str = "services", wait: bool = True) -> bool
pipe.start_locally(run_pipeline_steps_locally: bool = False) -> None
```

- `start()` serializes the pipeline and executes the controller remotely, usually on a service/controller queue.
- `start_locally(False)` runs the controller process locally but step Tasks still follow their configured queues.
- `start_locally(True)` also executes step Tasks locally as subprocesses for debugging, using local code rather than remote git state.
- A remote pipeline controller requires a controller Task; construct from code or ensure the controller Task exists before starting.

## PipelineDecorator

`PipelineDecorator` converts ordinary function calls into pipeline DAG nodes.

```python
@PipelineDecorator.component(
    return_values: str | list[str] = ("return_object",),
    name: str | None = None,
    cache: bool = False,
    packages: bool | str | list[str] | None = None,
    parents: list[str] | None = None,
    execution_queue: str | None = None,
    continue_on_fail: bool = False,
    docker: str | None = None,
    docker_args: str | None = None,
    docker_bash_setup_script: str | None = None,
    task_type: str | None = None,
    auto_connect_frameworks: dict | None = None,
    auto_connect_arg_parser: dict | None = None,
    repo: str | None = None,
    repo_branch: str | None = None,
    repo_commit: str | None = None,
    helper_functions: list[callable] | None = None,
    monitor_metrics: list[tuple] | None = None,
    monitor_artifacts: list[str | tuple[str, str]] | None = None,
    monitor_models: list[str | tuple[str, str]] | None = None,
    retry_on_failure: int | callable | None = None,
    pre_execute_callback: callable | None = None,
    post_execute_callback: callable | None = None,
    status_change_callback: callable | None = None,
    tags: str | list[str] | None = None,
    output_uri: str | bool | None = None,
    draft: bool | None = False,
    working_dir: str | None = None,
    continue_behaviour: dict | None = None,
    stage: str | None = None,
)
def step(...): ...
```

```python
@PipelineDecorator.pipeline(
    name: str,
    project: str,
    version: str | None = None,
    return_value: str | None = None,
    default_queue: str | None = None,
    pool_frequency: float = 0.2,
    add_pipeline_tags: bool = False,
    target_project: str | None = None,
    abort_on_failure: bool = False,
    pipeline_execution_queue: str | None = "services",
    multi_instance_support: bool | str = False,
    add_run_number: bool = True,
    args_map: dict[str, list[str]] | None = None,
    start_controller_locally: bool = False,
    retry_on_failure: int | callable | None = None,
    docker: str | None = None,
    docker_args: str | None = None,
    docker_bash_setup_script: str | None = None,
    packages: bool | str | list[str] | None = None,
    repo: str | None = None,
    repo_branch: str | None = None,
    repo_commit: str | None = None,
    artifact_serialization_function: callable | None = None,
    artifact_deserialization_function: callable | None = None,
    output_uri: str | bool | None = None,
    skip_global_imports: bool = False,
    working_dir: str | None = None,
    enable_local_imports: bool = True,
)
def pipeline(...): ...
```

Class helpers:

```python
PipelineDecorator.set_default_execution_queue(queue: str | None) -> None
PipelineDecorator.run_locally() -> None
PipelineDecorator.debug_pipeline() -> None
PipelineDecorator.get_current_pipeline() -> PipelineDecorator
PipelineDecorator.wait_for_multi_pipelines() -> list
```

Decision notes:

- `run_locally()` executes pipeline steps as local subprocesses; it still creates pipeline/step task semantics.
- `debug_pipeline()` executes the DAG locally as plain functions and does not create step Tasks.
- `pipeline_execution_queue=None` means the pipeline logic runs locally while steps can still run remotely unless local/debug helpers are enabled.
- `start_controller_locally=True` keeps the decorated controller on the local machine.
- `multi_instance_support='parallel'` allows parallel calls and returns results through `wait_for_multi_pipelines()`.

## HyperParameterOptimizer

`HyperParameterOptimizer` clones a base task, changes parameters, launches jobs, and ranks them by a scalar objective.

```python
HyperParameterOptimizer(
    base_task_id: str,
    hyper_parameters: list[Parameter],
    objective_metric_title: str | list[str],
    objective_metric_series: str | list[str],
    objective_metric_sign: str | list[str] = "min",
    optimizer_class=RandomSearch,
    max_number_of_concurrent_tasks: int = 10,
    execution_queue: str = "default",
    optimization_time_limit: float | None = None,
    compute_time_limit: float | None = None,
    auto_connect_task: bool | Task = True,
    always_create_task: bool = False,
    spawn_project: str | None = None,
    save_top_k_tasks_only: int | None = None,
    **optimizer_kwargs,
)
```

Lifecycle:

```python
optimizer.start(job_complete_callback=None) -> bool
optimizer.start_locally(job_complete_callback=None) -> bool
optimizer.wait(timeout: float | None = None) -> bool
optimizer.stop(timeout: float | None = None, wait_for_reporter: bool = True) -> None
optimizer.set_report_period(report_period_minutes: float) -> None
optimizer.get_top_experiments(top_k: int = 3) -> list
```

Callback signature:

```python
def job_complete_callback(job_id, objective_value, objective_iteration, job_parameters, top_performance_job_id): ...
```

Objective rules:

- `objective_metric_title` and `objective_metric_series` must match the exact title and series passed to `Logger.report_scalar(title=..., series=...)` in the base task.
- `objective_metric_sign` supports `min`, `max`, `min_global`, and `max_global`.
- For multi-objective optimization, title, series, and sign must all be lists with the same length and require the Optuna optimizer backend.

## Parameter Range Classes

```python
UniformParameterRange(name: str, min_value: float, max_value: float, step_size: float | None = None, include_max_value: bool = True)
UniformIntegerParameterRange(name: str, min_value: int, max_value: int, step_size: int = 1, include_max_value: bool = True)
DiscreteParameterRange(name: str, values: list | tuple = ())
LogUniformParameterRange(name: str, min_value: float, max_value: float, base: float = 10, step_size: float | None = None, include_max_value: bool = True)
```

Naming note: CLI-created HPO parameters without a slash are prefixed with `General/`. In Python, pass the full ClearML hyperparameter name explicitly when targeting a non-`General` section, such as `Args/lr` or `Hydra/optimizer.lr`.

## TaskScheduler

`TaskScheduler` is a service-style loop for recurring or one-shot task/function launches. Times are UTC.

```python
TaskScheduler(
    sync_frequency_minutes: float = 15,
    force_create_task_name: str | None = None,
    force_create_task_project: str | None = None,
)
```

```python
scheduler.add_task(
    schedule_task_id: str | Task | None = None,
    schedule_function: callable | None = None,
    queue: str | None = None,
    name: str | None = None,
    target_project: str | None = None,
    minute: int | None = None,
    hour: int | None = None,
    day: int | None = None,
    weekdays: list[str] | None = None,
    month: int | None = None,
    year: int | None = None,
    limit_execution_time: float | None = None,
    single_instance: bool = False,
    recurring: bool = True,
    execute_immediately: bool = False,
    reuse_task: bool = False,
    task_parameters: dict | None = None,
    task_overrides: dict | None = None,
) -> bool
scheduler.get_scheduled_tasks() -> list
scheduler.remove_task(task_id: str | Task | callable) -> bool
scheduler.start() -> None
scheduler.start_remotely(queue="services")
```

Scheduling semantics:

- A lone `minute=15` means every 15 minutes.
- `hour=1, minute=30` means every hour at minute 30.
- `day=1, hour=22, minute=30` means every day at 22:30 UTC.
- `weekdays` accepts lowercase day names: `monday` through `sunday`.
- If `weekdays` is used with `day`, `day` must be `None`, `0`, or `1`.
- `schedule_function` runs in the scheduler process; `schedule_task_id` clones/enqueues a ClearML Task.
- `task_parameters` and `task_overrides` are not available with `reuse_task=True`.

## TriggerScheduler

`TriggerScheduler` is a polling service for model, dataset, and task events.

```python
TriggerScheduler(
    pooling_frequency_minutes: float = 3.0,
    sync_frequency_minutes: float = 15,
    force_create_task_name: str | None = None,
    force_create_task_project: str | None = None,
)
```

Model triggers:

```python
trigger.add_model_trigger(
    schedule_task_id: str | Task | None = None,
    schedule_queue: str | None = None,
    schedule_function: callable[[str], None] | None = None,
    trigger_project: str | None = None,
    trigger_name: str | None = None,
    trigger_on_publish: bool | None = None,
    trigger_on_tags: list[str] | None = None,
    trigger_on_archive: bool | None = None,
    trigger_required_tags: list[str] | None = None,
    name: str | None = None,
    target_project: str | None = None,
    add_tag: bool | str = True,
    single_instance: bool = False,
    reuse_task: bool = False,
    task_parameters: dict | None = None,
    task_overrides: dict | None = None,
) -> None
```

Dataset triggers use the same arguments as model triggers and pass `dataset_id` to `schedule_function`. Task triggers add task-specific filters:

```python
trigger.add_task_trigger(
    schedule_task_id: str | Task | None = None,
    schedule_queue: str | None = None,
    schedule_function: callable[[str], None] | None = None,
    trigger_project: str | None = None,
    trigger_name: str | None = None,
    trigger_on_tags: list[str] | None = None,
    trigger_on_status: list[str] | None = None,
    trigger_exclude_dev_tasks: bool | None = None,
    trigger_on_metric: str | None = None,
    trigger_on_variant: str | None = None,
    trigger_on_threshold: float | None = None,
    trigger_on_sign: str | None = None,
    trigger_required_tags: list[str] | None = None,
    name: str | None = None,
    target_project: str | None = None,
    add_tag: bool | str = True,
    single_instance: bool = False,
    reuse_task: bool = False,
    task_parameters: dict | None = None,
    task_overrides: dict | None = None,
) -> None
trigger.get_triggers() -> list
trigger.start() -> None
trigger.start_remotely(queue="services")
```

Trigger notes:

- `schedule_function` receives one ID: `model_id`, `dataset_id`, or `task_id`.
- `task_overrides` can reference `${model.id}`, `${dataset.id}`, or `${task.id}` depending on trigger type.
- `trigger_on_sign` accepts `max`/`maximum` for above-threshold and `min`/`minimum` for below-threshold task metric triggers.
- Trigger and scheduler `start()` methods do not return; run them as services or remote service Tasks for production use.
