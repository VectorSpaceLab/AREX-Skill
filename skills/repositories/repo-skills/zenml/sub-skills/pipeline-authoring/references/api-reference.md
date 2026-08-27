# Pipeline Authoring API Reference

This reference summarizes the ZenML public APIs a future agent needs for step and pipeline authoring. It is distilled from the ZenML 0.95.1 package surface, public docs, examples, and unit-test-backed behavior.

## Imports

Use these stable imports for ordinary pipeline authoring:

```python
from typing import Annotated

from zenml import ArtifactConfig, get_step_context, pipeline, run_hook, step, unmapped, wait
from zenml.config import DockerSettings, ResourceSettings, Schedule, StepRetryConfig
from zenml.enums import ExecutionMode, StepRuntime, StepType
from zenml.materializers.base_materializer import BaseMaterializer
```

Operational code that queries runs, artifacts, wait conditions, schedules, or stack state usually needs `from zenml.client import Client`; CLI-heavy audits belong in `../cli-and-client/SKILL.md`.

## Decorators

### `@step`

A ZenML step wraps a normal Python function as a reusable unit of computation. Keep step functions importable from module scope for packaging, dynamic execution, and source resolution.

Common `@step(...)` options:

- `name`: Override the step name; defaults to the function name.
- `step_type`: Semantic label such as `StepType.LLM_CALL`, `StepType.TOOL_CALL`, or `StepType.MEMORY_CALL`; it does not change execution semantics.
- `enable_cache`: Enable or disable cache reuse for this step.
- `enable_artifact_metadata`, `enable_artifact_visualization`, `enable_step_logs`: Control metadata, visualizations, and logs.
- `experiment_tracker`, `step_operator`: Use the active stack component (`True`) or a named component (`"component_name"`) for this step.
- `output_materializers`: Custom materializer assignment for one or more outputs.
- `environment`, `secrets`, `settings`, `extra`: Runtime environment, secret, stack-component, and arbitrary extra configuration.
- `on_start`, `on_success`, `on_failure`, `on_end`: Step lifecycle hooks.
- `model`, `retry`, `substitutions`, `cache_policy`: Model Control Plane, retry, artifact/model name substitution, and cache policy controls.
- `runtime`: Dynamic-pipeline step runtime, commonly `"inline"` or `"isolated"`.
- `heartbeat_healthy_threshold`: Minutes without heartbeat before an isolated step is considered unhealthy.
- `group`: Step grouping metadata.

Step functions can use keyword-only parameters. Avoid variadic `*args` and `**kwargs`; ZenML needs a known interface before compiling or running the workflow.

### `@pipeline`

A ZenML pipeline composes steps into a DAG. Calling a prepared pipeline object runs it, or schedules it when a schedule is attached.

Common `@pipeline(...)` options:

- `name`: Override the pipeline name; defaults to the function name.
- `dynamic=True`: Execute the pipeline body at runtime and allow Python control flow, mapping, submitted steps, waits, and child pipelines.
- `depends_on`: Predeclare steps for dynamic-pipeline config templates; duplicates are rejected.
- `enable_cache`, `enable_artifact_metadata`, `enable_step_logs`, `enable_heartbeat`, `enable_pipeline_logs`: Pipeline defaults for caching, metadata, logs, and heartbeat behavior.
- `environment`, `secrets`, `settings`, `tags`, `extra`: Pipeline-level runtime and metadata configuration.
- `on_start`, `on_success`, `on_failure`, `on_end`: Static pipelines propagate these as defaults to steps; dynamic pipelines run them once at run scope.
- `on_pause`, `on_resume`: Dynamic-pipeline run-level hooks; ignored for static pipelines.
- `on_init`, `on_init_kwargs`, `on_cleanup`: Execution-environment setup/teardown hooks, not lifecycle `HookInvocation` records.
- `model`, `retry`, `substitutions`, `execution_mode`, `cache_policy`: Pipeline-level model, retry, naming, failure-mode, and cache controls.

Dynamic pipelines default to `ExecutionMode.STOP_ON_FAILURE` when no execution mode is supplied. Static pipelines cannot be called from inside a dynamic pipeline run; use a dynamic child pipeline instead.

## Configuration Methods

`configure(...)` and `with_options(...)` accept similar options but have different mutation behavior.

- `with_options(...)` returns a configured copy. Prefer it inside pipeline definitions and for per-run changes.
- `configure(...)` mutates the existing step or pipeline object in place. Use it only when every later invocation should inherit the change.
- Step `with_options(...)` accepts `parameters`, `output_materializers`, `settings`, hooks, `retry`, `runtime`, `cache_policy`, `merge`, and the decorator options listed above.
- Pipeline `with_options(...)` additionally accepts `run_name`, `schedule`, `build`, `steps` or `step_configurations`, `config_path`, and `prevent_build_reuse`.
- Code options override YAML options. Step-level settings override pipeline-level settings. Dictionary settings merge unless `merge=False` is used for step options.

