# Automation Workflow Recipes

Use these recipes with the verified signatures in [API reference](api-reference.md). They are safe authoring patterns only; do not start remote pipelines, optimizers, schedulers, or triggers unless the user confirms a configured ClearML server, credentials, queues, and execution target.

## Choose The Workflow Shape

- Use `PipelineDecorator` when the user already has Python functions and wants function calls converted into a DAG.
- Use `PipelineController.add_function_step()` when the user wants explicit DAG nodes from Python functions, named return artifacts, per-step queues, callbacks, retries, or cache flags.
- Use `PipelineController.add_step()` when the user already has ClearML Task templates and wants to clone/enqueue them as steps.
- Use `HyperParameterOptimizer` or `clearml-param-search` when a base task or script should be cloned over parameter ranges and ranked by scalar metrics.
- Use `TaskScheduler` for recurring time-based launches and `TriggerScheduler` for model, dataset, or task events.

For detailed experiment logging inside step bodies, route to `../../experiment-tracking/SKILL.md`. For dataset versioning or storage assets, route to `../../data-storage/SKILL.md`. For direct `clearml-task` launches outside pipeline/HPO orchestration, route to `../../remote-execution-cli/SKILL.md`. For HTTP routers or service endpoints, route to `../../routers-services/SKILL.md`.

## Function Pipeline With PipelineDecorator

Use decorators for a readable preprocessing/training/evaluation flow. Put remote-only imports inside component functions so ClearML records per-step package requirements.

```python
from clearml import TaskTypes
from clearml.automation import PipelineDecorator

@PipelineDecorator.component(
    name="preprocess",
    return_values=["processed_data"],
    cache=True,
    task_type=TaskTypes.data_processing,
    execution_queue="workers",
)
def preprocess(raw_uri: str):
    return {"raw_uri": raw_uri}

@PipelineDecorator.component(
    name="train",
    return_values=["model"],
    task_type=TaskTypes.training,
    execution_queue="workers",
)
def train(processed_data, learning_rate: float = 0.01):
    return {"model": "trained", "params": {"learning_rate": learning_rate}}

@PipelineDecorator.component(
    name="evaluate",
    return_values=["metrics"],
    task_type=TaskTypes.qc,
    execution_queue="workers",
)
def evaluate(model):
    return {"accuracy": 0.0}

@PipelineDecorator.pipeline(
    name="daily-training",
    project="automation",
    version="0.1.0",
    default_queue="workers",
    pipeline_execution_queue="services",
)
def training_pipeline(raw_uri: str, learning_rate: float = 0.01):
    processed = preprocess(raw_uri)
    model = train(processed, learning_rate=learning_rate)
    metrics = evaluate(model)
    print("metrics", metrics)
```

Local and remote execution choices:

- `PipelineDecorator.debug_pipeline()` runs the DAG locally as plain function calls; use it first to debug Python logic without remote step Tasks.
- `PipelineDecorator.run_locally()` runs pipeline steps as local subprocesses with ClearML step semantics; use it when debugging serialization and step boundaries locally.
- Without those helpers, calling the decorated pipeline creates/uses pipeline automation semantics; `pipeline_execution_queue="services"` controls the controller, while component `execution_queue` or `default_queue` controls worker steps.
- Pass `pipeline_execution_queue=None` or `start_controller_locally=True` only when the controller should stay in the current process while steps still follow their queue/debug settings.

Typical main block:

```python
if __name__ == "__main__":
    # Pick one local debugging mode while developing.
    # PipelineDecorator.debug_pipeline()
    # PipelineDecorator.run_locally()
    training_pipeline(raw_uri="dataset-or-file-reference", learning_rate=0.01)
```

## Task-Template DAG With PipelineController.add_step

Use task-template DAGs when the steps already exist as ClearML Tasks and the pipeline should clone them, override parameters/configuration, and pass artifacts between them.

