# Project initialization

Use this reference to plan and inspect `sam init` output. It is intentionally dry-run oriented: it describes files and decisions without starting brokers, LLM calls, gateways, or the Web UI.

## Initialization surfaces

| Surface | Command shape | Use when | Operating notes |
| --- | --- | --- | --- |
| Browser portal | `sam init --gui` | A human wants guided setup for providers, broker, gateway, and environment values. | Starts a local configuration portal at `http://127.0.0.1:5002`; the CLI resumes only after the portal submits data or exits. |
| Terminal prompts | `sam init` | A human wants to answer prompts in the shell. | First asks whether to use the browser portal; choosing browser follows the same portal path. |
| Automation | `sam init --skip ...` | CI, scripted examples, or deterministic fixtures. | Uses supplied flags or defaults. If `--gui` and `--skip` are combined, CLI mode wins and a warning is emitted. |
| Docker init | official image with mounted project directory | A user does not want a local Python install. | Map port `5002` for GUI setup. Avoid the "new local broker container" choice from inside the SAM container. |

`sam init` always targets the current working directory. Create and enter a clean project directory first.

## Main initialization sequence

Current SAM initialization orchestrates these steps:

1. Broker setup.
2. Project directory creation.
3. Standard project files.
4. Main orchestrator, shared config, and logging config.
5. Optional Web UI gateway config.
6. Optional platform service config bundled with Web UI.
7. `.env` creation.

The generated files should be reviewed before any live run.

## Expected generated layout

```text
sam-project/
├── .env
├── requirements.txt
├── configs/
│   ├── shared_config.yaml
│   ├── logging_config.yaml
│   ├── agents/
│   │   └── main_orchestrator.yaml
│   ├── gateways/
│   │   └── webui.yaml              # present when Web UI gateway is enabled
│   └── services/
│       └── platform.yaml           # present when Web UI gateway is enabled
└── src/
    └── __init__.py
```

`sam add gateway` later creates additional `src/<gateway_name>/` packages and `configs/gateways/<gateway_name>_config.yaml`. `sam add agent` and `sam add proxy` create additional YAML files under `configs/agents/`.

## `sam init` flags that matter for automation

| Concern | Important flags | Resulting files/fields |
| --- | --- | --- |
| Non-interactive mode | `--skip` | Uses defaults for anything not provided. |
| Browser mode | `--gui` | Starts local portal on port `5002`; not compatible with `--skip`. |
| Broker mode | `--broker-type`, `--dev-mode`, `--broker-url`, `--broker-vpn`, `--broker-username`, `--broker-password`, `--container-engine` | Writes broker values into `.env`; shared config reads them through `${SOLACE_*}` variables. |
| Namespace | `--namespace` | Writes `NAMESPACE`; `.env` normalization appends a trailing `/` when a non-default namespace omits it. |
| Orchestrator identity | `--agent-name`, `--supports-streaming` | Writes `configs/agents/main_orchestrator.yaml`; orchestrator names must contain only letters, numbers, and underscores. |
| Artifact service | `--artifact-service-type`, `--artifact-service-base-path`, `--artifact-service-bucket-name`, `--artifact-service-endpoint-url`, `--artifact-service-region`, `--artifact-service-scope`, `--artifact-handling-mode` | Configures shared default artifact service and orchestrator artifact handling. |
| Agent card/discovery | `--agent-card-description`, input/output modes, discovery and inter-agent flags | Configures orchestrator agent card publication and inter-agent allow/deny behavior. |
| Web UI gateway | `--add-webui-gateway`, `--webui-*` flags | Creates `configs/gateways/webui.yaml`, writes `FASTAPI_*`, frontend, SSL, and session settings to `.env`. |
| Platform service | `--platform-api-host`, `--platform-api-port` | Creates `configs/services/platform.yaml` when Web UI is enabled and writes `PLATFORM_*` values to `.env`. |
| Model values | `--llm-service-endpoint`, `--llm-service-api-key`, `--llm-service-planning-model-name`, `--llm-service-general-model-name` | Writes model-related `.env` values when a provider is selected in the flow; verify the generated `shared_config.yaml` contains model anchors before relying on them. |

## Broker choices

| Choice | CLI values | What it means | Safe planning guidance |
| --- | --- | --- | --- |
| Existing broker | `1` or `solace` | Use a reachable Solace Pub/Sub+ broker. | Requires URL, VPN, username, and password. Do not probe the broker from this sub-skill. |
| New local broker container | `2` or `container` | CLI attempts to run a local Solace broker container using Docker or Podman. | This has live side effects and is outside dry validation. In Docker-based SAM initialization, do not choose this mode. |
| Dev mode | `3`, `dev`, `dev_mode`, or `--dev-mode` | Uses an all-in-one development broker behavior. | Suitable for local development planning; not production. |

The shared config template uses:

```yaml
broker_connection: &broker_connection
  dev_mode: ${SOLACE_DEV_MODE, false}
  broker_url: ${SOLACE_BROKER_URL, ws://localhost:8008}
  broker_username: ${SOLACE_BROKER_USERNAME, default}
  broker_password: ${SOLACE_BROKER_PASSWORD, default}
  broker_vpn: ${SOLACE_BROKER_VPN, default}
  temporary_queue: ${USE_TEMPORARY_QUEUES, true}
```

