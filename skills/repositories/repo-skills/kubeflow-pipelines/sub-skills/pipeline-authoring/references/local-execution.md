# Local Execution Reference

KFP local execution lets you call components and pipelines as Python functions for fast authoring feedback. It is not a substitute for compile-output inspection or live KFP service execution.

## Public local API

Signatures verified for this skill:

```python
local.init(
    runner: Union[local.SubprocessRunner, local.DockerRunner],
    pipeline_root: str = "./local_outputs",
    workspace_root: Optional[str] = None,
    raise_on_error: bool = True,
    enable_caching: bool = False,
    cache_root: Optional[str] = None,
) -> None

local.SubprocessRunner(
    use_venv: bool = True,
    serialize_pip_installs: bool = True,
    max_concurrent_pip_installs: int = 1,
)

local.DockerRunner(
    max_concurrent_pip_installs: int = 1,
    **container_run_args,
)
```

Initialize once before local calls:

```python
from kfp import dsl, local

local.init(runner=local.SubprocessRunner(use_venv=False))

@dsl.component
def identity(text: str) -> str:
    return text

@dsl.pipeline
def identity_pipeline(text: str = "hello") -> str:
    task = identity(text=text)
    return task.output

result = identity_pipeline(text="local")
assert result.output == "local"
```

If `local.init(...)` has not been called, local component/pipeline execution raises an initialization error.

## Runner selection

| Runner | Use when | Avoid when | Main prerequisites |
| --- | --- | --- | --- |
| `SubprocessRunner` | Lightweight Python components and quick authoring feedback. | The graph uses `@dsl.container_component`, non-Python/custom base images, or `target_image` containerized Python components. | Python environment has package dependencies or can install them. |
| `DockerRunner` | You need container semantics, custom images, container components, or stronger runtime isolation. | Docker package or daemon is unavailable, or the task must not start containers. | Python `docker` package and a working Docker daemon. |

`SubprocessRunner` validates that the command is a lightweight Python component. It raises for container components and containerized Python components. It can also warn when the component image does not look Python-based, because subprocess execution cannot reproduce arbitrary image contents.

`DockerRunner` passes supported Docker SDK `containers.run` options through `container_run_args`, except KFP owns `image`, `command`, and `volumes`. Runner-level `environment` values are merged with component env vars, and runner values take precedence.

## Virtualenv and package install behavior

`SubprocessRunner(use_venv=True)` creates a temporary virtual environment for task package installs. This is the default and is safer when tasks have `packages_to_install`.

Parallel local tasks can race on package installation. The inspected SDK exposes:

- `serialize_pip_installs=True` by default for serialized installs.
- `max_concurrent_pip_installs` to bound concurrent installs when serialization is disabled.

Use `use_venv=False` only when the current environment already has the needed runtime packages and you want a faster smoke test.

For component authoring, distinguish:

- `base_image`: the image a backend or Docker runner uses.
- `packages_to_install`: pip packages installed at component runtime.
- `use_venv` on `@dsl.component`: controls the runtime install script inside the component.
- `use_venv` on `SubprocessRunner`: controls local subprocess isolation.

These are related but not interchangeable.

## Local output semantics

When a component or pipeline executes locally, KFP returns a `PipelineTask` in a final state whose outputs are realized values, not compile-time placeholders.

```python
task = identity_pipeline(text="hello")
print(task.output)              # realized value for one output
print(task.outputs["Output"])   # mapping access also works
```

For multiple outputs, always use the output mapping:

```python
result = split_pipeline()
left = result.outputs["left"]
right = result.outputs["right"]
```

Artifact outputs are local artifact objects with `.path`, `.uri`, and `.metadata`. Local tests can open artifact paths directly.

## Task modifiers under local execution

Inside a pipeline body, task modifiers such as `.set_env_variable()`, `.set_retry()`, and `.set_caching_options()` can be part of the graph that local execution runs.

Local behavior to remember:

- `set_env_variable` values are available to the local subprocess/container task.
- `set_retry` can retry failed local tasks according to the retry policy.
- `local.init(..., enable_caching=True)` enables local output caching; `task.set_caching_options(False)` can bypass it for a task.
- CPU, memory, accelerator, and display-name modifiers are Kubernetes/backend metadata. During local execution they may be ignored with warnings rather than changing local resources.
- Some compile-time task methods are blocked after a directly invoked component has already executed and entered final state. Apply task modifiers inside pipeline definitions before local execution, not after direct component calls.

## Control flow locally

The inspected local orchestrator supports common authoring control flow including conditions, loops, nested pipelines, exit handlers, retries, caching, and `dsl.OneOf` for selected branches. Keep local smokes small and deterministic; use compile or service verification for backend-specific behavior.

Example branch output pattern:

```python
@dsl.pipeline
def choose_pipeline(flag: str = "yes") -> str:
    with dsl.If(flag == "yes"):
        yes_task = emit(text="yes")
    with dsl.Else():
        no_task = emit(text="no")
    return dsl.OneOf(yes_task.output, no_task.output)
```

## Workspace and pipeline roots

- `pipeline_root` controls where local task outputs are placed.
- `workspace_root` controls the local workspace path used by workspace placeholders; if omitted, a temporary directory is created.
- `cache_root` controls local cache storage when caching is enabled; if omitted, it defaults under the local pipeline root.

Avoid hard-coding machine-specific absolute paths in reusable examples. Use a temporary directory or a user-provided path.

## DockerRunner troubleshooting signals

- `ImportError` mentioning package `docker`: install the optional Python Docker SDK or switch to `SubprocessRunner` if the flow is a lightweight Python component.
- Error that DockerRunner was selected but docker is not installed: the local package lacks Docker support in the current environment.
- Docker daemon connection errors: the Python package is present but the daemon/socket is unavailable or permissions are insufficient.
- Unsupported Docker run arguments: remove `image`, `command`, `volumes`, or unknown `containers.run` arguments; KFP supplies the task image/command/volumes.

## Runtime SDK caveat

Local and backend component execution use runtime entrypoints. Lightweight component source is executed with `_KFP_RUNTIME=true`, so compile-time symbols such as decorators, compiler objects, clients, and registry APIs are not generally available from `kfp.dsl` inside the component body. Keep authoring code outside the runtime function, and install/import only runtime dependencies inside the component.