```python
from clearml.automation import PipelineController

pipe = PipelineController(
    project="automation",
    name="task-template-pipeline",
    version="0.1.0",
    abort_on_failure=True,
    add_pipeline_tags=False,
)
pipe.set_default_execution_queue("workers")
pipe.add_parameter(name="raw_uri", default="dataset-or-file-reference", description="Input data reference")
pipe.add_parameter(name="test_size", default=0.2, description="Validation split fraction")

pipe.add_step(
    name="preprocess",
    base_task_project="templates",
    base_task_name="preprocess-template",
    parameter_override={"General/raw_uri": "${pipeline.raw_uri}"},
    cache_executed_step=True,
)
pipe.add_step(
    name="train",
    parents=["preprocess"],
    base_task_project="templates",
    base_task_name="train-template",
    parameter_override={
        "General/input_uri": "${preprocess.artifacts.processed_data.url}",
        "General/test_size": "${pipeline.test_size}",
    },
    recursively_parse_parameters=True,
)
pipe.add_step(
    name="evaluate",
    parents=["train"],
    base_task_project="templates",
    base_task_name="evaluate-template",
    parameter_override={"General/model_uri": "${train.models.output.-1.url}"},
)

# Development: pipe.start_locally(run_pipeline_steps_locally=False)
# Full local subprocess debug: pipe.start_locally(run_pipeline_steps_locally=True)
# Remote controller: pipe.start(queue="services", wait=True)
```

Interpolation references that future agents should reuse:

- `${pipeline.<name>}` for values created with `add_parameter()`.
- `${<step>.id}` for the executed step Task ID.
- `${<step>.artifacts.<artifact_name>.url}` for a task-template step artifact URL.
- `${<step>.models.output.-1.url}` for the latest output model URL.
- `${<step>.parameters.<section>/<name>}` for a step parameter value.
- Use `recursively_parse_parameters=True` when references are nested inside lists, tuples, or dictionaries.

Callbacks and retries:

```python
def pre_execute_callback(pipeline, node, parameters):
    return True  # return False to skip this node and its dependent subtree

def post_execute_callback(pipeline, node):
    print("completed", node.name, node.executed)

def retry_on_failure(pipeline, node, retries):
    return retries < 2
```

Attach these with `pre_execute_callback=...`, `post_execute_callback=...`, `status_change_callback=...`, or `retry_on_failure=...` on individual steps or controller defaults.

## Function Steps With PipelineController.add_function_step

Use `add_function_step()` when the user wants explicit DAG construction but does not have pre-existing task templates.

```python
from clearml import TaskTypes
from clearml.automation import PipelineController

def preprocess(raw_uri: str):
    return {"raw_uri": raw_uri}

def train(processed_data, learning_rate: float):
    return {"model": "trained", "learning_rate": learning_rate}

def evaluate(model):
    return {"accuracy": 0.0}

pipe = PipelineController(project="automation", name="function-step-pipeline", version="0.1.0")
pipe.set_default_execution_queue("workers")
pipe.add_parameter(name="raw_uri", default="dataset-or-file-reference")
pipe.add_parameter(name="learning_rate", default=0.01)
pipe.add_function_step(
    name="preprocess",
    function=preprocess,
    function_kwargs={"raw_uri": "${pipeline.raw_uri}"},
    function_return=["processed_data"],
    task_type=TaskTypes.data_processing,
    cache_executed_step=True,
)
pipe.add_function_step(
    name="train",
    function=train,
    function_kwargs={
        "processed_data": "${preprocess.processed_data}",
        "learning_rate": "${pipeline.learning_rate}",
    },
    function_return=["model"],
    task_type=TaskTypes.training,
    parents=["preprocess"],
)
pipe.add_function_step(
    name="evaluate",
    function=evaluate,
    function_kwargs={"model": "${train.model}"},
    function_return=["metrics"],
    task_type=TaskTypes.qc,
    parents=["train"],
)
```

Function-step notes:

- Functions should be importable/global, not nested closures.
- `function_return` names returned artifacts; references use `${step_name.return_name}` for function-created steps.
- `helper_functions` supplies extra standalone helpers needed by a function step.
- Use per-step `execution_queue`, `packages`, `repo`, `docker`, and `working_dir` when remote workers require explicit runtime controls.
- Use `cache_executed_step=True` only when identical code and inputs should reuse prior results.

## HPO With HyperParameterOptimizer

Use Python HPO when the agent can write an optimization controller script. The base task must report the exact scalar title and series used as the objective.

