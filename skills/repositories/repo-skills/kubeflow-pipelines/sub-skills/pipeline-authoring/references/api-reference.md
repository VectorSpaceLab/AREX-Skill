# Pipeline Authoring API Reference

This reference captures the KFP v2 authoring API surface verified for the generated skill. It is for writing DSL code, not for explaining compiler flags or live service calls.

## Decorators and component builders

### `dsl.component`

Signature:

```python
dsl.component(
    func: Optional[Callable] = None,
    *,
    base_image: Optional[str] = None,
    target_image: Optional[str] = None,
    packages_to_install: List[str] = None,
    pip_index_urls: Optional[List[str]] = None,
    output_component_file: Optional[str] = None,
    install_kfp_package: bool = True,
    kfp_package_path: Optional[str] = None,
    pip_trusted_hosts: Optional[List[str]] = None,
    use_venv: bool = False,
    additional_funcs: Optional[List[Callable]] = None,
    embedded_artifact_path: Optional[str] = None,
    task_config_passthroughs: Optional[List[Union[TaskConfigPassthrough, TaskConfigField]]] = None,
)
```

Use it for Python-function components. The decorated function must have type annotations for every argument. Plain Python parameter types become pipeline parameters; artifact object inputs/outputs require artifact annotations or artifact return types.

Key options:

- `base_image`: runtime image for a lightweight Python component. Use an explicit Python-compatible image when reproducibility matters.
- `target_image`: declares a containerized Python component to be packaged into an image by the separate build flow. Route detailed build/CLI questions to `compiler-and-cli`.
- `packages_to_install`: packages installed in the component runtime before the function executes.
- `pip_index_urls`, `pip_trusted_hosts`: package index configuration for runtime installs.
- `install_kfp_package`: when true for lightweight components, KFP injects a runtime KFP install unless the package list already includes `kfp`.
- `kfp_package_path`: override where the runtime KFP package is installed from.
- `use_venv`: create and use a temporary virtual environment inside the component runtime install script.
- `additional_funcs`: helper functions to embed alongside the main function.
- `embedded_artifact_path`: embed a local file or directory into the component package. Use only for small assets.
- `output_component_file`: deprecated component spec write path; prefer full pipeline compilation via the compiler sub-skill.

### `dsl.container_component`

Signature:

```python
dsl.container_component(func: Callable) -> ContainerComponent
```

Use it when the task is an arbitrary container command, not a Python function body executed by the lightweight component launcher. The decorated function is evaluated at authoring time and must return a `dsl.ContainerSpec`.

```python
from kfp import dsl

@dsl.container_component
def echo_text(text: str):
    return dsl.ContainerSpec(
        image="python:3.11-slim",
        command=["python", "-c"],
        args=["import sys; print(sys.argv[1])", text],
    )
```

For container components, artifact arguments must use `dsl.Input[...]`, `dsl.Output[...]`, `dsl.InputPath(...)`, or `dsl.OutputPath(...)`. Do not place an artifact object itself directly into `ContainerSpec.command` or `ContainerSpec.args`; use a path, URI, or supported placeholder form.

### `dsl.ContainerSpec`

Signature:

```python
dsl.ContainerSpec(
    image: str,
    command: Optional[List[Union[str, Placeholder]]] = None,
    args: Optional[List[Union[str, Placeholder]]] = None,
)
```

The image and command describe what the runtime container executes. This is authoring-level container configuration. Kubernetes-specific pod settings belong to the `kubernetes-platform` sub-skill.

### `dsl.pipeline`

Signature:

```python
dsl.pipeline(
    func: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    pipeline_root: Optional[str] = None,
    display_name: Optional[str] = None,
    pipeline_config: Optional[dsl.PipelineConfig] = None,
) -> Callable
```

Use it to compose component factories into a graph. A pipeline function should instantiate tasks and return task outputs when the pipeline has outputs.

```python
@dsl.pipeline(name="text-pipeline", pipeline_root="gs://my-bucket/root")
def text_pipeline(message: str = "hello") -> str:
    make_task = make_message(message=message)
    return make_task.output
```

## Parameters, artifacts, paths, and outputs

### Parameter types

Common parameter annotations include `str`, `int`, `float`, `bool`, `dict`, and `list`. Component function parameters without defaults are required; parameters with defaults are optional.

Multiple parameter outputs are usually declared with `typing.NamedTuple`:

```python
from typing import NamedTuple
from kfp import dsl

@dsl.component
def split_pair(text: str) -> NamedTuple("outputs", left=str, right=str):
    outputs = NamedTuple("outputs", left=str, right=str)
    left, _, right = text.partition(":")
    return outputs(left=left, right=right)
```

Access multiple outputs by name: `task.outputs["left"]`. Use `task.output` only when exactly one output exists.

### Artifact classes and annotations

Available artifact classes include:

