# Running SAM projects and task operations

This reference covers existing SAM project operation. It intentionally does not teach project creation or workflow YAML authoring; route those cases to the sibling sub-skills named in `../SKILL.md`.

## Dry versus live actions

| Action | Safe without services? | Notes |
| --- | --- | --- |
| `sam run --help`, `sam task --help`, `sam task send --help`, `sam task run --help` | yes | CLI parser/help only. |
| Inspect YAML files, `.env` names, or command lines | yes | Do not require broker/model/gateway. |
| `python scripts/check_gateway.py --url ...` | mostly | Performs GET probes only; it may read agent cards/version/task history if flags ask for it. |
| `sam run ...` | no | Starts configured apps and may contact a broker, models, databases, auth services, plugins, and gateways. |
| `sam task send ...` | no | Sends a real task to an already-running Web UI gateway. |
| `sam task run ...` | no | Starts SAM, sends a real task, streams the answer, then stops SAM. |

If the user asks only to validate a command, prefer help/config inspection and the gateway checker. If the user asks to run or submit, continue with the live workflow and make external-service prerequisites explicit.

## Runtime mental model

A SAM runtime is a set of YAML app configs loaded into Solace AI Connector. Agents, gateways, proxies, platform service, session/artifact services, logging, model providers, and plugins are app entries in those configs. The `sam` console script and `solace-agent-mesh` console script both route to the same CLI.

Common runtime prerequisites:

- Installed `solace-agent-mesh` package with working console scripts.
- A project directory containing a `configs/` tree, unless explicit YAML files/directories are supplied.
- Required environment variables for broker, model provider, auth, database, artifact storage, and plugin settings.
- A Web UI gateway config if using browser or `sam task` commands. The common local URL is `http://localhost:8000`.
- A REST gateway plugin/config if using `sam-rest-client`, `sam-rest-cli`, or `/api/v2/tasks`; the Web UI task CLI is a different API surface.

## Run an existing SAM project

`sam run [OPTIONS] [FILES]...` starts the selected YAML configuration set.

### Configuration discovery

- With no file arguments, `sam run` searches `configs/` under the current working directory.
- Directory arguments are searched recursively for `.yaml` and `.yml` files.
- File arguments are accepted only when they end in `.yaml` or `.yml`.
- Files whose basename starts with `_` are skipped.
- Files whose basename starts with `shared_config` are skipped by discovery.
- `-s NAME` or `--skip NAME` excludes matching basenames after discovery.
- If no `configs/` directory exists and no explicit config path is supplied, the command errors and tells the user to run project initialization or provide config files.
- If filtering leaves no YAML files, the command logs a warning and exits without starting apps.

### Environment loading

- By default, `sam run` uses dotenv discovery from the current directory upward and loads the first `.env` found, overriding process values.
- `-u` or `--system-env` skips `.env` discovery/loading and uses only the existing process environment.
- When `LOGGING_CONFIG_PATH` comes from `.env` and is relative, `sam run` resolves it to an absolute path before logging is configured.
- If no `.env` is found, the command warns but proceeds; missing provider/broker/database credentials may still fail later during app startup.

### Examples

```sh
# Run all discovered project configs
sam run

# Run selected app configs
sam run configs/agents/orchestrator.yaml configs/gateways/webui.yaml

# Run a directory but skip a disabled or experimental app
sam run configs/ -s experimental_agent.yaml

# Use only already-exported shell environment variables
sam run configs/ --system-env
```

### Docker notes

For containerized local execution, expose the gateway port and set the FastAPI host inside config or environment to `0.0.0.0` when the host machine must reach the Web UI gateway. If the project depends on extra Python packages or plugins, build a custom image that installs them before running `solace-agent-mesh run`.

## Web UI gateway task semantics

The `sam task` family speaks to the Web UI HTTP SSE gateway, not the REST gateway plugin. It uses these gateway paths internally:

- `GET /api/v1/agentCards` for agent discovery and authorization-filtered tool visibility.
- `POST /api/v1/message:stream` to submit a JSON-RPC streaming message.
- `GET /api/v1/sse/subscribe/{task_id}` to stream status updates, artifact updates, and final task response.
- `GET /api/v1/tasks/{task_id}` to download a `.stim` task invocation log unless disabled.
- `GET /api/v1/artifacts/{session_id}` and per-artifact download paths to collect generated artifacts into the output directory.

