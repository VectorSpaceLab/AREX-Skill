# Pipeline Authoring Troubleshooting

Use this as symptom -> cause -> repair guidance for KFP DSL authoring. Route compiler flags/output-shape issues to `compiler-and-cli`, service calls to `client-and-registry`, Kubernetes helper issues to `kubernetes-platform`, and source-checkout maintainer issues to `repo-development`.

## Missing type annotations

**Symptoms**

- Component creation fails with a missing annotation error.
- An argument is treated differently than expected.

**Likely cause**

`@dsl.component` and `@dsl.container_component` build component interfaces from Python type annotations. Every component argument needs an annotation.

**Repair**

```python
@dsl.component
def transform(text: str, limit: int = 10) -> str:
    return text[:limit]
```

For artifacts, choose `dsl.Input[T]` / `dsl.Output[T]` or path annotations rather than leaving arguments untyped.

## Wrong artifact annotation

**Symptoms**

- Artifact input is rejected or appears as a parameter.
- A consumer cannot access `.path`, `.uri`, or `.metadata`.
- A container component errors when an artifact object is placed directly in `ContainerSpec.args`.

**Likely cause**

Artifact object IO and path-style IO were mixed up, or a container component did not wrap artifacts with `Input`/`Output` markers.

**Repair**

Use artifact objects when the component needs metadata:

```python
@dsl.component
def consume(dataset: dsl.Input[dsl.Dataset]):
    print(dataset.uri)
    with open(dataset.path, "r", encoding="utf-8") as input_file:
        print(input_file.read())
```

Use paths when only a filesystem path is needed:

```python
@dsl.component
def consume_path(dataset_path: dsl.InputPath(dsl.Dataset)):
    with open(dataset_path, "r", encoding="utf-8") as input_file:
        print(input_file.read())
```

For container components, pass supported placeholders or fields such as `.path`, not the artifact object by itself.

## Missing return or output wiring

**Symptoms**

- `task.output` raises because the task has multiple outputs.
- A downstream component gets a missing input or wrong type.
- An output artifact is never connected to its consumer.

**Likely cause**

The producer has multiple outputs or an output artifact parameter, but downstream code uses the single-output shortcut.

**Repair**

- Single return output only: use `task.output`.
- Multiple `NamedTuple` outputs: use `task.outputs["field_name"]`.
- Output artifact parameter: use `task.outputs["argument_name"]`.
- A Python component with both a return value and an artifact output has at least two outputs; use mapping access for both.

```python
produced = make_dataset(text="hello")
read_dataset(dataset=produced.outputs["dataset"])
print_text(text=produced.outputs["Output"])
```

## Component vs container component confusion

**Symptoms**

- A `@dsl.container_component` body imports Python packages and expects that body to run in the task container.
- `SubprocessRunner` raises that it only supports lightweight Python components.
- A `@dsl.component` is used when the desired behavior is an existing image command.

**Likely cause**

`@dsl.component` and `@dsl.container_component` have different execution models.

**Repair**

- Use `@dsl.component` when the decorated Python function is the runtime task logic.
- Use `@dsl.container_component` when the function returns `dsl.ContainerSpec` at authoring time and the container command is the runtime logic.
- Use `DockerRunner` or a real backend for local/runtime checks involving container components. Use `SubprocessRunner` for lightweight Python components only.

## Local execution not initialized

**Symptoms**

- Error says the local environment is not initialized and asks to run `kfp.local.init()`.

**Likely cause**

A component or pipeline was called as a Python function before local execution was initialized.

**Repair**

```python
from kfp import local
local.init(runner=local.SubprocessRunner(use_venv=False))
```

Then call the component or pipeline function. See `local-execution.md` for runner choice.

## Wrong local runner selected

**Symptoms**

- `SubprocessRunner` rejects a container component.
- A custom image behaves differently locally than in the backend.
- Docker errors occur for a lightweight component that could run in a subprocess.

**Likely cause**

The runner does not match the component style.

**Repair**

- Choose `SubprocessRunner` for lightweight Python components where package dependencies are available or installable in Python.
- Choose `DockerRunner` for container components, custom images, or image-dependent behavior.
- If the task is only to compile a pipeline, do not use local execution at all; use the bundled smoke helper here or route compile details to `compiler-and-cli`.

