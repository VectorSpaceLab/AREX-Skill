# n8n and webhook integrations

RocketRide and n8n connect in both directions:

```text
n8n → RocketRide:      n8n action node or HTTP Request → RocketRide HTTP gateway /webhook
RocketRide → n8n:      RocketRide tool_n8n node → n8n Webhook trigger
Round trip:            RocketRide pipeline A → n8n workflow → RocketRide pipeline B → n8n → pipeline A
```

Use this reference for integration wiring, credentials, and network reachability.
For generic pipeline design, source/target lane repair, or SDK start commands,
route to the neighboring sub-skills.

## n8n community node package

| Item | Behavior |
| --- | --- |
| Package | `n8n-nodes-rocketride` |
| n8n compatibility | n8n 1.94.0+ |
| Runtime dependencies | none beyond n8n's own runtime |
| Action node | `RocketRide` (`n8n-nodes-rocketride.rocketRide`) |
| Trigger node | `RocketRide Trigger` (`n8n-nodes-rocketride.rocketRideInboundTrigger`) |
| AI Agent tool support | Set `N8N_COMMUNITY_PACKAGES_ALLOW_TOOL_USAGE=true` on self-hosted n8n so the action node can be used by n8n's AI Agent. |

Self-hosted n8n installs the package through **Settings → Community Nodes →
Install** with `n8n-nodes-rocketride`. On n8n Cloud, availability depends on n8n
community-node approval.

## n8n → RocketRide with the action node

The `RocketRide` action node calls a deployed/running RocketRide pipeline through
the pipeline HTTP gateway, not through the MCP WebSocket.

### Credentials

| Credential field | Typical value | Notes |
| --- | --- | --- |
| Base URL | `http://127.0.0.1:5567` | RocketRide HTTP gateway base URL. Prefer `127.0.0.1` over `localhost` on the same host because n8n's Node.js runtime may resolve `localhost` to IPv6 (`::1`). |
| API Key | `pk_…` public key shown for the running pipeline | Sent as `Authorization: Bearer <key>`. This is not the same as MCP's `ROCKETRIDE_AUTH`. |
| Ignore SSL Issues | `false` by default | Enable only for a self-signed local HTTPS gateway. |

The credential test performs `GET /version` to confirm the base URL is reachable.
It cannot fully validate a `pk_…` key because that key resolves only while the
corresponding pipeline is running.

### Operations

| Operation | Request sent to RocketRide | Common use | Important behavior |
| --- | --- | --- | --- |
| Run Pipeline | `POST {baseUrl}/webhook` | Text, JSON, RAG/document structured input | Payload mode `text` sends `text/plain`; `json` sends `application/json`; `structured` sends `{ "text": "…", "documents": [{"content", "metadata"}] }`. |
| Upload Files | `POST {baseUrl}/webhook` multipart | OCR/document/image/audio/video file uploads | One or more comma-separated binary fields; optional text part; total payload capped at 16 MB. |
| Chat | `POST {baseUrl}/webhook` with `application/rocketride-question` | Chat-enabled RocketRide pipeline | Body is a question object with `type: "question"`, `questions`, optional `role`, and `expectJson`. |

Action-node output is normalized for n8n:

- A single pipeline result is lifted to top-level JSON keys.
- RocketRide output lane names are dynamic, so never hard-code a lane name such
  as `answers`; inspect the actual output keys.
- Counts, object IDs, and result types are preserved under `_rocketride`.

### Equivalent generic HTTP Request settings

If the community action node is unavailable, n8n can call a RocketRide pipeline
with a regular HTTP Request node:

| Setting | Value |
| --- | --- |
| Method | `POST` |
| URL | The pipeline interface URL, usually `http://127.0.0.1:5567/webhook` or a public HTTPS URL. |
| Header | `Authorization: Bearer <pipeline-public-key>` or the exact authorization format shown by the running pipeline. |
| Body | JSON, text, multipart, or chat body matching the pipeline source. |