## Inputs, Parameters, and Outputs

ZenML distinguishes artifacts from parameters.

- A value produced by one step and passed to another is an artifact. ZenML stores, versions, materializes, and tracks it.
- A literal value supplied directly to a step invocation is a parameter. Keep it JSON-serializable.
- Pass complex objects, datasets, model objects, directories, and non-JSON values as artifacts rather than parameters.
- Type annotations help ZenML choose materializers and validate runtime values.

Output naming rules:

- A single unannotated output is named `output`.
- Multiple unannotated outputs are named `output_0`, `output_1`, and so on.
- Use `typing.Annotated` to name outputs explicitly:

```python
from typing import Annotated

@step
def split() -> tuple[Annotated[list[int], "train"], Annotated[list[int], "test"]]:
    return [1, 2], [3]
```

Use `ArtifactConfig` when a name needs metadata or placeholder substitution:

```python
@step(substitutions={"suffix": "validated"})
def score() -> Annotated[int, ArtifactConfig(name="score_{suffix}")]:
    return 1
```

When assigning `output_materializers` with a mapping, every key must match a real output name. If a step returns `train` and `test`, a key such as `output` is invalid.

## Materializers

Materializers define how artifact values are saved, loaded, visualized, and indexed. Built-in materializers cover primitives, bytes, containers, NumPy arrays, pandas objects, Pydantic models, dataclasses, structured strings, paths, and services. Integration-specific materializers require their corresponding extras or stack image dependencies.

Custom materializer checklist:

```python
from typing import Any, Type

from zenml.enums import ArtifactType
from zenml.materializers.base_materializer import BaseMaterializer

class MyObjectMaterializer(BaseMaterializer):
    ASSOCIATED_TYPES = (MyObject,)
    ASSOCIATED_ARTIFACT_TYPE = ArtifactType.DATA

    def save(self, data: MyObject) -> None:
        with self.artifact_store.open(f"{self.uri}/data.json", "w") as handle:
            handle.write(data.to_json())

    def load(self, data_type: Type[Any]) -> MyObject:
        with self.artifact_store.open(f"{self.uri}/data.json", "r") as handle:
            return MyObject.from_json(handle.read())
```

Rules that matter in production:

- `ASSOCIATED_TYPES` must contain at least one class, otherwise class creation fails.
- `ASSOCIATED_ARTIFACT_TYPE` should be a valid `ArtifactType` when set.
- Use `self.artifact_store.open(...)`, not direct filesystem I/O, so remote artifact stores work.
- Save all visualization files below `self.uri`; return a mapping of visualization URI to `VisualizationType`.
- Implement `compute_content_hash(...)` when cache identity should depend on custom object contents.
- Implement both `get_item_count(...)` and `load_item(...)` before using a custom type in dynamic mapping.
- Avoid `CloudpickleMaterializer` for durable production artifacts because Python-version compatibility is weak.
- For Docker or remote orchestrators, include the custom materializer module and any integration materializer dependencies in the pipeline image.

## Settings

Settings are supplied under the `settings={...}` mapping at the pipeline or step level.

Common keys:

- `"docker"`: `DockerSettings` or equivalent dictionary.
- `"resources"`: `ResourceSettings` or equivalent dictionary.
- `"orchestrator"`: Default orchestrator settings for the active stack.
- `"orchestrator.<flavor>"`: Target the only attached orchestrator of a flavor.
- `"orchestrator:<name>"`: Target a specific named stack component.
- The same category, flavor, and name patterns apply to experiment trackers, step operators, deployers, and other stack components.

`ResourceSettings` authoring notes:

- Common fields are `cpu_count`, `gpu_count`, `memory`, `pool_resources`, and `preemptible`.
- `memory` must include a supported unit such as `MB`, `MiB`, `GB`, or `GiB`.
- Deployment-related fields include `min_replicas`, `max_replicas`, `autoscaling_metric`, `autoscaling_target`, and `max_concurrency`.
- Not every orchestrator or deployer enforces every resource field; route backend enforcement questions to `../stacks-and-integrations/SKILL.md`.

`DockerSettings` authoring notes:

- Common fields are `parent_image`, `image_tag`, `dockerfile`, `build_context_root`, `skip_build`, `target_repository`, `requirements`, `required_integrations`, `install_stack_requirements`, `apt_packages`, `environment`, `runtime_environment`, `copy_files`, `copy_global_config`, and build options.
- When using integration materializers or optional SDKs in remote containers, add the narrow `required_integrations` or `requirements` entries rather than relying on a broad local development environment.
- `skip_build=True` requires a `parent_image`; otherwise there is no image to run.
- `replicate_local_python_environment=True` exports the local environment and can make images large or non-reproducible; prefer explicit requirements for agent-authored examples.

## Caching, Retries, and Execution Modes

