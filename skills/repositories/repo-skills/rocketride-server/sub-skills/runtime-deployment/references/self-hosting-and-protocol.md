# Self-hosting and Runtime Protocol

This reference is for operating the RocketRide engine as a local, on-prem, or
Cloud-connected runtime. It is intentionally self-contained: use it to decide how
to start the engine, what URI a client should use, how `/ping` differs from the
WebSocket task service, and how to read DAP-style runtime traffic.

## Runtime choices

| Target | Best for | Operator work | Client URI |
|---|---|---|---|
| RocketRide Cloud | Managed execution, no infrastructure | Token only | `https://api.rocketride.ai` |
| Release archive | Local/on-prem runtime without compiling | Download, extract, install OS runtime libs | `ws://<host>:5565` |
| Source build | Contributor or custom runtime build | Workspace install, build/fetch engine, sync runtime modules | `ws://<host>:5565` |
| Docker Compose | Local full stack with engine plus data stores | Docker/Compose, passwords, volumes | `ws://localhost:5565` from host |
| Helm/Kubernetes | Cluster deployment | Chart values, external services, secrets, ingress/TLS | service, ingress, or port-forward URI |

Cloud and self-hosted engines run the same pipeline JSON. Changing the target
should change endpoint/auth configuration, not the `.pipe` structure.

## URI and endpoint rules

RocketRide has two important HTTP/WebSocket surfaces on the same engine port:

- Health check: `http://<host>:5565/ping`
- Task protocol socket: `ws://<host>:5565/task/service`

Use `curl http://localhost:5565/ping` to check whether a local engine is listening.
Use the WebSocket endpoint when debugging the wire protocol directly. SDKs and
integrations may accept a base URI, but the underlying task service is always the
`/task/service` WebSocket.

Cloud uses a secure base URI:

```bash
ROCKETRIDE_URI=https://api.rocketride.ai
ROCKETRIDE_AUTH=<api-token>       # ROCKETRIDE_APIKEY is also accepted by clients
```

For Cloud, always use `https://` or `wss://`. `http://`, `ws://`, or a bare host
selects an unencrypted connection and is not appropriate for Cloud.

For a local self-hosted engine, a typical client environment is:

```bash
ROCKETRIDE_URI=ws://localhost:5565
# Local engines often allow no auth token; production/exposed engines should require one.
ROCKETRIDE_APIKEY=<local-or-production-api-key>
```

If a local development tool is already configured with `http://localhost:5565`,
remember that `/ping` is HTTP while task execution upgrades to WebSocket.
Normalize to `ws://localhost:5565/task/service` when debugging protocol frames.

## Option A: release archive

Use a release archive when you want the engine without compiling it. Choose a
server/runtime release, not a client or extension release. Asset names follow
these patterns:

| Platform | Archive pattern |
|---|---|
| Linux x64 | `rocketride-server-<version>-linux-x64.tar.gz` |
| macOS Apple Silicon | `rocketride-server-<version>-darwin-arm64.tar.gz` |
| Windows x64 | `rocketride-server-<version>-win64.zip` |

After extraction, the extracted directory is the runtime directory. It contains
an `engine` binary and an `ai/` runtime tree.

Linux needs runtime libraries before the binary starts:

```bash
# Debian / Ubuntu
sudo apt install libc++1 libc++abi1 libgomp1

# Fedora / RHEL
sudo dnf install libcxx libcxxabi libgomp

# Alpine
sudo apk add libc++ libgomp
```

Start from inside the runtime directory:

```bash
# Linux / macOS
./engine ./ai/eaas.py --host=0.0.0.0

# Windows
engine.exe ./ai/eaas.py --host=0.0.0.0
```

Use `--host=127.0.0.1` for a loopback-only local service. Use `--host=0.0.0.0`
only when you intend to expose the engine on the network and have handled TLS,
firewalling, and authentication.

Verify:

```bash
curl http://localhost:5565/ping
```

Expected signal: an HTTP success response from the engine. If the health check
works but the SDK fails, treat it as a URI/auth/WebSocket issue, not a process
startup issue.

## Option B: source build or source-managed runtime

Use a source build when contributing, customizing the runtime, building Compose
images from the assembled runtime, or packaging a release. This path is heavier
than a release archive and can download or build toolchains and dependencies.
Only run it when the user explicitly wants a build.

Common source workflow:

```bash
pnpm install
./builder build server
```

The build/fetch workflow assembles `dist/server/` as the runtime directory. From
that runtime directory, the engine command is the same shape as the release
archive:

```bash
./engine ./ai/eaas.py --host=0.0.0.0
```

The source task graph may download a prebuilt engine or compile one. It can also
configure CMake/vcpkg/compiler tools, set up Java/Tika and Python runtime files,
sync nodes/AI/Python client code into the runtime, install selected runtime/test
dependencies, and build TypeScript/shell assets. Treat failures in any of those
areas as source-build failures, not as evidence that a release archive cannot run.

Useful source task names to recognize:

| Task | What it means | Notes |
|---|---|---|
| `server:build` | Assemble the runtime directory | Heavy; may download or compile |
| `server:run` | Build/assemble then start the EaaS runtime | Starts a long-running process |
| `server:dev` | Run engine plus development shell | Starts multiple dev services |
| `server:compile` | Configure Python/runtime and compile engine | Compile-only path |
| `server:package` | Create server release archive after build | Requires successful build state |
| `server:test` | Build and run engine tests | Heavy; not a deployment smoke check |
| `server:clean` / `server:clean-all` | Remove generated server/build artifacts | Destructive to build outputs |

