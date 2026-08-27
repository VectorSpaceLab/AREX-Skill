# Code Executors and Runtime Extensions

`autogen_ext.code_executors.*` provides code execution backends. `autogen_ext.runtimes.grpc` provides distributed worker runtime extension surfaces. This reference is about installation, safety, and backend diagnostics; route routed-agent protocol and subscription design to `core-runtime`.

## Executor Selection

| Backend | Extra | Public imports | Primary risk/dependency |
| --- | --- | --- | --- |
| Local command line | base install | `LocalCommandLineCodeExecutor` | Executes on the host; trusted-code only |
| Docker command line | `docker` | `DockerCommandLineCodeExecutor` | Docker daemon, image, container lifecycle, mounted work dir |
| Local Jupyter | `jupyter-executor` | `JupyterCodeExecutor`, `JupyterCodeResult` | Starts local kernels; output directory and timeout management |
| Docker Jupyter gateway | `docker-jupyter-executor` | `DockerJupyterServer`, `DockerJupyterCodeExecutor`, `JupyterClient`, `JupyterKernelClient` | Docker plus Jupyter gateway, token/port/image handling |
| Azure Container Apps Dynamic Sessions | `azure` | `ACADynamicSessionsCodeExecutor`, `TokenProvider` | Azure endpoint, credential, auth roles, pool availability |
| Code executor as tool | executor-specific | `PythonCodeExecutionTool` | Inherits backend execution risk |
| gRPC worker runtime | `grpc` | `GrpcWorkerAgentRuntime`, `GrpcWorkerAgentRuntimeHost`, `GrpcWorkerAgentRuntimeHostServicer` | gRPC/protobuf dependencies and host/worker topology |

## Local Command Line Executor

`LocalCommandLineCodeExecutor` is available without extras and supports Python and shell-family languages. It writes code blocks to files and runs them as subprocesses. It has some command sanitization, but it still executes on the local machine.

Use only when:

- The code is trusted or has been reviewed.
- `work_dir` is isolated and disposable.
- Timeouts are explicit and at least 1 second.
- The caller understands generated code can read/write files and use the host network/process environment.

If using functions, validate `functions_module` is a valid Python identifier and that extra function requirements are installed in the executor environment.

## Docker Command Line Executor

`DockerCommandLineCodeExecutor` requires `autogen-ext[docker]`. Import failures usually mean the extra is absent. Runtime failures commonly mean Docker is not installed/running, the image cannot be pulled/built, the container failed to start, or the work directory/container cleanup policy is invalid.

Constructor/usage checks:

- `timeout >= 1`.
- Avoid `work_dir="."`; it is deprecated and weakens isolation.
- Review `image`, `container_name`, `auto_remove`, `delete_tmp_files`, `extra_hosts`, and any mounted data.
- Start with an async context manager or `start()` before executing; otherwise execution raises that the container is not running.
- `create_default_code_executor()` prefers Docker when available and falls back to local with a warning if Docker is missing or unavailable.

Do not ping Docker or start containers during import-only diagnosis. Run Docker tests only in an environment where container execution is explicitly allowed.

## Jupyter Executors

`JupyterCodeExecutor` requires `autogen-ext[jupyter-executor]`. It starts local Jupyter kernel resources when used. Validate kernel name, timeout, and output directory. Execution before startup raises `RuntimeError("Executor must be started before executing cells")`.

`DockerJupyterServer` and `DockerJupyterCodeExecutor` require `autogen-ext[docker-jupyter-executor]`. The server can build or use a Docker image and expose a Jupyter gateway. Validate:

- Docker daemon availability.
- Custom image existence if `custom_image_name` is supplied.
- Token and exposed port policy.
- Kernel name availability; missing kernels raise a kernel-not-installed error.
- Gateway connection info when using an existing `JupyterConnectionInfo`.

## Azure Container Apps Dynamic Sessions

`ACADynamicSessionsCodeExecutor` requires `autogen-ext[azure]`. It executes code in Azure dynamic sessions and needs a pool management endpoint plus a credential, commonly from Azure Identity. This is an external service-backed executor, not an import-only surface.

Check before use:

- `pool_management_endpoint` points to the intended session pool.
- Credential type is async/sync compatible with the executor path and has required Azure permissions.
- Upload/workdir behavior does not expose unintended local files.
- Tests requiring a real pool should be skipped unless `POOL_ENDPOINT`-style configuration and Azure auth are explicitly provided.

## gRPC Worker Runtime Extension

`autogen_ext.runtimes.grpc` requires `autogen-ext[grpc]` and exports worker runtime, host, and host servicer classes. Use it when an AutoGen Core distributed runtime design needs the packaged gRPC transport components. Route message handler, topic, subscription, serialization, and worker architecture questions to `core-runtime`.

Safe checks:

- Import `autogen_ext.runtimes.grpc` and verify `grpcio` is installed.
- Confirm package versions match the AutoGen Core version used by workers and host.
- Do not start worker hosts or bind ports during import/spec inspection.

## Test Candidate Classification

- Local executor tests are usually safe only in a disposable workspace and still execute shell/Python code.
- Docker executor tests require Docker and may pull/start containers.
- Jupyter executor tests start kernels and write outputs.
- Docker-Jupyter tests require Docker plus network ports and image/gateway lifecycle.
- Azure Dynamic Sessions tests require Azure credentials and a live pool endpoint.

Use the bundled inspection script for package-level checks before any native executor test selection.
