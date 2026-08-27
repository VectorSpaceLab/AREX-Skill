# Projects, Deployments, Model Serving, MCP, And Development Server

## MLflow Projects

An MLflow Project is a directory or Git repository that can be run with `mlflow run`. It may include an `MLproject` file for explicit metadata, entry points, parameters, and environment definitions. Without an `MLproject` file, MLflow can infer entry points from `.py` and `.sh` files.

Typical `MLproject` concepts:

- Project name: human-readable identifier.
- Entry points: named commands, usually `main`, each with parameters and a command string.
- Parameter types: `string`, `float`, `int`, `path`, and `uri`.
- Environments: `python_env`, `conda_env`, `docker_env`, or current/system environment through the selected environment manager.

Safe local dry-run planning:

```bash
mlflow run . --help
mlflow run . -e main -P alpha=0.5 --env-manager local
```

Only run the second command when the current directory is the intended project and reusing the current Python environment is acceptable. For remote Git URIs, Docker projects, Databricks, or Kubernetes backends, confirm network, credentials, image builds, and compute cost first.

## Environment Managers And Project Failure Modes

Common MLproject execution failures:

- Missing `MLproject`, wrong entry point, or inferred `.py`/`.sh` entry point mismatch.
- Invalid `-P NAME=VALUE` syntax, repeated parameters, or values that fail declared type coercion.
- `path` parameters downloading remote artifacts into `--storage-dir`; missing cloud credentials can look like project failures.
- Conda terms or unavailable Conda binary when `conda_env` is selected.
- Virtualenv creation failures due Python version constraints or package resolver/network issues.
- Docker daemon unavailable, image build failures, missing volumes, or GPU flags passed through `-A` incorrectly.
- Databricks and Kubernetes backends requiring backend config, workspace credentials, or cluster permissions.

If the task is about how runs, experiments, nested runs, parameters, metrics, or artifact logging behave after launch, route to `tracking-and-registry`.

## Local Model Serving

`mlflow models serve` starts a local web server for an MLflow model, usually a pyfunc model. It requires a model URI and may prepare dependencies.

Planning checklist:

- Confirm model URI: local path, `runs:/...`, or supported artifact URI.
- Confirm tracking URI if the model URI depends on a tracking server.
- Choose host/port and timeout; avoid port conflicts.
- Choose `--env-manager local` only when the current environment already has required dependencies.
- Capture logs and define cleanup for long-running processes.

Example request payloads for `/invocations` use one of these JSON shapes:

```json
{"dataframe_records": [{"a": 1, "b": 2}]}
```

```json
{"dataframe_split": {"columns": ["a", "b"], "data": [[1, 2]]}}
```

```json
{"inputs": [[1, 2], [3, 4]]}
```

```json
{"instances": [{"a": "x", "b": [1, 2, 3]}]}
```

Use `mlflow models predict` for one-shot local prediction from a JSON or CSV input file. It is easier to validate than a server when debugging payload shape, but it can still create environments or write output files.

Route flavor-specific save/load requirements, signatures, conda/pip inference, custom pyfunc code paths, and model packaging details to `models-and-flavors`.

## Docker Model Serving

`mlflow models generate-dockerfile` writes a Dockerfile directory. `mlflow models build-docker` builds an image with a serving entry point, often on port `8080` inside the container. Docker operations can download packages, consume disk, use network, and build architecture-specific images.

Do not build or run Docker unless local Docker availability and side effects are approved. If Docker is unavailable, use generated Dockerfile inspection or CLI help only.

## Deployments And Targets

`mlflow deployments` is a plugin-facing interface. The verified target list for this generated skill includes `databricks`, `http`, `https`, `openai`, and `sagemaker`; always probe the live environment because plugins can add or remove targets.

Target-specific decision flow:

1. Run `mlflow deployments --help` and `mlflow deployments help --target <target>`.
2. Identify whether the command is local (`run-local`), metadata read (`list`, `get`, `list-endpoints`, `get-endpoint`), invocation (`predict`, `explain`), or lifecycle mutation (`create`, `update`, `delete`, endpoint create/update/delete).
3. Confirm `--target`, `--name` or `--endpoint`, `--model-uri`, input files, and all `-C key=value` config values.
4. Confirm credentials and network for Databricks, OpenAI-compatible, HTTP(S), SageMaker, or custom targets.
5. Avoid lifecycle mutation unless the user explicitly approves the target and resource names.

Cloud deployment examples are useful as patterns but should be treated as reference-only unless credentials and cloud cost boundaries are explicit.

## Gateway Notes

The older `mlflow gateway start` style command starts a gateway service from a config file and can proxy model-provider traffic. Gateway resources are also represented in server/auth handlers for secrets, endpoints, model definitions, guardrails, and budget policies. Starting a gateway or mutating gateway resources can call provider APIs and should not be used as a probe.

For GenAI trace/eval semantics, route to `genai-observability`; for server auth over gateway resource permissions, use `server-and-auth.md`.

## MCP Server

`mlflow mcp run` starts an MCP server for MLflow trace operations so MCP-compatible clients can interact with MLflow. Treat it as a long-running server process:

- Confirm the tracking URI and auth context first.
- Confirm whether the client expects stdio, HTTP, or another transport from the installed version.
- Capture logs and define shutdown behavior.
- Do not expose trace data to an agent/client without user approval.

## Agent Setup

`mlflow agent setup` is experimental. It can:

- Detect installed coding-agent CLIs.
- Offer to install MLflow skills into a project-local agent skills directory.
- Choose a tracking backend: new local server, Databricks workspace, or existing server URL.
- Prompt for Databricks experiment IDs or paths.
- Print a composed prompt with `--print`, or launch the selected agent without `--print`.

Prefer `mlflow agent setup --agent <agent> --print` when reviewing behavior safely. Do not allow it to install files or launch another interactive agent unless the user asked for that setup flow.

## Repository Development Server Workflow

The repo development helper starts both an MLflow tracking backend and the React frontend development server. It is reference-only for this runtime skill because it is specific to an MLflow source checkout and frontend tooling.

Behavior to remember when working inside a checkout:

- It picks free backend and frontend ports near `5000` and `3000`.
- If `MLFLOW_TRACKING_URI` or `MLFLOW_BACKEND_STORE_URI` is set, it proxies to that backend store and uses `mlruns` as the default artifact root.
- Otherwise, it creates temporary SQLite and artifact directories and cleans them up on exit.
- It starts the tracking server with `python -m mlflow server ... --dev --port <port>`.
- It starts the React app with `MLFLOW_PROXY` pointing at the backend and `MLFLOW_DEV_PROXY_MODE=1`.
- For Databricks proxy development, set `DATABRICKS_HOST`, `DATABRICKS_TOKEN`, `MLFLOW_TRACKING_URI=databricks`, and an appropriate `MLFLOW_REGISTRY_URI` before startup.

Do not start this helper from a generated skill. In a repository task, follow the repository's own development instructions and use a log file plus cleanup plan.
