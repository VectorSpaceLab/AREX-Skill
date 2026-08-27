# Component scaffolding

Use this reference after a SAM project already exists and the task is to add or inspect project-local agents, gateways, or A2A proxies. It covers scaffold behavior only; live activation belongs to runtime operations.

## Command map

```bash
sam add agent [OPTIONS] [NAME]
sam add gateway [OPTIONS] [NAME]
sam add proxy [OPTIONS] NAME
```

The `sam` executable and `solace-agent-mesh` executable both route to the same CLI.

## Name normalization

The CLI normalizes component names by splitting spaces, hyphens, underscores, and camel-case boundaries:

| User input | Snake file stem | Pascal app/name stem | Kebab id stem |
| --- | --- | --- | --- |
| `my-agent` | `my_agent` | `MyAgent` | `my-agent` |
| `MyHTTPAgent` | `my_http_agent` | `MyHttpAgent` | `my-http-agent` |
| `data proxy` | `data_proxy` | `DataProxy` | `data-proxy` |

The orchestrator agent created by `sam init` is stricter: only letters, numbers, and underscores are valid. Other component add commands normalize a wider range of human-friendly names.

## Add an agent

### Output

`sam add agent weather --skip` writes:

```text
configs/agents/weather_agent.yaml
```

The generated YAML uses:

- `!include ../shared_config.yaml`
- `app_module: solace_agent_mesh.agent.sac.app`
- `app_config.agent_name` as the PascalCase agent name.
- `model_provider` and `model` alias, usually `general` / `*general_model`.
- `tools`, `session_service`, `artifact_service`, artifact handling, data tools, auto-summarization, agent card, discovery, and inter-agent communication.

### Common flags

| Concern | Flags | Notes |
| --- | --- | --- |
| GUI setup | `--gui` | Starts the local add-agent portal on port `5002` with `?config_mode=addAgent`. The CLI writes the file only if the portal returns `success_from_gui_save`. |
| Automation | `--skip` | Uses defaults for unprovided values. |
| Identity | `NAME`, `--namespace`, `--supports-streaming` | `NAME` is required unless using `--gui`. |
| Model alias | `--model-provider` | Alias must exist in `shared_config.yaml` if the generated YAML references `*<alias>_model`. |
| Instruction | `--instruction` | Written as the agent system instruction; `__AGENT_NAME__` in defaults is replaced. |
| Session | `--session-service-type`, `--session-service-behavior`, `--database-url` | The current CLI collection path normalizes new agents to SQL session service; GUI/direct config can provide other session choices. If a custom database URL is provided, it is appended to `.env` as `<AGENT>_DATABASE_URL`. |
| Artifact | `--artifact-service-type`, `--artifact-service-base-path`, `--artifact-service-bucket-name`, `--artifact-service-endpoint-url`, `--artifact-service-region`, `--artifact-service-scope` | Agent CLI supports `memory`, `filesystem`, `gcs`, and `s3`; GUI schema exposes memory/filesystem/gcs plus shared defaults. |
| Artifact behavior | `--artifact-handling-mode`, `--enable-embed-resolution`, `--enable-artifact-content-instruction` | Controls whether artifacts are ignored, embedded, or referenced and whether embed resolution/instructions are enabled. |
| Agent card | `--agent-card-description`, `--agent-card-default-input-modes-str`, `--agent-card-default-output-modes-str`, `--agent-card-publishing-interval`, `--agent-discovery-enabled` | Agent card describes discoverable capabilities. |
| Peer delegation | `--inter-agent-communication-allow-list-str`, `--inter-agent-communication-deny-list-str`, `--inter-agent-communication-timeout` | Comma-separated allow/deny lists; default timeout is long enough for multi-agent tasks. |
| Tools/skills JSON | advanced config data | GUI/API paths can pass tools and agent-card skills. MCP tool entries without a timeout receive a default timeout. |

### Agent session and database details

Generated SQL session service blocks usually look like:

```yaml
session_service:
  type: "sql"
  default_behavior: "PERSISTENT"
  database_url: "${WEATHER_DATABASE_URL, sqlite:///weather.db}"
```

If a custom `--database-url` is accepted, the YAML references `${WEATHER_DATABASE_URL}` and `.env` receives that value. SQLite URLs should use `sqlite:///relative-or-absolute-file.db`; PostgreSQL URLs should use `postgresql://...` and require PostgreSQL driver support in the runtime environment.

### Agent artifact service choices