- `dsl.Artifact(name=None, uri=None, metadata=None)`
- `dsl.Dataset(name=None, uri=None, metadata=None)`
- `dsl.Model(name=None, uri=None, metadata=None)`
- `dsl.Metrics(name=None, uri=None, metadata=None)`
- `dsl.ClassificationMetrics(name=None, uri=None, metadata=None)`

Use `dsl.Input[T]` and `dsl.Output[T]` for artifact objects:

```python
@dsl.component
def train(dataset: dsl.Input[dsl.Dataset], model: dsl.Output[dsl.Model]):
    with open(dataset.path, "r", encoding="utf-8") as source:
        data = source.read()
    with open(model.path, "w", encoding="utf-8") as target:
        target.write(data)
    model.metadata["framework"] = "custom"
```

Use `dsl.InputPath(T)` and `dsl.OutputPath(T)` when the component should receive a local filesystem path instead of an artifact object:

```python
@dsl.component
def write_number(number: int, output_path: dsl.OutputPath(int)):
    with open(output_path, "w", encoding="utf-8") as output_file:
        output_file.write(str(number))
```

Artifact outputs declared as parameters, such as `model: dsl.Output[dsl.Model]`, appear in `task.outputs` under the function argument name.

### Metrics helpers

`dsl.Metrics` supports scalar metadata via `metrics.log_metric(name, value)`. `dsl.ClassificationMetrics` supports ROC and confusion-matrix helpers such as `log_roc_data_point`, `log_roc_curve`, `set_confusion_matrix_categories`, `log_confusion_matrix_row`, `log_confusion_matrix_cell`, and `log_confusion_matrix`.

### Runtime URI helper

`dsl.get_uri(suffix="Output")` can be called only inside a component at task runtime. It raises if the task root is unknown. Prefer backend-provided `Output[...]` paths when possible.

## `PipelineTask` usage

Do not construct `dsl.PipelineTask` directly. A task is returned when a component or pipeline component is called inside a pipeline definition.

Important properties:

- `task.name`: generated task name.
- `task.inputs`: arguments passed to the task.
- `task.output`: the only output, if the task has exactly one output.
- `task.outputs`: mapping of all output names to pipeline channels or realized local values.
- `task.dependent_tasks`: compile-time dependency names; not available after direct local execution.

Verified user-facing modifier methods:

| Method | Purpose | Notes |
| --- | --- | --- |
| `after(*tasks)` | Add explicit ordering dependency. | Accepts upstream `PipelineTask` objects and exit handler groups. |
| `ignore_upstream_failure()` | Run even when upstream dependencies fail. | Inputs from failed upstream tasks need safe defaults unless using final status. |
| `set_retry(num_retries, backoff_duration=None, backoff_factor=None, backoff_max_duration=None)` | Configure retry policy. | Also supported by local execution in the inspected package. |
| `set_caching_options(enable_caching, cache_key=None)` | Enable/disable task cache and optional key. | Local caching also requires `local.init(..., enable_caching=True)`. |
| `set_env_variable(name, value)` | Add environment variable to the task container. | Useful for component runtime config; Kubernetes secrets/config maps route to `kubernetes-platform`. |
| `set_display_name(name)` | Set human-readable task display name. | Local execution may ignore it with a warning. |
| `set_cpu_request(cpu)`, `set_cpu_limit(cpu)` | Set CPU request/limit. | CPU strings accept numbers or millicores such as `500m`. |
| `set_memory_request(memory)`, `set_memory_limit(memory)` | Set memory request/limit. | Memory strings accept units such as `Mi`, `Gi`, `M`, or bare integers. |
| `set_accelerator_type(accelerator)`, `set_accelerator_limit(limit)` | Set accelerator type/count. | Compile-time task resource metadata; actual runtime needs matching cluster resources. |
| `set_gpu_limit(gpu)` | Deprecated GPU count helper. | Prefer `set_accelerator_limit`. |
| `add_node_selector_constraint(accelerator)` | Deprecated accelerator-type helper. | Prefer `set_accelerator_type`. |
| `set_container_image(name)` | Override task container image. | May accept a static string or pipeline-channel-derived dynamic value. |
| `set_debug_pause(before=False, after=True, on_error=False)` | Configure Argo debug pause env vars. | Requires a backend that honors those env vars; not a local debugging primitive. |

Regular task modifiers are in this sub-skill. Kubernetes-specific task helpers, including secrets, PVCs, tolerations, affinity, pod labels, and security context, are not.

## Runtime import caveat

Lightweight component code is executed with `_KFP_RUNTIME=true`. In that mode, most compile-time SDK imports are intentionally hidden from `kfp.dsl`; runtime-safe classes such as `Artifact`, `Dataset`, `Model`, `Metrics`, `Input`, `Output`, `InputPath`, `OutputPath`, placeholders, `get_uri`, and final-status helpers remain available. Do not call `dsl.component`, `dsl.container_component`, `dsl.pipeline`, compiler APIs, clients, or registry APIs from inside component runtime code unless you explicitly install and import the needed packages and understand the runtime image constraints.