Temporary queues are the default. For deployments with multiple instances of the same agent, durable queues may be needed; that is a deployment/runtime decision, not a bootstrap dry-check.

## Shared configuration

`configs/shared_config.yaml` is the central anchor file included by generated app configs. Generated app files should keep a relative include such as:

```yaml
!include ../shared_config.yaml
```

Expected sections:

- `broker_connection`: Solace broker/dev-mode connection values.
- `models`: optional anchors such as `planning`, `general`, `image_gen`, `report_gen`, `multimodal`, and OAuth variants.
- `services`: shared `session_service`, `artifact_service`, `data_tools_config`, and auto-summarization.

### Model provider behavior

- The UI path can collect an LLM provider and associated model values.
- If no provider is selected, current templates strip the model anchors from `shared_config.yaml` and strip `model: *planning_model` / `model: *general_model` lines from generated orchestrator/Web UI configs while keeping `model_provider` metadata.
- CLI examples in documentation use provider/model names such as `openai/gpt-4o`, `anthropic/...`, or OpenAI-compatible custom model identifiers. The exact values must match the target LiteLLM/ADK provider.
- If a generated component references `*planning_model`, `*general_model`, or another model alias, verify `shared_config.yaml` defines the matching anchor.
- It is acceptable to skip model configuration during initialization and configure models later through the Web UI, but that requires a live run and is outside this dry bootstrap sub-skill.

## Services, persistence, and project features

### Session service

- The shared service template may default to `memory` unless customized.
- Generated orchestrator and Web UI gateway configs set SQL session services with SQLite fallbacks:
  - `ORCHESTRATOR_DATABASE_URL` fallback: `sqlite:///orchestrator.db`
  - `WEB_UI_GATEWAY_DATABASE_URL` fallback: `sqlite:///webui_gateway.db`
- Project/session UI features require SQL persistence. If `session_service.type` is `memory`, project management endpoints are disabled even if frontend flags request projects.
- PostgreSQL URLs use `postgresql://user:pass@host:port/dbname` and require PostgreSQL driver support in the runtime environment.

### Artifact service

| Type | Where used | Required values | Notes |
| --- | --- | --- | --- |
| `memory` | Fast local experimentation | none | Artifacts disappear when the process exits. |
| `filesystem` | Default durable local storage | `base_path`, `artifact_scope` | Orchestrator defaults to a filesystem base path and `namespace` scope. Ensure the runtime user can create/write the directory. |
| `gcs` | Google Cloud Storage | bucket/credential configuration supplied by environment/runtime | Supported by docs and GUI artifact choices. |
| `s3` | S3 or S3-compatible storage | `S3_BUCKET_NAME`, optional endpoint, region | Supported by CLI paths for orchestrator/agent artifact config. |

`artifact_scope` can be `namespace`, `app`, or `custom`. Use one consistent scope in a single process unless intentionally isolating artifacts.

### Data tools and summarization

Generated shared config includes data tool limits:

- SQLite memory threshold, commonly `100` MB.
- Result preview row/byte limits.
- Auto-summarization compaction percentage for long conversations.

### Logging

`configs/logging_config.yaml` configures stream and rotating-file handlers. Generated app YAML files also set per-app log file names. `.env` includes `LOGGING_CONFIG_PATH`, defaulting to `configs/logging_config.yaml`.

## Web UI gateway and platform service

When Web UI is enabled, `sam init` creates:

- `configs/gateways/webui.yaml` using `app_module: solace_agent_mesh.gateway.http_sse.app`.
- `configs/services/platform.yaml` using `app_module: solace_agent_mesh.services.platform.app`.
- `.env` values for Web UI session secret, FastAPI host/ports, SSL files, frontend flags, platform host/port, and `PLATFORM_SERVICE_URL`.

Default ports:

| Service | Default host | Default port | Config keys |
| --- | --- | --- | --- |
| Init/add configuration portal | `127.0.0.1` | `5002` | local portal only |
| Web UI FastAPI/SSE gateway | `127.0.0.1` | `8000` | `FASTAPI_HOST`, `FASTAPI_PORT` |
| Web UI HTTPS | `127.0.0.1` | `8443` | `FASTAPI_HTTPS_PORT`, SSL env vars |
| Platform API service | `127.0.0.1` | `8001` | `PLATFORM_API_HOST`, `PLATFORM_API_PORT`, `PLATFORM_SERVICE_URL` |

For containerized runtime access, set `FASTAPI_HOST="0.0.0.0"` in `.env` or system environment and map the desired host port. Do not start the runtime from this sub-skill; only plan or inspect the file values.

## Dry inspection command

From the generated skill tree, validate a candidate project without live services:

```bash
python sub-skills/project-bootstrap/scripts/inspect_project.py path/to/sam-project
```

Useful variants:

```bash
python sub-skills/project-bootstrap/scripts/inspect_project.py . --json
python sub-skills/project-bootstrap/scripts/inspect_project.py . --strict
python sub-skills/project-bootstrap/scripts/inspect_project.py --self-test
```

The helper checks directory layout, expected files, YAML parseability after safe include/alias preprocessing, unresolved template tokens, environment placeholders, service/database/artifact shapes, and Web UI/platform consistency.
