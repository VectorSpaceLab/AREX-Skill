# ADK CLI Reference

ADK exposes the `adk` console script. In ADK 2.3.0 the verified top-level commands are `api_server`, `conformance`, `create`, `deploy`, `eval`, `eval_set`, `migrate`, `optimize`, `run`, `test`, and `web`.

## Safe Inspection Commands

Use these checks before making changes or starting services:

```bash
adk --help
adk run --help
adk web --help
adk api_server --help
adk test --help
adk eval --help
adk eval_set --help
adk deploy --help
python path/to/scripts/inspect_adk_cli.py --json
```

The bundled `scripts/inspect_adk_cli.py` uses subprocess help calls and package-resource inspection only. It does not import user agents, start servers, create sessions, deploy, contact cloud services, or read credentials.

## Command Families

| Command | Primary use | Mutating or long-running behavior | Notes |
| --- | --- | --- | --- |
| `adk create APP_NAME` | Scaffold an agent app folder. | Writes files under the target app path. | Options include `--model`, `--api_key`, `--project`, and `--region`; avoid embedding real secrets in generated examples. |
| `adk run AGENT [QUERY]` | Run one agent locally, interactively or one-shot. | Interactive mode can create local `.adk` storage unless `--in_memory` or storage URIs are used. | `AGENT` is a path to one agent folder. A supplied `QUERY` performs a single-step run. |
| `adk web [AGENTS_DIR]` | Start FastAPI plus the ADK Web UI for local development. | Starts a long-running local server. | `AGENTS_DIR` can be a directory containing many app subdirectories or one single-agent folder. |
| `adk api_server [AGENTS_DIR]` | Start FastAPI endpoints without requiring the full web UI. | Starts a long-running local server. | Supports `--with_ui`, `--auto_create_session`, A2A, triggers, plugins, service URIs, and CORS options. |
| `adk test [FOLDER]` | Run JSON agent test files through the packaged test runner. | Runs pytest; `--rebuild` rewrites test files by running the real agent. | Additional pytest args go after `--`. Keep assertion design details in the evaluation/debugging sub-skill. |
| `adk eval AGENT_MODULE_FILE_PATH [EVAL_SET...]` | Evaluate an app against eval sets. | Runs agent/model inference and can use local or GCS eval storage. | Requires eval dependencies and model credentials; supports `--config_file_path`, `--eval_storage_uri`, and `--print_detailed_results`. |
| `adk eval_set ...` | Create, add, or generate eval cases. | Writes eval-set records; generation may call Vertex AI Eval SDK. | Subcommands include `create`, `add_eval_case`, and `generate_eval_cases`. |
| `adk optimize ...` | Optimize root-agent instructions with GEPA. | Runs model/eval workloads. | Requires eval/optimization dependencies and config files. |
| `adk deploy cloud_run AGENT` | Generate and deploy to Cloud Run. | Calls Google Cloud tooling and creates deployment artifacts. | Confirm project, region, service name, auth, storage services, UI exposure, and extra `gcloud` args. |
| `adk deploy agent_engine AGENT` | Deploy to Vertex AI Agent Engine or Express Mode. | Uses cloud credentials/API key and deployment staging. | Confirm project/region or API key, Agent Engine id/update semantics, and cloud extras. |
| `adk deploy gke AGENT` | Generate and deploy to GKE. | Uses Google Cloud/Kubernetes credentials and cluster resources. | Confirm project, region, cluster, service type, and ingress exposure. |
| `adk migrate session` | Migrate session database schema. | Reads and writes databases. | Requires source and destination DB URLs; route persistence design to runtime-services. |
| `adk conformance ...` | Record or replay conformance cases. | Reads/writes conformance fixtures and can run agents. | Intended for behavior consistency checks, not everyday app use. |

## `adk run`

Typical safe flows:

```bash
adk run path/to/my_agent --help
adk run path/to/my_agent "hello" --in_memory --jsonl
adk run path/to/my_agent --in_memory
```

Important options:

- `--replay FILE`: Create a fresh session from an input JSON file containing `state` and `queries`; cannot be combined with `--resume`.
- `--resume FILE`: Redisplay and continue a previously saved session; cannot be combined with `--replay`.
- `--state JSON`: Provide initial state for the run.
- `--timeout 30s` or `--timeout 5m`: Bound a single turn/query.
- `--in_memory`: Avoid local persistent session/artifact storage.
- `--jsonl`: Print structured JSONL events instead of human-readable output.
- `--default_llm_model MODEL`: Set a default LLM model for agents that do not configure one.
- `--session_service_uri`, `--artifact_service_uri`, `--memory_service_uri`, `--use_local_storage/--no-use_local_storage`: Choose storage backends.

Inputs and outputs:

- `AGENT` is a filesystem path to an agent folder, not an import string.
- If a `QUERY` argument is provided, ADK runs one turn and exits.
- Without `QUERY`, ADK enters an interactive loop and exits on `exit`.
- JSONL output includes event fields such as `author`, `session_id`, `node_path`, and event ids when available.

## `adk web` and `adk api_server`

Both server commands use the same agent loader and service factory. Defaults are development-friendly, not production-hardened.

Common options:

- `--host` and `--port`: Bind address and port, defaulting to local development values.
- `--allow_origins ORIGIN`: Repeatable CORS allow-list; values can be literal origins or regex patterns prefixed with `regex:`.
- `--reload/--no-reload`: Enable or disable server reload; reload is disabled on Windows when subprocess support would break.
- `--reload_agents`: Enable live reload for agent source changes.
- `--url_prefix /path`: Serve behind a reverse proxy or gateway prefix.
- `--a2a`: Enable A2A endpoints.
- `--extra_plugins MODULE.OBJECT`: Add plugin classes or instances.
- `--trigger_sources pubsub,eventarc`: Register trigger endpoints for batch/event-driven invocations.
- `--trace_to_cloud` and `--otel_to_cloud`: Cloud telemetry options; prefer `--otel_to_cloud` for newer flows.
- `--session_service_uri`, `--artifact_service_uri`, `--memory_service_uri`, `--use_local_storage/--no-use_local_storage`: Select runtime services.

`adk web` adds UI options:

- `--logo-text TEXT`
- `--logo-image-url URL`
- `--default_llm_model MODEL`

`adk api_server` adds API-server options:

- `--auto_create_session`: Create sessions automatically for `/run` calls when missing.
- `--with_ui`: Serve the web UI from the API server.
- `--gemini_enterprise_app_name` and `--express_mode`: Gemini Enterprise registration/express-mode integration.

Expected server API concepts:

- App listing depends on `AgentLoader.list_agents_detailed()` successfully importing/loading each app.
- Graph visualization serializes the loaded root `Agent`, `Workflow`, sub-agents, tools, graph nodes, and graph edges; missing graph nodes usually mean the loaded app object lacks the expected `root_agent`/graph structure.
- Builder endpoints only accept YAML/YML files and block some keys in uploaded YAML to reduce arbitrary-code execution risk.

## `adk test`, `adk eval`, and `adk eval_set`

Use this sub-skill for CLI mechanics and storage paths; route assertion design, event interpretation, metric selection, and flaky eval diagnosis to evaluation-debugging.

`adk test`:

```bash
adk test path/to/agents
adk test path/to/agents -- --maxfail=1 -q
adk test path/to/agents --rebuild
```

- `FOLDER` defaults to the current directory.
- Normal mode runs the packaged JSON test runner through pytest.
- `--rebuild` runs the real agent with user messages and rewrites tests; confirm before using it.
- Arguments after `--` pass through to pytest.

`adk eval`:

```bash
adk eval path/to/my_app path/to/eval_set.json
adk eval path/to/my_app eval_set_id:case_a,case_b --config_file_path eval_config.json
adk eval path/to/my_app eval_set_id --eval_storage_uri gs://bucket
```

- `AGENT_MODULE_FILE_PATH` is a directory path whose basename becomes the app name.
- Eval set file paths and eval set IDs cannot be mixed in the same command.
- File or ID suffix `:eval_1,eval_2` narrows which cases run.
- Missing eval dependencies are expected in base installs; install the appropriate eval extras before using eval/optimize workflows.

`adk eval_set` subcommands:

- `adk eval_set create AGENT_MODULE_FILE_PATH EVAL_SET_ID`
- `adk eval_set add_eval_case AGENT_MODULE_FILE_PATH EVAL_SET_ID --scenarios_file scenarios.json --session_input_file session.json`
- `adk eval_set generate_eval_cases AGENT_MODULE_FILE_PATH EVAL_SET_ID --user_simulation_config_file config.json`

## Deployment Commands

Deployment commands are side-effecting. Do not run them as diagnostics. First use `adk deploy --help` and target-specific `--help`.

### Cloud Run

```bash
adk deploy cloud_run --project PROJECT --region REGION path/to/my_agent
adk deploy cloud_run --project PROJECT --region REGION path/to/my_agent -- --min-instances=2
```

Key options:

- `--project`, `--region`, `--service_name`, `--app_name`, `--port`.
- `--with_ui`: Deploy the Web UI; warning: development/testing only, not production UI.
- `--temp_folder`: Generated source location; command may create or overwrite generated deployment files there.
- `--adk_version`: Version to pin in generated deployment.
- `--a2a`, `--trigger_sources`, `--allow_origins`, service URI options, and telemetry flags.
- Use `--` to separate extra `gcloud` arguments. Unexpected extra args before `--` are usage errors.

### Agent Engine

```bash
adk deploy agent_engine --project PROJECT --region REGION --display_name NAME path/to/my_agent
adk deploy agent_engine --api_key API_KEY projects/PROJECT/locations/LOCATION/reasoningEngines/ID
```

Key options:

- `--api_key` for Express Mode; otherwise use project/region credentials.
- `--agent_engine_id` to update an existing engine or identify a resource.
- `--display_name`, `--description`, `--agent_engine_config_file`.
- `--temp_folder` can remove existing generated source contents; confirm before using.
- Deprecated flags include `--staging_bucket`, `--adk_app`, `--adk_app_object`, `--env_file`, `--requirements_file`, `--absolutize_imports`, and import-validation aliases.
- Service URI and telemetry options are available; base installs may lack GCP extras.

### GKE

```bash
adk deploy gke --project PROJECT --region REGION --cluster_name CLUSTER path/to/my_agent
```

Key options:

- `--project`, `--region`, `--cluster_name`, `--service_name`, `--app_name`, `--port`.
- `--service_type ClusterIP|LoadBalancer` controls whether the Kubernetes Service remains internal or is publicly exposed.
- `--with_ui` carries the same development/testing warning.
- `--temp_folder`, `--adk_version`, `--trigger_sources`, service URI options, and telemetry flags.

## Service URI Options

CLI/server commands can construct runtime services from URIs through the service registry:

- Session schemes: `memory://`, `sqlite://...`, `agentengine://...`, and SQLAlchemy-style database schemes such as `postgresql://...` or `mysql://...` when dependencies are installed.
- Artifact schemes: `memory://`, `file:///absolute/path`, and `gs://bucket` when GCS dependencies and credentials are available.
- Memory schemes: `memory://`, `rag://RAG_CORPUS`, and `agentengine://...` when cloud dependencies and credentials are available.
- A2A task-store schemes include memory and async DB schemes when A2A dependencies are installed.

Custom service registration:

- `services.yaml` or `services.yml` under the agent directory can register service factories by `scheme`, `type`, and `class`.
- `services.py` under the agent directory can call `get_service_registry()` and register custom factory functions.
- If both YAML and Python registration exist, YAML loads first and `services.py` can override duplicate schemes.

## Optional Dependency Assumptions

A base `google-adk` install can omit optional extras. Diagnose these as environment facts, not user mistakes:

- Eval/optimization commands may need eval-related packages.
- Database services may need DB dependencies such as SQLAlchemy and drivers.
- `adk deploy` cloud targets may need GCP/cloud packages and external CLIs/credentials.
- MCP, extensions, A2A, Slack, toolbox, and cloud integrations are optional extras.

## Config Schema Generation Context

`AgentConfig.json` is generated from Pydantic config models using a custom schema generator that falls back for types that cannot be represented directly in JSON Schema. For users generating YAML, prefer validating against the installed package schema rather than relying on a source checkout. For repository maintainers regenerating the schema file, route to repo-development.