- Caching is enabled by default unless disabled at the step or pipeline level.
- A cache hit reuses previous outputs and does not run the step body or step-level hooks.
- Step and pipeline `retry` values use `StepRetryConfig(max_retries=..., delay=..., backoff=...)`.
- Retried steps fire `on_start` and `on_end` for each attempt; `on_success` or `on_failure` fires once for the terminal result.
- Execution modes are `CONTINUE_ON_FAILURE`, `STOP_ON_FAILURE`, and `FAIL_FAST`. Full support depends on the orchestrator; local, local Docker, Kubernetes, and Modal are documented as supporting the non-default modes.
- Heartbeat applies to isolated step environments, not inline local steps.

## Hooks

Lifecycle hooks accept a callable or import-source string.

- `on_start`, `on_success`, `on_pause`, and `on_resume` take no arguments.
- `on_failure` and `on_end` may take an optional `BaseException` argument.
- Step-level hooks fire for static and dynamic pipelines.
- In static pipelines, `@pipeline(on_*=...)` acts as a default for each step.
- In dynamic pipelines, `@pipeline(on_*=...)` fires once at the run level.
- Hook failures are swallowed and recorded; they do not abort the step or run.
- Async hooks are supported and run to completion before ZenML continues.
- Use `get_step_context()` inside step hooks and `DynamicPipelineRunContext.get().run` for dynamic run-level hooks.
- Use `run_hook(...)` inside a step or dynamic pipeline body to record arbitrary custom invocations; `store_return=True` materializes the returned value.

## Dynamic Pipeline APIs

Dynamic pipelines are declared with `@pipeline(dynamic=True)`. They run the pipeline function at runtime, so normal Python control flow can shape the DAG.

Key APIs:

- `artifact_future.load()`: Load concrete data into the orchestration environment for decisions.
- `artifact_future.chunk(index=...)`: Wire one item from a sequence-like artifact to a downstream step.
- `step.map(...)`: Fan out over aligned sequence-like inputs.
- `step.product(...)`: Fan out over the Cartesian product of sequence-like inputs.
- `unmapped(value)`: Broadcast a sequence-like artifact as a whole to each mapped invocation.
- `mapped_outputs.unpack()`: Split mapped multi-output results into one list per output.
- `step.submit(...)`: Launch a step concurrently and return a future.
- `future.result()`: Wait for a submitted step or child pipeline and return its output artifact future or value wrapper.
- `future.wait()`: Wait for completion when no return value is needed.
- `child_pipeline(...)`: Synchronous child run.
- `child_pipeline.submit(...)`: Concurrent child run.
- `child_pipeline.embed(...)`: Inline reuse of a child dynamic pipeline body inside the parent run.
- `wait(schema=..., question=..., timeout=..., metadata=..., name=...)`: Pause a dynamic run for external input.

Dynamic child and resume semantics:

- `embed(...)` does not create a child run and ignores the child pipeline's own pipeline-level settings, retry, cache, tags, substitutions, model, and pipeline hooks.
- `child_pipeline(...)` and `child_pipeline.submit(...)` create child runs and apply child configuration.
- Child runs share the parent's build, source bundle, image, and orchestration environment; no separate Docker build occurs for the child.
- Resume idempotency depends on call order. Inserting, removing, or reordering child pipeline or step calls can shift generated invocation IDs and rerun previously completed work.
- A dynamic pipeline source must be loadable. If source resolution fails, move the decorated pipeline function to module scope.

## Wait and Resume

`wait(...)` only works inside a dynamic pipeline body, not in static pipelines and not inside `@step` functions.

- `schema` can be a primitive type, container type, or Pydantic model.
- `timeout` is the earliest point a run can pause after waiting; concurrent steps or child runs can keep the orchestration process alive until tree-wide work settles.
- Resolve wait conditions from the UI or CLI, then resume the run manually when required.
- Resume the parent run when the paused run is a child; the parent safely controls the nested execution tree.
- A run cannot resume while wait conditions remain active or when required snapshot/stack references are missing.

## Scheduling

Create schedules with `Schedule` and attach them with pipeline `with_options(schedule=...)`.

```python
from datetime import datetime, timedelta

from zenml.config import Schedule

cron_schedule = Schedule(cron_expression="5 14 * * 3", catchup=False)
interval_schedule = Schedule(
    start_time=datetime.now().astimezone(),
    interval_second=timedelta(minutes=30),
)
training_pipeline.with_options(schedule=cron_schedule)()
```

Rules:

- A valid schedule needs `cron_expression`, or `start_time` plus `interval_second`, or `run_once_start_time`.
- If both cron and interval/run-once fields are set, behavior depends on the orchestrator and usually favors cron.
- Naive datetimes are treated as local timezone and trigger a warning; prefer timezone-aware datetimes.
- Local and local Docker orchestrators do not support schedules. Scheduling support and native schedule update/delete behavior are orchestrator-specific.
- Schedule lifecycle CLI commands belong in `../cli-and-client/SKILL.md`; backend schedule implementation belongs in `../stacks-and-integrations/SKILL.md`.