`server:run` starts the same EaaS entrypoint. It accepts deployment-oriented
options that are passed into the runtime entry script:

- `--trace=<types>` forwards trace selection.
- `--saas` starts with SaaS/cloud-style behavior.
- `--modelserver` starts a local model server alongside the task server.
- `--modelserver=<host:port>` points the runtime at an existing model server.

## Authentication and secrets

RocketRide separates engine auth from provider secrets:

- Cloud requires an API token. Set `ROCKETRIDE_AUTH` or `ROCKETRIDE_APIKEY`.
- A local engine commonly runs without auth for localhost-only use, but exposed
  or production deployments should require an API key and TLS.
- The first WebSocket frame is an auth request carrying the API key plus client
  name/version. After auth, task requests carry the task token/id returned by the
  open/execute step.
- Provider API keys and database credentials belong in the engine environment,
  Docker `.env`, or Kubernetes Secret. Do not put literal secrets in `.pipe`
  files; pipeline node config should reference environment variables such as
  `${ROCKETRIDE_OPENAI_KEY}` or other provider-specific names.
- Local development templates commonly use a placeholder API key such as
  `MYAPIKEY`; replace it for any shared or exposed deployment.

## DAP-style WebSocket protocol

The engine protocol is a JSON, DAP-style message exchange over
`ws://<host>:5565/task/service`.

| Frame type | Purpose | Key fields |
|---|---|---|
| `request` | Client asks the engine to do something | `seq`, `command`, `arguments`, optional `data` |
| `response` | Engine answers a request | `request_seq`, `command`, `success`, `body` or `message`/`trace` |
| `event` | Engine pushes output or status not tied to one response | `event`, `body` |

A request example:

```json
{
  "type": "request",
  "seq": 1,
  "command": "rrext_process",
  "arguments": { "subcommand": "open", "token": "$ROCKETRIDE_APIKEY" }
}
```

A failure response carries `success: false`, a `message`, and a source `trace`
object. A streaming result arrives as `event` frames rather than one large final
response.

## SDK method to runtime-command map

This map is for debugging runtime traffic. For SDK signatures, options, and code
examples, route to the SDK sub-skill instead.

| Client action | Runtime command/subcommand | Runtime effect |
|---|---|---|
| Connect/authenticate | initial auth frame | Authenticates socket using API key/client metadata |
| `use()` | `rrext_process` / `open` | Opens a task on a running pipeline and returns the task handle |
| `send()` / `pipe()` | `rrext_process` / `write` | Sends lane input; file bytes travel in the request `data` field |
| `chat()` | streaming task exchange over the same socket | Conversational input/output over event frames |
| `terminate()` | `rrext_process` / `close` | Closes the task and releases resources |
| keepalive | WebSocket ping plus `rrext_ping` | Keeps the long-lived connection healthy |
| monitor events | `rrext_monitor` | Subscribes to task/status/flow/output/SSE events |
| synchronous status | `rrext_get_task_status` | Fetches the current `TASK_STATUS` snapshot |
| resolve running task | `rrext_get_token` | Resolves a task token by project/source/team scope |
| execute pipeline | `execute` | Starts a pipeline; can set `pipelineTraceLevel` |

Default connection health behavior to know:

| Setting | Default | Meaning |
|---|---:|---|
| Ping interval | 15 s | How often a ping frame is sent |
| Ping timeout | 60 s | No pong closes the connection |
| Idle/socket timeout | 180 s | No communication is treated as stale |

## Observability model

Runtime observability is a live event stream over the same WebSocket protocol.
There is no separate Prometheus/OpenTelemetry/Sentry endpoint and no durable
history database. If history matters, connect, subscribe, and persist the events
as they arrive.

Subscribe with `rrext_monitor` after authentication:

```json
{
  "type": "request",
  "seq": 2,
  "command": "rrext_monitor",
  "token": "*",
  "arguments": {
    "types": ["TASK", "SUMMARY", "FLOW", "OUTPUT", "SSE"]
  }
}
```

Important event types:

| Type | Typical event names | Use |
|---|---|---|
| `TASK` | `apaevt_task` | Lifecycle: running/begin/end/restart |
| `SUMMARY` | `apaevt_status_update`, `apaevt_status_upload` | Full task status snapshots and upload progress |
| `FLOW` | `apaevt_flow` | Per-component flow traces; requires trace level |
| `OUTPUT` | `output` | Engine stdout/stderr-style output lines |
| `SSE` | `apaevt_sse` | Custom node-to-UI messages |
| `DASHBOARD` | `apaevt_dashboard` | Server-level connection and monitor-change events |
| `DEPLOY` | `apaevt_deploy` | Deployment-change invalidations |

Subscription scope is part of the request. `token: "*"` receives all tasks owned
by the authenticated token. A single `token` narrows to one task. A `projectId` +
`source` subscription follows your own development run; adding `teamId` addresses
a deployed team run.

`FLOW` events are silent unless the task was started with a trace level. Use
`pipelineTraceLevel: "summary"` as a practical default when you need input/output
flow without full per-call noise. Available levels are `none`, `metadata`,
`summary`, and `full`.

Operational notes:

- Subscriptions are per connection and not durable; reconnects must resubscribe.
- Turning on `TASK` or `SUMMARY` seeds the subscriber with current state.
- Status snapshots cap recent errors/warnings/notes; persist events if older
  history matters.
- Correlate events by task token/id, `project_id`, `source`, and connection-local
  `seq`; there is no global event id.