```python
from clearml.automation import (
    DiscreteParameterRange,
    HyperParameterOptimizer,
    LogUniformParameterRange,
    RandomSearch,
    UniformIntegerParameterRange,
)

optimizer = HyperParameterOptimizer(
    base_task_id="BASE_TASK_ID",
    hyper_parameters=[
        LogUniformParameterRange("General/learning_rate", min_value=-5, max_value=-1, base=10),
        UniformIntegerParameterRange("General/batch_size", min_value=16, max_value=128, step_size=16),
        DiscreteParameterRange("General/optimizer", values=["adam", "sgd"]),
    ],
    objective_metric_title="validation",
    objective_metric_series="loss",
    objective_metric_sign="min",
    optimizer_class=RandomSearch,
    max_number_of_concurrent_tasks=2,
    execution_queue="workers",
    optimization_time_limit=60.0,
    compute_time_limit=120.0,
)
optimizer.set_report_period(1.0)
optimizer.start()
optimizer.wait()
print(optimizer.get_top_experiments(top_k=3))
```

HPO constraints and choices:

- `objective_metric_title` and `objective_metric_series` must exactly match the base task's `Logger.report_scalar(title=..., series=...)` calls; wrong capitalization or series names produce no usable objective.
- `objective_metric_sign` accepts `min`, `max`, `min_global`, or `max_global`; use `_global` variants when the best value over all iterations matters instead of the last value.
- Search parameter names should include the ClearML section prefix, such as `General/lr` or `Args/batch_size`. The CLI prefixes names without `/` as `General/`.
- `execution_queue` is the worker queue for cloned jobs. The optimizer controller itself runs where the script is launched unless it is embedded in another remote controller/service.
- `start_locally()` keeps HPO work local; use it only when local dependencies, data, and compute capacity match the intended run.
- For CLI HPO, use [HPO CLI reference](hpo-cli-reference.md) and validate JSON with [`../scripts/hpo_search_space_check.py`](../scripts/hpo_search_space_check.py) before launching.

## Scheduler And Trigger Recipes

Use schedulers as long-running services. `start()` does not return; prefer remote service/controller queues for production if the user has a safe queue and agent.

```python
from clearml.automation import TaskScheduler

scheduler = TaskScheduler(sync_frequency_minutes=15)
scheduler.add_task(
    name="weekday-training",
    schedule_task_id="BASE_TASK_ID",
    queue="workers",
    minute=30,
    hour=8,
    weekdays=["monday", "tuesday", "wednesday", "thursday", "friday"],
    recurring=True,
    single_instance=True,
    task_parameters={"General/lr": 0.01},
)
# scheduler.start_remotely(queue="services")
# scheduler.start()
```

Scheduler validation notes:

- Times are UTC.
- `minute=15` means every 15 minutes; `hour=1, minute=30` means every hour at minute 30; `day=1, hour=22, minute=30` means every day at 22:30 UTC.
- `weekdays` accepts lowercase day names. If `weekdays` is used with `day`, `day` must be `None`, `0`, or `1`.
- `schedule_function` runs in the scheduler process; `schedule_task_id` clones/enqueues a ClearML Task.
- `task_parameters` and `task_overrides` are not available with `reuse_task=True`.

```python
from clearml.automation import TriggerScheduler

trigger = TriggerScheduler(pooling_frequency_minutes=3.0, sync_frequency_minutes=15)
trigger.add_model_trigger(
    name="deploy-on-publish",
    schedule_task_id="DEPLOY_TASK_ID",
    schedule_queue="services",
    trigger_project="models",
    trigger_on_publish=True,
    trigger_required_tags=["production"],
    single_instance=True,
)
trigger.add_task_trigger(
    name="retrain-on-quality-drop",
    schedule_task_id="RETRAIN_TASK_ID",
    schedule_queue="workers",
    trigger_project="training",
    trigger_on_metric="validation",
    trigger_on_variant="loss",
    trigger_on_sign="min",
    trigger_on_threshold=0.2,
)
# trigger.start_remotely(queue="services")
# trigger.start()
```

Trigger validation notes:

- A model trigger `schedule_function` receives `model_id`; a dataset trigger receives `dataset_id`; a task trigger receives `task_id`.
- `task_overrides` may use `${model.id}`, `${dataset.id}`, or `${task.id}` according to trigger type.
- Task metric trigger signs accept `max`/`maximum` for above-threshold events and `min`/`minimum` for below-threshold events.
- Add tags or `single_instance=True` to reduce duplicate launches when polling sees repeated matching events.
