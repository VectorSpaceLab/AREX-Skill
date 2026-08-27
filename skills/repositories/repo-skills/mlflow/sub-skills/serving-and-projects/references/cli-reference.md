# MLflow CLI Reference

## Entry Point And Command Discovery

MLflow installs the `mlflow` console script from `mlflow.cli:cli`. The top-level CLI supports `--version` and an optional `--env-file` that loads dotenv variables before command execution without overriding existing environment variables.

Expected top-level groups in this repo generation include:

- Core operation: `server`, `ui` alias, `run`, `models`, `deployments`, `db`, `artifacts`, `experiments`, `runs`.
- Observability/data/admin surfaces: `traces`, `datasets`, `scorers`, `doctor`, `migrate-filestore`, `ai-commands`, `skills`, `demo`, `crypto` when available.
- Integration surfaces: `mcp`, `agent`, `assistant`, Claude Code/autolog integrations when optional imports are available.

Use help probes instead of importing private internals when possible:

```bash
mlflow --version
mlflow --help
mlflow server --help
mlflow run --help
mlflow models --help
mlflow models serve --help
mlflow deployments --help
mlflow deployments help --target databricks
mlflow mcp --help
mlflow agent setup --help
mlflow doctor --mask-envs
```

For automated inspection, run the bundled safe probe. If the `mlflow` console script is not on `PATH`, add `--python-module /path/to/python` to run `python -m mlflow` instead.

```bash
python skills/mlflow/sub-skills/serving-and-projects/scripts/cli_probe.py \
  --commands mlflow "mlflow server" "mlflow models serve" "mlflow deployments"
```

## Side-Effect Levels

- Safe read-only: `mlflow --version`, `mlflow <group> --help`, `mlflow deployments help --target <target>`, and `mlflow doctor --mask-envs`.
- Local filesystem mutation: `mlflow run` with local backend, `mlflow models predict` with output path, `mlflow models prepare-env`, `mlflow models generate-dockerfile`, `mlflow artifacts download`, and most commands that write outputs.
- Long-running local processes: `mlflow server`, `mlflow ui`, `mlflow models serve`, `mlflow gateway start`, `mlflow mcp run`, and repo development server commands.
- Database mutation: `mlflow db upgrade`, auth DB upgrade, tracking server startup against SQL stores that initialize schema, and migration helpers.
- External or costly side effects: `mlflow deployments create/update/delete`, SageMaker, Docker build/run, Kubernetes, Databricks project backends, and cloud artifact stores.

When a command is not read-only, confirm the target URI, workspace, credentials, ports, output paths, expected duration, and cleanup behavior.

## `mlflow run` And Projects CLI

`mlflow run URI` executes an MLflow Project from a Git URI or local path. Important options:

- `-e/--entry-point`: entry point name; default is `main`.
- `-P/--param-list NAME=VALUE`: project parameters; repeated values for the same name are rejected.
- `--backend local|databricks|kubernetes`: local blocks until complete; Databricks runs remotely; Kubernetes is experimental and requires backend config.
- `-c/--backend-config`: JSON file ending in `.json` or a JSON string; Kubernetes requires it.
- `--env-manager`: controls environment creation; use `local` or equivalent only when the current Python environment is intentionally reused.
- `-A/--docker-args NAME=VALUE` or `-A FLAG`: passes Docker run arguments for Docker projects.
- `--build-image`: builds a new Docker image for Docker projects.

Do not run remote Git projects, Docker projects, Kubernetes backends, or Databricks backends without explicit approval. Route experiment selection and run lifecycle questions to `tracking-and-registry`.

## `mlflow server` And `mlflow ui`

`mlflow ui` is an alias for `mlflow server`. Key option families:

- Storage: `--backend-store-uri`, `--read-replica-backend-store-uri`, `--registry-store-uri`, `--default-artifact-root`, `--serve-artifacts`, `--artifacts-only`, `--artifacts-destination`.
- Network: `--host`, `--port`, `--workers`, `--static-prefix`.
- Security: `--allowed-hosts`, `--cors-allowed-origins`, `--x-frame-options`, `--disable-security-middleware`.
- Runtime: `--gunicorn-opts`, `--waitress-opts`, `--uvicorn-opts`, `--dev`, `--expose-prometheus`, `--app-name`.
- Advanced: `--trace-archival-config`, `--secrets-cache-ttl`, `--secrets-cache-max-size`, `--workspace-store-uri`, `--enable-workspaces`.

Important validation behavior:

- `--dev` is for development only, uses uvicorn reload/debug, is unsupported on Windows, and cannot be combined with `--gunicorn-opts`, `--uvicorn-opts`, or `--app-name`.
- `--gunicorn-opts`, `--waitress-opts`, and `--uvicorn-opts` are mutually exclusive.
- Security middleware options for allowed hosts/CORS are supported with the default uvicorn path; do not combine command-line security options with gunicorn/waitress modes.
- If no backend store URI is supplied, MLflow uses the default local tracking URI and reports it.

## `mlflow models` CLI

The models group deploys or invokes MLflow Models locally. It is operational, not just metadata inspection:

- `serve -m MODEL_URI --port PORT --host HOST --timeout SECONDS --workers N --env-manager ...`: starts a web server exposing `/invocations`.
- `predict -m MODEL_URI --input-path PATH --content-type json|csv --output-path PATH --env-manager ...`: runs local prediction and may prepare dependencies.
- `prepare-env -m MODEL_URI`: downloads/prepares dependencies so later serve/predict is faster.
- `generate-dockerfile -m MODEL_URI --output-directory DIR`: writes a Dockerfile directory.
- `build-docker -m MODEL_URI --name IMAGE`: builds a Docker image and may require Docker daemon/network.
- `update-pip-requirements -m MODEL_URI add|remove REQUIREMENTS...`: mutates model dependency files and does not support `models:/` registry URIs.

For payload formats, modern serving accepts JSON with one of `dataframe_split`, `dataframe_records`, `inputs`, or `instances`. Older MLflow 1.x `columns/data` payloads usually require migration.

## `mlflow deployments` CLI

The deployments group delegates to target plugins. Installed targets verified for this generated skill include `databricks`, `http`, `https`, `openai`, and `sagemaker`, but future environments may differ. Always probe `mlflow deployments --help` and `mlflow deployments help --target <target>`.

Commands include:

- Deployment lifecycle: `create`, `update`, `delete`, `list`, `get`, `run-local`.
- Invocation: `predict`, `explain` using `--input-path` and optional `--output-path`.
- Endpoint lifecycle: `create-endpoint`, `update-endpoint`, `delete-endpoint`, `list-endpoints`, `get-endpoint`.

Target-specific config uses `-C/--config NAME=VALUE`; repeated keys are rejected. `predict` and `explain` require exactly one of `--name` or `--endpoint`. Treat create/update/delete and cloud-backed predict/explain as external side effects.

## Auth, DB, MCP, Agent, And Doctor Commands

- `mlflow db upgrade <db_uri>` and related DB commands mutate tracking database schema. Require explicit target and backup.
- Auth DB command group is available under the auth app internals and performs `upgrade --url URI --revision head`; only run against intended auth stores.
- `mlflow mcp run` starts an MCP server for exposing MLflow trace operations to MCP-compatible clients; treat as a long-running local process.
- `mlflow agent setup` is experimental. It may install MLflow skills into an agent directory, choose or start tracking backends, prompt for Databricks experiments, and launch an agent CLI unless `--print` is used.
- `mlflow doctor --mask-envs` is a safe first diagnostic because it masks MLflow environment variable values.
