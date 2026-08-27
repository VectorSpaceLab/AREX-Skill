# REST gateway, `sam-rest-cli`, and `SAMRestClient`

The REST client targets the SAM REST API Gateway plugin. This is separate from the Web UI gateway task CLI in `references/running-and-tasks.md`.

## Install surface and dependency conflict guidance

The `sam-rest-client` package is useful for external callers, CI jobs, and application code that should submit tasks through a REST gateway. Treat it as a separate install surface from the main SAM runtime when possible.

Known pin conflict:

| Package surface | Pinned dependencies relevant to conflict |
| --- | --- |
| Main `solace-agent-mesh` package | `pydantic==2.12.5`, `rich==13.9.4` |
| `sam-rest-client==0.1.0` | `pydantic==2.11.9`, `rich==14.1.0` |

Recommended patterns:

```sh
# Dedicated REST client environment for callers
python -m venv .venv-sam-rest-client
. .venv-sam-rest-client/bin/activate
python -m pip install sam-rest-client
sam-rest-cli -h
```

```sh
# Main SAM project environment, without adding conflicting client pins
python -m pip install solace-agent-mesh
# Add the REST gateway plugin to the SAM project/runtime environment when needed:
python -m pip install sam-rest-gateway
```

Do not install or upgrade the REST client in a live SAM project environment unless the user accepts the dependency pin change. If the user needs both CLI surfaces on one machine, use separate virtual environments and run each command from its own environment.

## REST gateway API contract

Modern async mode uses REST v2:

| Operation | HTTP form/API behavior |
| --- | --- |
| Create task | `POST /api/v2/tasks` with multipart/form fields `agent_name`, `prompt`, and optional repeated `files`. Expected status is 202 with `taskId`. |
| Poll task | `GET /api/v2/tasks/{taskId}`. Status 202 means still running; status 200 returns final task data; other statuses are client errors. |
| List artifacts | `GET /api/v2/artifacts/?session_id={contextId or sessionId}`. |
| Download artifact | `GET /api/v2/artifacts/{filename}?session_id={contextId or sessionId}` or versioned path through the client helper. |
| Legacy sync | `POST /api/v1/invoke` with form fields; deprecated and selected by `mode='sync'`. |

The REST gateway commonly requires a bearer token. If auth is disabled, omit the token. If auth is enabled, pass `Authorization: Bearer <token>` or the equivalent client/CLI option.

## `sam-rest-cli`

`sam-rest-cli` submits a real task. It is not a dry health check.

Key options:

| Option | Meaning |
| --- | --- |
| `--url URL` | Required base URL of the REST API Gateway, for example `http://localhost:8080`. |
| `--token TOKEN` | Bearer token. Defaults from `SAM_AUTH_TOKEN` if set. |
| `--agent NAME` | Required target agent name as known to the REST gateway. |
| `--prompt TEXT` | Required prompt to send. |
| `--file PATH` | Optional file upload; repeat for multiple files. The CLI sends basename plus open file handle. |
| `--mode async|sync` | Default `async` uses v2 submit+poll; `sync` uses deprecated v1 blocking invoke. |
| `--timeout SECONDS` | Async completion timeout. Default is 120 seconds. |
| `--log PATH` | Write raw submit/poll responses for debugging. |

Examples:

```sh
# Async v2 task through REST gateway
sam-rest-cli --url http://localhost:8080 --agent OrchestratorAgent --prompt "Give me a list of agents"

# Authenticated call with upload and raw response log
sam-rest-cli --url "$SAM_REST_URL" --token "$SAM_AUTH_TOKEN" --agent DataAgent --prompt "Summarize this CSV" --file ./sales.csv --log ./rest-debug.jsonl

# Deprecated sync mode only when integrating with legacy REST gateway behavior
sam-rest-cli --url http://localhost:8080 --agent LegacyAgent --prompt "Quick check" --mode sync
```

The CLI may prompt before downloading generated artifacts to the current directory. In automation, account for that prompt or use the Python client for explicit artifact handling.

## Python client usage

Core import surface:

```python
from sam_rest_client import (
    SAMRestClient,
    SAMClientError,
    SAMTaskFailedError,
    SAMTaskTimeoutError,
)
```

Minimal async task:

```python
import asyncio
from sam_rest_client import SAMRestClient, SAMTaskFailedError, SAMTaskTimeoutError

async def main():
    client = SAMRestClient(base_url="http://localhost:8080", auth_token=None)
    try:
        result = await client.invoke(
            agent_name="OrchestratorAgent",
            prompt="Summarize the attached sales data.",
            timeout_seconds=120,
            polling_interval_seconds=2,
        )
        print(result.get_text())
    except SAMTaskTimeoutError as exc:
        print(f"Timed out: {exc}")
    except SAMTaskFailedError as exc:
        print(f"Agent failed: {exc.error_details}")
    finally:
        await client.close()

asyncio.run(main())
```

With file uploads and artifacts:

```python
import asyncio
from pathlib import Path
from sam_rest_client import SAMRestClient

async def main():
    client = SAMRestClient(base_url="http://localhost:8080", auth_token="token-if-required")
    file_handle = open("sales.csv", "rb")
    try:
        result = await client.invoke(
            agent_name="DataAgent",
            prompt="Analyze this file and create a report artifact.",
            files=[("sales.csv", file_handle)],
            mode="async",
            timeout_seconds=300,
        )
        print(result.get_text())
        for artifact in result.get_artifacts():
            await artifact.save_to_disk(".")
    finally:
        file_handle.close()
        await client.close()

asyncio.run(main())
```

Client behavior to remember:

- `SAMRestClient(base_url, auth_token=None, log_file_handle=None)` strips a trailing slash and uses an `httpx.AsyncClient` with a 30 second per-request timeout.
- `invoke(..., mode='async')` submits to `/api/v2/tasks`, requires 202 on submission, then polls `/api/v2/tasks/{taskId}` until 200 or timeout.
- `invoke(..., mode='sync')` posts to `/api/v1/invoke`; this is the deprecated legacy path.
- `SAMResult.get_text()` joins final text parts where part `type` is `text`.
- `SAMResult.get_artifacts()` returns helpers only when a session ID is present.
- `SAMArtifact.get_content(version=None)` downloads latest content; pass a version number for a specific version.
- `SAMArtifact.save_to_disk(path='.')` writes the artifact by its server-provided name.

## REST troubleshooting quick map

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `Failed to submit task. Status: 404` | Wrong base URL or using Web UI gateway without REST plugin route. | Probe the URL with `scripts/check_gateway.py`; confirm REST gateway port/config. |
| Submit returns 401/403 | Missing/expired bearer token or gateway auth policy. | Pass `--token` or `SAM_AUTH_TOKEN`; refresh token using the gateway's auth flow if applicable. |
| Polling stays 202 until timeout | Agent is slow, task is stuck, target agent cannot complete, or timeout too low. | Increase `--timeout`/`timeout_seconds`; inspect server logs and task history. |
| `SAMTaskFailedError` | Gateway returned a final task object with an error. | Inspect `error_details`, raw log, and agent/service logs. |
| No artifacts download | No `sessionId` in result, artifact list empty, wrong session ID, or artifact storage failure. | Use raw result to verify `sessionId`; query artifact list with that value. |
| Dependency resolver wants to change SAM pins | `sam-rest-client` conflicts with main package pins. | Use a separate client environment. |
