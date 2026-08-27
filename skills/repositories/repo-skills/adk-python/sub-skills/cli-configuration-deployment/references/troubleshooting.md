# ADK CLI, Configuration, and Deployment Troubleshooting

Use this reference when CLI commands fail before an agent turn starts, a server starts but does not list the app, YAML config validation fails, or deployment commands fail before reaching the agent logic.

## `adk web` Does Not List an Agent

Symptoms:

- The Web UI loads but the expected app name is missing.
- Server logs mention import errors, missing `root_agent`, or skipped directories.
- `/list-apps` or the UI returns fewer apps than expected.

Likely causes and fixes:

1. Check the path passed to `adk web`. A parent directory can contain multiple agent subdirectories; a single agent directory must itself contain the entry point.
2. Ensure `__init__.py` imports the `agent` module.
3. Ensure `agent.py` defines `root_agent` or `app` at module import time.
4. Run `adk run path/to/agent --help` and import the package with the same working directory the server uses.
5. If import fails on optional tools, install the required extra or temporarily remove that tool configuration to isolate loader behavior.
6. Inspect verbose logs before debugging model credentials; model credentials are not needed just to discover the app object.

## CLI Command Not Found or Wrong Version

Symptoms:

- `adk: command not found`.
- `adk --version` or `adk --help` does not match expected commands.
- Python imports `google.adk`, but the shell runs another `adk` executable.

Fixes:

- Install `google-adk` into the active environment and ensure its console scripts directory is on `PATH`.
- Run `python -m pip show google-adk` in the same environment used by `adk`.
- Use `python -c "import google.adk; print(google.adk.__version__)"` to confirm the import package.
- Avoid mixing editable source checkouts and globally installed command wrappers when diagnosing user app behavior.

## YAML Config Errors

Symptoms:

- Config load fails with unknown `agent_class`, missing required `name`, invalid callback/tool entries, or schema validation errors.
- Builder endpoints reject YAML keys.
- A YAML app loads but the constructed agent differs from the expected Python version.

Fixes:

1. Inspect installed schema metadata with `scripts/inspect_adk_cli.py --json`.
2. Use `agent_class` values supported by the installed package.
3. Keep fields owned by `LlmAgent` on the agent config itself; do not put system instruction, response schema, or tools inside raw model generation config when ADK exposes dedicated fields.
4. Validate callback and tool code references are importable from the app package.
5. If YAML uploads are blocked by a builder endpoint, remove unsupported arbitrary-code keys and use a Python app for custom logic.

## `adk run` Starts but Agent Behavior Is Wrong

Symptoms:

- Agent outputs JSON instead of calling tools.
- Tool calls are missing from JSONL output.
- State does not persist between runs.

Likely routes:

- Agent schema/tool behavior belongs in `agent-construction`.
- Tool callback and optional toolset behavior belongs in `tools-and-integrations`.
- Session, memory, and artifact persistence belongs in `runtime-services`.
- Evaluation assertions and event summaries belong in `evaluation-debugging`.

CLI checks still help:

```bash
adk run path/to/agent "hello" --in_memory --jsonl
adk run path/to/agent --state '{"debug": true}' --in_memory
```

## Server, Logs, and CORS

Symptoms:

- Browser UI cannot call the API server.
- Cross-origin errors appear in browser logs.
- Server reload fails to pick up agent changes.
- Trace endpoints are empty or cloud traces are missing.

Fixes:

- Use `--allow_origins` for explicit local origins; regex origins must use the CLI's documented regex prefix.
- Use `--reload_agents` for agent source reload; server code reload is separate.
- Check log level flags and the ADK log output location before assuming the agent did not run.
- Cloud tracing requires cloud project/credentials and telemetry options; local debugging can use server trace endpoints when enabled.
- Do not expose development UI publicly without reviewing auth, CORS, service storage, and secret handling.

## Deployment Failures

Symptoms:

- `adk deploy cloud_run`, `agent_engine`, or `gke` fails before serving traffic.
- Generated deployment source is missing dependencies.
- Cloud commands ask for project, region, cluster, service, bucket, or credentials.

Fixes:

1. Run only target-specific `--help` until the user confirms side effects.
2. Confirm project, region/location, service name, app name, and target backend.
3. Confirm generated-source output directory because deploy commands can create or overwrite deployment artifacts.
4. Install cloud/GCP optional dependencies and external CLIs required by the target.
5. Verify credentials outside the agent logic with cloud CLI or ADC checks.
6. For service URIs, confirm DB/GCS/Agent Engine dependencies and permissions before deployment.
7. If the deployment package cannot import optional integrations, add the relevant package extras to the deployment requirements instead of relying on the local development environment.

## Optional Dependency Failures

Symptoms:

- `No module named 'mcp'`.
- `DatabaseSessionService` asks for SQLAlchemy or `google-adk[db]`.
- LiteLLM, Claude, container, GKE, cloud storage, BigQuery, Slack, or toolbox imports fail.

Fixes:

- Treat missing extras as expected for base `google-adk` installs.
- Install the narrow extra needed by the selected workflow, not `all` by default.
- For CLI eval/optimize, use eval/optimization dependencies and model credentials.
- For MCP and toolsets, route detailed setup to `tools-and-integrations`.
- For persistent sessions/artifacts/memory, route storage design to `runtime-services`.

## Safe Stop Conditions

Stop and ask before running commands that:

- Start long-running servers in the user's workspace.
- Rewrite eval/test files with `--rebuild`.
- Deploy or mutate cloud resources.
- Delete or overwrite generated deployment folders.
- Read credentials, secrets, private data, or production databases.
