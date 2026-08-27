# Troubleshooting Serving And Projects

## First Safe Checks

Start with read-only commands:

```bash
mlflow --version
mlflow --help
mlflow server --help
mlflow models serve --help
mlflow deployments --help
mlflow doctor --mask-envs
python skills/mlflow/sub-skills/serving-and-projects/scripts/cli_probe.py --json
# If the console script is unavailable, add: --python-module /path/to/python
```

If a command is missing, check whether the installed MLflow package includes optional integrations and whether the command is conditionally registered.

## Tracking Server Does Not Start

Check these in order:

1. Backend store URI syntax. SQLAlchemy URIs need the driver installed and correct escaping for credentials.
2. Existing `./mlruns` file store. MLflow may choose legacy file-store behavior when a local store already exists; MLflow 3 may require migration or deliberate `MLFLOW_ALLOW_FILE_STORE=true` opt-out.
3. Default artifact root. SQL backend deployments need a coherent artifact location for new experiments.
4. Registry store. If omitted, it follows backend store; separate registry databases need explicit `--registry-store-uri`.
5. Port binding. Another process may already use the selected port.
6. Server option conflicts: `--gunicorn-opts`, `--waitress-opts`, and `--uvicorn-opts` are mutually exclusive; `--dev` conflicts with gunicorn/uvicorn opts and app-name.
7. Workspace flags. Do not set request workspace variables for server startup; use `--enable-workspaces` and `--workspace-store-uri` intentionally.

For shared services, do not retry with a different database URI just to make startup pass; confirm the intended metadata store first.

## Host, CORS, Or Proxy Failures

Symptoms include UI loads but API calls fail, reverse proxy requests receive `400`, browser CORS errors, or a service works from localhost but not via DNS.

Check:

- `--host 0.0.0.0` controls binding but does not by itself authorize every host header.
- `--allowed-hosts` must include the public DNS name, reverse proxy host header, Docker service name, or private IP pattern being used.
- `--cors-allowed-origins` must include browser origins, including scheme and port.
- `--static-prefix` must start with `/` and must not end with `/`.
- Do not use wildcard hosts/origins as a production fix unless the user accepts the security risk.

## Auth App And RBAC Issues

Common causes:

- Missing `mlflow[auth]` extra in the server environment.
- Missing or inconsistent `MLFLOW_FLASK_SERVER_SECRET_KEY`, especially across replicas.
- Server started without `--app-name basic-auth`, so auth enforcement is disabled even though auth data exists.
- Auth database not migrated to the current revision.
- Confusing prompt resources with registered-model resources; their permissions are distinct.
- Legacy pre-RBAC permission scripts against modern MLflow versions where legacy APIs have been removed.

Never run auth DB migrations against production without a backup. Ask for the auth database URI, not just the tracking URI.

## Artifact Store And Model URI Problems

For failed artifact downloads, model serving, or `runs:/` resolution:

- Confirm `MLFLOW_TRACKING_URI` points to the server that owns the run.
- Check the run's artifact URI rather than assuming the server's current default artifact root.
- For proxied artifacts, confirm the server was started with the intended `--serve-artifacts` or `--artifacts-destination`.
- For direct object-store artifact URIs, confirm local credentials are available to the client process.
- For local path model URIs, ensure the process working directory matches the path assumptions.

Route model flavor loading failures, missing `MLmodel` fields, dependency inference, custom pyfunc code, and signature validation to `models-and-flavors`.

## `mlflow run` Failures

Check:

- `MLproject` YAML syntax and entry point name.
- `-P name=value` format and duplicate parameter names.
- Parameter type coercion. `path` may trigger remote downloads; `uri` may become absolute.
- Environment manager choice. Conda, virtualenv, and local reuse fail differently.
- `--backend-config` format. JSON files must end in `.json`; Kubernetes requires backend config.
- Docker flags. `-A gpus=all` becomes a Docker run argument; `-A t` becomes a flag.
- Remote Git version refs and network access.

Use `--env-manager local` only when dependency isolation is intentionally skipped.

## Local Serving Or Prediction Failures

For `mlflow models serve`:

- Confirm the selected port is free and the host is reachable by the client.
- Increase `--timeout` when model import or dependency setup is slow.
- Use `mlflow models predict` first to isolate model loading from HTTP/server issues.
- Validate payload shape: use `dataframe_records`, `dataframe_split`, `inputs`, or `instances` rather than older `columns`/`data` payloads.
- Confirm content type headers for HTTP calls: usually `Content-Type: application/json`.
- Capture server logs before killing the process.

For `mlflow models predict`:

- JSON input should match the same structural keys expected by serving.
- CSV input requires `--content-type csv`.
- Output paths can overwrite or create files; confirm before use.
- Dependency preparation can be slow or require network access unless `--env-manager local` is selected.

## Deployments Failures

Deployment failures are usually target-specific. First run:

```bash
mlflow deployments --help
mlflow deployments help --target <target>
```

Then check:

- Target plugin is installed and listed in help.
- Target URI is correct and credentials are set in the expected environment variables or config.
- `-C key=value` options match the target's documented schema.
- `predict` and `explain` specify exactly one of `--name` or `--endpoint`.
- Input files are JSON or CSV as expected by the command.
- Create/update/delete commands reference the intended resource names.
- Cloud targets may incur cost, create durable resources, or expose models externally.

For SageMaker, Databricks, OpenAI-compatible, and HTTP(S) targets, do not retry blindly; inspect target help and provider logs.

## MCP And Agent Setup Failures

- `mlflow mcp run` starts a server; verify tracking URI and auth first, then inspect client transport expectations.
- `mlflow agent setup` can install files and launch another CLI. Use `--print` to inspect the generated prompt without launching.
- If no supported agent CLI is installed, setup exits with an error listing supported agents.
- If no tracking URI is set, setup may offer to start a local server or configure Databricks/existing server.
- Databricks setup may create or resolve experiment IDs from workspace paths.

## Long-Running Process Hygiene

Before starting any server or serving command, define:

- Host, port, and expected health endpoint.
- Log file location and whether secrets may appear in logs.
- Startup timeout and readiness check.
- Shutdown command or process group cleanup.
- Whether temporary SQLite/artifact directories should persist.

If the user only asked for guidance or diagnosis, provide commands but do not start processes.