| Choice | YAML pattern | Good for | Watch for |
| --- | --- | --- | --- |
| Default shared | `artifact_service: *default_artifact_service` | Consistent project-wide artifacts. | Requires `configs/shared_config.yaml` to define the anchor. |
| Memory | `type: "memory"` | Temporary experiments. | Files are not durable. |
| Filesystem | `type: "filesystem"` plus `base_path` | Local durable artifacts. | Base path must be writable by the runtime. |
| GCS | `type: "gcs"` | Google Cloud Storage. | Requires runtime credentials and bucket configuration. |
| S3 | `type: "s3"` plus bucket/endpoint/region values | AWS S3 or S3-compatible stores. | Endpoint is optional for AWS S3; region defaults to `us-east-1` where not supplied. |

## Add a gateway

### Output

`sam add gateway inbox --skip` writes:

```text
configs/gateways/inbox_config.yaml
src/inbox/__init__.py
src/inbox/app.py
src/inbox/component.py
```

The generated config uses:

- `!include ../shared_config.yaml`
- `app_module: src.inbox.app`
- `gateway_id`, defaulting to `<kebab-name>-gw-01`.
- A gateway-local or shared artifact service.
- `system_purpose` and `response_format` blocks.
- Source stubs for schema and component logic.

### Common flags

| Concern | Flags | Notes |
| --- | --- | --- |
| GUI setup | `--gui` | Starts local add-gateway portal on port `5002` with `?config_mode=addGateway`. |
| Automation | `--skip` | Uses defaults and overwrites any existing gateway scaffold without prompting. |
| Identity | `NAME`, `--namespace`, `--gateway-id` | `NAME` is required unless using `--gui`; default gateway id is `<kebab-name>-gw-01`. |
| Artifact service | `--artifact-service-type`, `--artifact-service-base-path`, `--artifact-service-scope` | Choices are shared default, `memory`, `filesystem`, and `gcs`; S3 is not exposed by the gateway add command. |
| Gateway prompt context | `--system-purpose`, `--response-format` | In interactive mode, missing multiline values may open an editor. In skip mode, defaults are used. |

### Gateway artifact path wrapping

For gateway filesystem artifact services, a plain base path can be wrapped in an `${ARTIFACT_BASE_PATH, ...}` expression. If the value already contains an environment expression, it is preserved.

## Add an A2A proxy

### Output

`sam add proxy external-search --skip` writes:

```text
configs/agents/external_search_proxy.yaml
```

The proxy config uses:

- `!include ../shared_config.yaml`
- `app_module: solace_agent_mesh.agent.proxies.a2a.app`
- A filesystem artifact service for artifacts received from downstream HTTP agents.
- `artifact_handling_mode: "reference"`.
- `discovery_interval_seconds`.
- Built-in artifact management tools.
- A `proxied_agents` list to edit with downstream agent names, URLs, authentication, timeouts, and agent-card URL behavior.

`NAME` is required. `--skip` is accepted but proxy creation is non-interactive either way.

## GUI add flow behavior

Both add-agent and add-gateway GUI flows:

1. Start the local configuration portal on `127.0.0.1:5002`.
2. Open a browser URL with `config_mode=addAgent` or `config_mode=addGateway`.
3. Wait for the portal process to exit.
4. Read a shared status payload.
5. Write project files only when status is `success_from_gui_save` and required name/config data are present.

Failure modes:

- Browser does not open: the CLI prints the URL; the user can open it manually.
- Portal returns incomplete data: no component is created.
- Portal is closed or aborted: no component is created.
- Port `5002` is busy: the portal cannot start; resolve the port conflict and retry.

## Overwrite and idempotence behavior

| Command | Existing file behavior | Safer operating pattern |
| --- | --- | --- |
| `sam add agent` | Writes the target YAML path; existing content can be replaced. | Inspect or back up `configs/agents/<name>_agent.yaml` first. |
| `sam add gateway` | Interactive mode prompts before overwriting conflicting gateway files; `--skip` overwrites without prompting. | Avoid `--skip` when modifying a hand-edited gateway unless the overwrite is intentional. |
| `sam add proxy` | Writes the target YAML path; existing content can be replaced. | Back up `configs/agents/<name>_proxy.yaml` first. |

## Dry inspect after component changes

After adding a component, run:

```bash
python sub-skills/project-bootstrap/scripts/inspect_project.py path/to/sam-project
```

The inspector checks that new YAML parses, include targets exist, app modules are declared, unresolved template placeholders are absent, and storage/session/database shapes are plausible. It does not import custom gateway source or start the project.