The submitted JSON-RPC message contains a text part plus optional file parts. File attachments are read from local paths, MIME-guessed, base64 encoded, and embedded as A2A file parts with `kind: file`, `file.bytes`, `file.name`, and `file.mimeType`. Large files therefore increase request size in memory and on the wire.

Agent matching for `sam task send` and `sam task run` is exact first, then case-insensitive, then partial. If no match is found after agent discovery succeeds, the command reports available names and exits.

## Send a task to an already-running Web UI gateway

Use `sam task send [OPTIONS] MESSAGE` when SAM is already running.

Key options:

| Option | Meaning |
| --- | --- |
| `-u, --url URL` | Base URL of the Web UI gateway. Defaults to `http://localhost:8000`; can also come from `SAM_WEBUI_URL`. |
| `-a, --agent NAME` | Target agent. Defaults to `orchestrator`; can also come from `SAM_AGENT`. |
| `-s, --session-id ID` | Preserve conversation context. If omitted, a UUID is generated. |
| `-t, --token TOKEN` | Bearer token; can also come from `SAM_AUTH_TOKEN`. |
| `-f, --file PATH` | Attach one local file; repeat for multiple files. |
| `--timeout SECONDS` | Overall SSE stream timeout. Default is 120 seconds. |
| `-o, --output-dir DIR` | Output directory. Default is `/tmp/sam-task-{taskId}`. |
| `-q, --quiet` | Suppress live streamed text and show final summary only. |
| `--no-stim` | Skip `.stim` download. |
| `--debug` | Print gateway URL, agent discovery, POST, and SSE debug details. |

Examples:

```sh
# Simple live task to the default gateway and agent
sam task send "What agents are available?"

# Continue an existing session
sam task send "What did we discuss?" --session-id abc-123

# Target a named agent and attach files
sam task send "Compare these files" --agent data_analyst --file ./a.csv --file ./b.csv

# Authenticated remote gateway with longer streaming timeout
sam task send "Summarize the uploaded report" --url https://gateway.example.invalid --token "$SAM_AUTH_TOKEN" --timeout 300 --file ./report.pdf
```

Output directory contents normally include:

```text
sse_events.yaml   # every SSE event recorded for debugging
response.txt      # text streamed to the terminal
{taskId}.stim     # task invocation log unless --no-stim is set
artifacts/        # downloaded artifacts created during the session
```

## Start SAM, send one task, and stop

Use `sam task run [OPTIONS] MESSAGE` for one-shot testing or automation. It discovers config files, starts SAM in-process, waits for the target agent to be advertised by the Web UI gateway, submits the task, streams the answer, and then stops SAM in a `finally` cleanup block.

Additional `task run` options:

| Option | Meaning |
| --- | --- |
| `-c, --config PATH` | Config file or directory; repeat as needed. Default discovery is `configs/`. |
| `-s, --skip NAME` | Exclude matching config basenames. |
| `--startup-timeout SECONDS` | Wait for agent discovery before submitting. Default is 60 seconds. |
| `--timeout SECONDS` | Wait for task completion after submission. Default is 300 seconds. |
| `--system-env` | Do not load `.env` before starting SAM. |
| `-o, --output-dir DIR` | Output directory. Default is `/tmp/sam-task-run-{uuid}` and includes `sam.log`. |

Examples:

```sh
# One-shot using default configs/
sam task run "What agents are available?"

# One-shot with selected configs and debug logs
sam task run "Hello" -c configs/agents/orchestrator.yaml -c configs/gateways/webui.yaml --debug

# One-shot with file input and explicit output directory
sam task run "Summarize this document" -c configs/ --file ./document.pdf --output-dir ./task-output
```

When diagnosing failures, separate these phases:

1. Config discovery and `.env` loading.
2. SAM startup and logs in `sam.log`.
3. Agent discovery at `/api/v1/agentCards` within `--startup-timeout`.
4. Task submission at `/api/v1/message:stream`.
5. SSE streaming and artifact/STIM downloads within `--timeout`.

## Gateway preflight without task submission

The bundled checker performs only GET requests:

```sh
python scripts/check_gateway.py --url http://localhost:8000 --expect-agent orchestrator
python scripts/check_gateway.py --url https://gateway.example.invalid --token "$SAM_AUTH_TOKEN" --json
```

Use it to tell apart a dead URL, auth failure, wrong gateway type, absent version endpoint, and missing agent card. Do not treat it as proof that a real LLM task will succeed; it does not submit a prompt or contact an agent through the message route.
