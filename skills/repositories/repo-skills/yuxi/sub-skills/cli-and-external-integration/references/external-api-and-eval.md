# External API and eval

This reference captures the live API boundaries that `yuxi-cli` depends on.
Treat every write path as side-effectful and require an explicit user decision
before using it.

## Authentication boundary

- API keys use the `Authorization: Bearer yxkey_...` form.
- JWTs also use `Authorization: Bearer ...`, but the CLI login flow stores API
  keys locally in `~/.yuxi/config.toml`.
- Use HTTPS for any non-local remote. API keys travel in headers and must not be
  sent over plain HTTP in production.
- `agent_id` and `agent_slug` values in the public APIs are slug strings, not
  database IDs.

## CLI login and discovery flow

`yuxi login` checks discovery before storing credentials.
The expected sequence is:

1. `GET /api/system/discovery`
2. `POST /api/auth/cli/sessions`
3. `GET /auth/cli/authorize?user_code=...` in the browser
4. `POST /api/auth/cli/sessions/token`
5. `GET /api/auth/me`

The CLI refuses old servers or missing capabilities. The server must advertise
`version >= 0.7.1` and the capability bit for the requested action.

## Browser chat helper

`yuxi chat` does not expose the API key to the browser. It starts a temporary
local page on `127.0.0.1`, adds a short-lived session token, and proxies the
chat run through the CLI process.

The helper sends a channel message payload like this:

```json
{
  "channel": "cli",
  "account_id": "local",
  "chat_id": "cli",
  "agent_slug": "default-chatbot",
  "thread_id": "thread-1",
  "message_id": "request-1",
  "request_id": "request-1",
  "message": {"type": "text", "text": "你好"}
}
```

The page understands the streamed NDJSON bridge events `meta`, `delta`,
`approval_required`, `command`, `error`, and `done`.
It supports `/state` and `/approve`, but it is not the full web UI.

## SSE consumption pattern

Use the compact Agent Run event stream for CLI-style consumers:

```python
import json
import requests

headers = {"Authorization": f"Bearer {token}"}
url = f"{base_url}/api/agent/runs/{run_id}/events"

with requests.get(url, headers=headers, params={"verbose": "false"}, stream=True) as response:
    response.raise_for_status()
    event_type = None
    data_lines = []
    for line in response.iter_lines(decode_unicode=True):
        if line is None or line.startswith(":"):
            continue
        if line == "":
            if event_type and data_lines:
                payload = json.loads("\\n".join(data_lines))
                print(event_type, payload)
            event_type = None
            data_lines = []
            continue
        if line.startswith("event:"):
            event_type = line.removeprefix("event:").strip()
        elif line.startswith("data:"):
            data_lines.append(line.removeprefix("data:").strip())
```

If the consumer needs resumability, use the server-provided `id` field together
with `Last-Event-ID` or `after_seq`.

## KB external API surface

These are the read-only endpoints that back `yuxi kb list/files/query/open/find`:

- `GET /api/knowledge/databases/external`
- `GET /api/knowledge/databases/external/{kb_id}/files`
- `POST /api/knowledge/databases/external/{kb_id}/retrieve`
- `GET /api/knowledge/databases/external/{kb_id}/files/{file_id}/open`
- `POST /api/knowledge/databases/external/{kb_id}/files/{file_id}/find`

`kb upload` adds the write-side calls around the file pipeline:

- `GET /api/knowledge/databases/{kb_id}/documents/exists?filename=...`
- `POST /api/knowledge/files/upload?kb_id=...`
- `POST /api/knowledge/databases/{kb_id}/documents/add`

## External agent-call routes

These routes are for external systems that need the same agent runtime without
using the CLI wrapper:

- `POST /api/agent-invocation/agent-call/runs`
- `POST /api/agent-invocation/agent-call/runs/result`

The payloads use the same slug-based identifiers as the rest of the public API.
`messages[].content` accepts OpenAI-style `text` and `image_url` arrays.
Do not try to override runtime context through `agent_call_meta.context`; use
`model_spec` for model selection instead.

## Langfuse agent eval

`yuxi agent eval` is a dataset experiment runner, not a dataset uploader.
It needs three Langfuse environment variables in the CLI process:

- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`
- `LANGFUSE_BASE_URL`

Typical run flow:

1. Load the Langfuse dataset by name.
2. Extract a query from each item input.
3. Call `POST /api/agent-invocation/eval/runs` on the logged-in remote.
4. Write the final output back to the Langfuse experiment.

The CLI options map directly to that flow:

- `--dataset-name`
- `--agent-slug`
- `--experiment-name`
- `--max-concurrency`
- `--timeout-seconds`

A minimal shell example:

```bash
export LANGFUSE_PUBLIC_KEY=...
export LANGFUSE_SECRET_KEY=...
export LANGFUSE_BASE_URL=https://cloud.langfuse.com
yuxi login --api-key "$YUXI_API_KEY"
yuxi agent eval --dataset-name my-dataset --agent-slug default-chatbot --max-concurrency 1
```

## Side-effect gates

- `kb upload` writes remote storage and document records. Use `--yes` only when
  the user already approved the upload.
- `agent eval` writes Langfuse experiment state and remote run state. Only run
  when both the remote and the Langfuse workspace are intended targets.
- `scripts/eval/upload_langfuse_python_tasks_dataset.py` is reference-only.
  It creates or updates external Langfuse datasets and must not be bundled as a
  default runtime action.
