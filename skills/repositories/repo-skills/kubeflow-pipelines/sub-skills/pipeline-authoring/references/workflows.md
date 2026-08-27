# Pipeline Authoring Workflows

These recipes are self-contained KFP v2 authoring patterns. They do not require a running KFP service. For compile flags, CLI behavior, or generated YAML shape, route to `compiler-and-cli`.

## Choose the right component style

### Use `@dsl.component` for Python function work

Use this when the task can be expressed as Python code and the runtime image has Python.

```python
from kfp import dsl

@dsl.component(base_image="python:3.11", packages_to_install=[])
def normalize_text(text: str) -> str:
    return " ".join(text.strip().lower().split())
```

Put runtime imports inside the function body if the package is needed when the task runs:

```python
@dsl.component(packages_to_install=["pandas>=2,<3"])
def count_rows(csv_path: str) -> int:
    import pandas as pd
    return int(len(pd.read_csv(csv_path)))
```

Use `base_image` for the Python runtime and system libraries. Use `packages_to_install` for pip-installed Python dependencies. Use `use_venv=True` when the runtime environment is restrictive or shared and you want component package installs isolated in a temporary virtual environment.

### Use `@dsl.container_component` for arbitrary containers

Use this when the component is an image plus command, or when the command is not a lightweight Python function.

```python
from kfp import dsl

@dsl.container_component
def echo_container(text: str):
    return dsl.ContainerSpec(
        image="python:3.11-slim",
        command=["python", "-c"],
        args=["import sys; print(sys.argv[1])", text],
    )
```

In a container component, the decorated Python function is an authoring-time factory for `ContainerSpec`. It is not the task runtime body.

## Wire parameters and artifacts

### Single parameter output

```python
@dsl.component
def add(a: float, b: float) -> float:
    return a + b

@dsl.pipeline(name="add-pipeline")
def add_pipeline(x: float = 1.0) -> float:
    task = add(a=x, b=2.0)
    return task.output
```

### Multiple parameter outputs

```python
from typing import NamedTuple
from kfp import dsl

@dsl.component
def split_name(full_name: str) -> NamedTuple("outputs", first=str, last=str):
    outputs = NamedTuple("outputs", first=str, last=str)
    first, _, last = full_name.partition(" ")
    return outputs(first=first, last=last)

@dsl.pipeline(name="name-pipeline")
def name_pipeline(full_name: str = "Ada Lovelace"):
    task = split_name(full_name=full_name)
    greet(first=task.outputs["first"], last=task.outputs["last"])
```

Do not use `task.output` when a task has multiple outputs; use `task.outputs["name"]`.

### Artifact producer and consumer

```python
from kfp import dsl

@dsl.component
def make_dataset(text: str, dataset: dsl.Output[dsl.Dataset]) -> str:
    import json
    with open(dataset.path, "w", encoding="utf-8") as output_file:
        json.dump({"text": text}, output_file)
    dataset.metadata["format"] = "json"
    return text

@dsl.component
def read_dataset(dataset: dsl.Input[dsl.Dataset]) -> int:
    import json
    with open(dataset.path, "r", encoding="utf-8") as input_file:
        payload = json.load(input_file)
    return len(payload["text"])

@dsl.pipeline(name="artifact-pipeline")
def artifact_pipeline(message: str = "hello") -> int:
    produced = make_dataset(text=message)
    consumed = read_dataset(dataset=produced.outputs["dataset"])
    return consumed.output
```

Artifact outputs declared as output parameters are keyed by the parameter name (`"dataset"` above). Return values are keyed as `"Output"` when another output exists.

### Output paths for parameters

Use `dsl.OutputPath(T)` when a component writes a parameter value to a file path supplied by KFP.

```python
@dsl.component
def write_score(score: float, score_path: dsl.OutputPath(float)):
    with open(score_path, "w", encoding="utf-8") as output_file:
        output_file.write(str(score))
```

A path output appears in `task.outputs` under the function parameter name (`"score_path"` here).

## Compose pipelines and task modifiers

Task modifiers are chainable when they return the task object:

```python
@dsl.pipeline(name="training-pipeline", pipeline_root="gs://my-bucket/kfp-root")
def training_pipeline(dataset_uri: str):
    prep = prepare(uri=dataset_uri).set_display_name("prepare data")

    train_task = train(dataset=prep.output)
    train_task.after(prep)
    train_task.set_cpu_limit("1")
    train_task.set_memory_limit("2Gi")
    train_task.set_retry(num_retries=2, backoff_duration="30s")
    train_task.set_caching_options(enable_caching=True)
    train_task.set_env_variable("LOG_LEVEL", "INFO")

    evaluate(model=train_task.output).after(train_task)
```

Use regular task modifiers here. If the user asks for secrets, ConfigMaps, PVCs, pod annotations, tolerations, affinity, image pull secrets, or security contexts, route to `kubernetes-platform`.

## Author control flow

### Prefer `dsl.If` / `dsl.Elif` / `dsl.Else`

```python
@dsl.pipeline(name="branching-pipeline")
def branching_pipeline(threshold: float = 0.8) -> str:
    score = score_model()

    with dsl.If(score.output >= threshold):
        accepted = emit_message(message="accepted")
    with dsl.Else():
        rejected = emit_message(message="rejected")

    return dsl.OneOf(accepted.output, rejected.output)
```

`dsl.Condition` exists for legacy code but is deprecated in favor of `dsl.If`. If a user brings legacy code using `dsl.Condition`, repair the code without expanding new examples around it unless compatibility is required.

A condition must include at least one pipeline parameter or upstream task output. A plain Python boolean condition means the expression evaluated too early and should be rewritten.

### Loop over static items

```python
@dsl.pipeline(name="static-loop-pipeline")
def static_loop_pipeline():
    with dsl.ParallelFor([
        {"fold": 0, "seed": 11},
        {"fold": 1, "seed": 17},
    ], parallelism=1) as item:
        train_fold(fold=item.fold, seed=item.seed)
```

Use `parallelism=1` when you need deterministic serialized iteration; omit it or set `0` for unconstrained backend scheduling.

### Loop over an upstream list

```python
@dsl.component
def make_items() -> list:
    return ["a", "b", "c"]

@dsl.pipeline(name="dynamic-loop-pipeline")
def dynamic_loop_pipeline():
    items = make_items()
    with dsl.ParallelFor(items.output) as item:
        consume_item(value=item)
```

### Exit handling and final status

```python
@dsl.component
def cleanup(status: dsl.PipelineTaskFinalStatus):
    print(status.state)

@dsl.pipeline(name="exit-handler-pipeline")
def exit_handler_pipeline():
    cleanup_task = cleanup()
    with dsl.ExitHandler(cleanup_task):
        train()
        evaluate()
```

`ExitHandler` is useful for cleanup and status reporting. The exit task itself cannot depend on other tasks before the `ExitHandler` block is formed.

## Local or compile-adjacent smoke pattern

For a quick authoring sanity check without a cluster, use either a direct local execution smoke from `references/local-execution.md` or the bundled compile smoke helper.

From this sub-skill directory:

```bash
python scripts/compile_minimal_pipeline.py --output /tmp/kfp-authoring-smoke.yaml
```

Use this helper to prove the installed SDK can parse common authoring constructs. If the user needs custom `kfp dsl compile` flags, package-path handling, type-check switches, Kubernetes manifest options, or YAML field inspection, route to `compiler-and-cli`.

## Review checklist for authored code

Before handing authoring code back:

- Every component argument has a type annotation.
- Runtime-only imports are inside the component body or installed in the runtime image.
- Artifact objects use `Input[...]`/`Output[...]`; path-style IO uses `InputPath(...)`/`OutputPath(...)`.
- Task outputs are accessed by key when there is more than one output.
- Control-flow conditions involve a pipeline parameter or upstream task output.
- Container components return `dsl.ContainerSpec` and do not attempt to run the decorated Python function as the task body.
- Local execution examples call `local.init(...)` before invoking a component or pipeline.