The pipeline's `response_*` node determines what n8n receives.

## n8n → RocketRide with the RocketRide Trigger node

`RocketRide Trigger` is a branded n8n webhook trigger for workflows that receive
calls from RocketRide.

| Field | Behavior |
| --- | --- |
| Path | The webhook path segment. Paste the full production/test URL into the RocketRide `tool_n8n` node or into another RocketRide HTTP-capable node. |
| Respond | `Immediately`, `When Last Node Finishes`, or `Using Respond to Webhook Node`. Use a response-producing mode when RocketRide needs data back synchronously. |
| Secret | Optional shared secret. If set, incoming calls must send it in the `Authorization` header; `Bearer ` prefix is accepted. Invalid secrets return 401. |

The trigger strips sensitive `authorization`, `cookie`, and `set-cookie` headers
from workflow data before forwarding safe header/query metadata under
`_rocketride`.

## RocketRide → n8n with `tool_n8n`

RocketRide also has an `n8n`/`tool_n8n` node. It can be a pipeline step or an
agent tool.

### Configuration fields and env placeholders

| Field | Default/placeholder | Notes |
| --- | --- | --- |
| n8n Base URL | `http://localhost:5678` or `${ROCKETRIDE_N8N_URL}` | The n8n instance URL from RocketRide's perspective. In Docker, `localhost` points at the RocketRide container, not the host. |
| API Key | `${ROCKETRIDE_N8N_KEY}` | n8n public API key (`X-N8N-API-KEY`). Required for listing workflows, inspecting executions, async polling, and activate/deactivate operations. |
| Workflow | `${ROCKETRIDE_N8N_WORKFLOW}` or explicit path | Webhook path to trigger, e.g. `rr-callback`. |
| Payload shape | `simple` | `simple` sends `{ "data": "<text>" }`; `structured` sends `{ "text": "…", "documents": [...] }`. |
| Result mode | `sync` | `sync` waits for the webhook response; `async` triggers and polls executions, requiring API key. |
| Webhook auth | `none` | Supports webhook-level auth separate from the n8n public API key. |
| Verify TLS certificate | `true` | Disable only for self-signed local HTTPS. |
| Read-only mode | `true` | Blocks activation/deactivation operations from an agent. |

Minimal reusable component config pattern:

```json
{
  "id": "tool_n8n_1",
  "provider": "tool_n8n",
  "config": {
    "profile": "default",
    "default": {
      "baseUrl": "${ROCKETRIDE_N8N_URL}",
      "apiKey": "${ROCKETRIDE_N8N_KEY}",
      "workflow": "rr-callback",
      "mode": "sync"
    },
    "parameters": {}
  },
  "input": [{ "lane": "text", "from": "chat_1" }]
}
```

Keep secrets in environment variables or credential stores; do not bake them into
`.pipe` files.

### Pipeline-step behavior

| Input lane | Sent to n8n | Output lanes to expect |
| --- | --- | --- |
| `text` | Text payload, typically `{ "data": "…" }` or structured body. | `text`, `answers`, `table` depending on response shape. |
| `questions` | Question text extracted for workflow processing. | `answers`, `text`, `table`. |
| `documents` | Preserved as documents in structured mode. | `documents`, `text`, `table`. |
| `image` / `audio` / `video` | Multipart file parts plus text fields. | Matching binary lane or text note/result. |

Sync mode needs the n8n workflow to return data through a **Respond to Webhook**
node or a Webhook trigger configured to respond when the last node finishes. If
n8n returns only `{ "message": "Workflow was started" }`, RocketRide has no
synchronous result to pass downstream.

Async mode injects a correlation id, triggers the webhook, then polls executions
through n8n's public API until the matching execution finishes. It requires
`ROCKETRIDE_N8N_KEY` or an explicit API key.

### Agent-tool behavior

When attached to an agent's tool channel, `tool_n8n` exposes functions under the
`n8n` namespace:

| Function | Requires API key? | Behavior |
| --- | --- | --- |
| `n8n.trigger_workflow` | Not for simple webhook trigger, unless webhook auth needs it | Trigger a workflow by webhook path and return the response. |
| `n8n.list_workflows` | Yes | List workflow ids, names, active state, and webhook paths. |
| `n8n.get_workflow` | Yes | Inspect one workflow by id, including webhook paths. |
| `n8n.list_executions` | Yes | List recent execution status/timestamps. |
| `n8n.get_execution` | Yes | Fetch one execution with data and a deep link. |
| `n8n.activate_workflow` | Yes and read-only off | Activate a workflow. |
| `n8n.deactivate_workflow` | Yes and read-only off | Deactivate a workflow. |

The agent does not choose the n8n host; every request targets the configured
Base URL, and workflow arguments are sanitized to plain webhook paths.

## Target workflow requirements

For RocketRide → n8n:

1. The target n8n workflow must start with a **Webhook** trigger or the
   `RocketRide Trigger` node. Manual, schedule/cron, and app-event workflows
   cannot be invoked directly over HTTP.
2. Activate/publish the workflow for the production `/webhook/...` route. While
   editing, use n8n's test webhook route only when the workflow editor is
   listening for one-shot test calls.
3. Return data if RocketRide needs data downstream: use **Respond to Webhook** or
   configure the trigger to respond when the workflow finishes.
4. For long human-in-the-loop waits, use async mode and an n8n public API key.

For non-webhook workflows, use a dispatcher:

```text
RocketRide tool_n8n → /webhook/my-dispatch
                         ↓
n8n Webhook → Execute Sub-Workflow → Respond to Webhook
                         ↓
                  target workflow result
```

## Round-trip pattern

A full round trip uses both directions:

```text
RocketRide pipeline A: chat/webhook → tool_n8n(workflow="rr-callback") → response
                                      ↓ POST /webhook/rr-callback
n8n workflow:            Webhook/RocketRide Trigger → HTTP Request to pipeline B → Respond
                                      ↓ POST http://…:5567/webhook
RocketRide pipeline B:   webhook/chat/dropper → processing → response
```

Checklist:

- Pipeline A's `tool_n8n` points at a reachable n8n Base URL and active webhook
  path.
- The n8n workflow calls pipeline B's HTTP gateway URL, not its MCP WebSocket URI.
- The n8n HTTP Request uses pipeline B's public authorization key.
- Every synchronous segment has a response-producing node.
- Avoid infinite loops: pipeline B should not call the same n8n workflow unless
  the workflow has explicit loop guards.

## Reachability matrix

| Situation | Use this address |
| --- | --- |
| n8n and RocketRide native on the same host | Prefer `http://127.0.0.1:<port>` over `localhost` for n8n → RocketRide to avoid IPv6 loopback surprises. |
| RocketRide runs in Docker, n8n on host | From RocketRide to n8n use `http://host.docker.internal:5678` on Docker Desktop; on Linux add `extra_hosts: ["host.docker.internal:host-gateway"]` or use a shared Docker network. |
| n8n runs in Docker, RocketRide on host | From n8n to RocketRide use `http://host.docker.internal:5567/webhook` or a shared Docker network, not `localhost`. |
| Both in same Docker network | Use service DNS names such as `http://n8n:5678` or the RocketRide gateway service name. |
| RocketRide Cloud needs to call n8n | Expose n8n publicly or through a tunnel; private `localhost`/LAN addresses are unreachable from Cloud. |
| n8n behind reverse proxy | Set n8n's `WEBHOOK_URL` to the externally reachable URL so it advertises usable webhook URLs. |

## Payload and size limits

- n8n's default payload cap is 16 MB. Both the n8n community node upload path and
  RocketRide `tool_n8n` binary path surface clearer errors near that limit.
- Keep large files in object storage and pass references when possible.
- For binary round trips, preserve MIME/file metadata where n8n provides it;
  RocketRide maps returned binary data back to matching lanes when possible.