## DockerRunner package or daemon missing

**Symptoms**

- `ImportError` says package `docker` must be installed.
- Error says DockerRunner was selected but docker is not installed.
- Connection or permission failure when contacting the Docker daemon.

**Likely cause**

Docker local execution needs both the Python Docker SDK and a reachable Docker daemon.

**Repair**

- For lightweight Python components, switch to `local.SubprocessRunner(...)`.
- For container semantics, install the Python Docker SDK in the working environment and start or grant access to the Docker daemon.
- Do not pass `image`, `command`, or `volumes` as DockerRunner run arguments; KFP controls those for the task.

## `base_image`, `packages_to_install`, and `use_venv` confusion

**Symptoms**

- A component imports a package successfully at authoring time but fails at runtime.
- Pip installs race or contaminate the local environment.
- A custom image is specified but Python package dependencies are still missing.

**Likely cause**

Authoring-time imports, component runtime image contents, component runtime pip installs, and local runner isolation are separate concerns.

**Repair**

- Put imports needed by the task inside the component body.
- Add missing Python runtime packages to `packages_to_install` or build them into `base_image`.
- Use `@dsl.component(use_venv=True)` when the component runtime should create a temporary venv for its install script.
- Use `local.SubprocessRunner(use_venv=True)` when local subprocess task installs should be isolated.
- Use DockerRunner when the behavior depends on non-Python system libraries in a custom image.

## Runtime image missing SDK-only dependencies

**Symptoms**

- Component runtime fails importing SDK compile-time APIs.
- Code inside a component attempts to define another component or compile a pipeline.
- Runtime sees fewer `kfp.dsl` symbols than authoring code.

**Likely cause**

Lightweight component execution sets `_KFP_RUNTIME=true`, which hides most compile-time SDK imports from `kfp.dsl`. KFP may install the runtime SDK package, but not every authoring or service dependency is available in the task image.

**Repair**

- Do not author or compile pipelines inside component bodies.
- Keep decorators, compiler calls, client calls, and registry calls in the outer script or a separate workflow.
- If a task truly needs an SDK or third-party runtime import, install it via `packages_to_install` or bake it into the image, and import it inside the component body.

## Conditions evaluate too early

**Symptoms**

- Error says a constant boolean was used as a condition.
- A branch is chosen by Python at authoring time instead of by KFP at runtime.

**Likely cause**

The condition compares plain Python values rather than a pipeline parameter or upstream task output.

**Repair**

Use a pipeline argument or task output in the condition:

```python
@dsl.pipeline
def branch_pipeline(flag: str = "yes"):
    with dsl.If(flag == "yes"):
        run_yes()
```

If both sides are constants, use normal Python before defining the pipeline instead of KFP control flow.

## Multiple-output or branch merge errors

**Symptoms**

- `dsl.OneOf` rejects mixed output types.
- `dsl.OneOf` says an `Else` branch is required.
- Downstream task receives an unavailable branch output.

**Likely cause**

Branch outputs are not mutually complete or have incompatible types.

**Repair**

- Ensure every mutually exclusive branch that can run produces the output.
- Include an `dsl.Else` branch when using `dsl.OneOf` so at least one output is available.
- Do not mix parameter outputs and artifact outputs in one `dsl.OneOf`.
- Keep all `dsl.OneOf` channels the same type.

## Resource modifiers do not affect local runs

**Symptoms**

- CPU/memory/accelerator settings compile but local execution does not enforce them.
- Local execution emits warnings that backend-specific methods are ignored.

**Likely cause**

Resource methods are backend scheduling metadata. The local runner does not become Kubernetes or enforce pod resources.

**Repair**

Use local execution to validate Python logic and data wiring. Use compile checks to validate resource settings exist. Use a real backend with matching resources for runtime scheduling behavior.

## Need secrets, PVCs, labels, tolerations, or security context

**Symptoms**

- User asks for Kubernetes pod/task configuration that is not a regular `PipelineTask` method.

**Likely cause**

The request belongs to the `kfp-kubernetes` addon, not core DSL authoring.

**Repair**

Route to `kubernetes-platform`. Keep this sub-skill focused on regular DSL authoring and task modifiers.
