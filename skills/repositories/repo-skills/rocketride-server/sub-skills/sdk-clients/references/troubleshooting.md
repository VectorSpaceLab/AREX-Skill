# SDK and CLI Troubleshooting

Use this when Python/TypeScript SDK calls or the `rocketride` CLI fail before
or during normal client operations. Route engine startup, Docker/Helm, and deep
DAP protocol failures to the runtime/deployment sub-skill; route `.pipe` shape
and lane problems to the pipeline-authoring sub-skill.

## Safe first check: imports and signatures

Run the bundled smoke script in the environment that should run Python client
code. It imports the SDK and inspects method signatures, but does not connect:

```bash
python scripts/sdk_import_smoke.py
python scripts/sdk_import_smoke.py --json
```

Expected signal: package version is shown, required `RocketRideClient` methods
are present, and the script exits `0`.

If it fails:

- `ModuleNotFoundError: rocketride` -> install the Python SDK in this Python
  environment.
- Missing methods -> the installed SDK version differs from this skill's
  distilled 1.3.0 surface; use the installed method names or upgrade/downgrade.
- Do not fix this by starting an engine; import/signature failures are local
  packaging problems.

## URI and secure Cloud mistakes

Symptoms:

- Cloud connection fails or appears to use `ws://`.
- WebSocket upgrade/proxy errors occur immediately.
- Code works locally but not against Cloud.

Checks:

1. Print the base URI before constructing the client; do not print credentials.
2. For Cloud, use `https://...` or `wss://...`.
3. For local/self-hosted engine, use `ws://localhost:5565` or an explicit host
   and port.
4. Avoid bare Cloud hostnames. Bare hosts and `http://`/`ws://` normalize to
   plain `ws://.../task/service`.
5. Do not pass `/task/service` twice; SDK constructors accept the base URI and
   append the task service path.

Examples:

```bash
# Good local
export ROCKETRIDE_URI=ws://localhost:5565

# Good Cloud-style secure base URI
export ROCKETRIDE_URI=https://api.rocketride.ai
```

```python
client = RocketRideClient(uri="https://api.rocketride.ai", auth=api_key)
```

```typescript
const client = new RocketRideClient({ uri: 'https://api.rocketride.ai', auth: apiKey });
```

## Auth variable confusion

Symptoms:

- `AuthenticationException`, `ConnectionException`, or CLI unauthorized errors.
- MCP examples work but SDK/CLI calls report missing API key.
- `ROCKETRIDE_AUTH` is set but `ROCKETRIDE_APIKEY` is empty.

Facts:

- Python and TypeScript SDKs/CLIs use `ROCKETRIDE_APIKEY` as the primary
  credential environment variable.
- `ROCKETRIDE_AUTH` is common in MCP/Cloud docs and integrations.
- API keys and task tokens are different. `ROCKETRIDE_TOKEN` is a task token;
  it cannot authenticate the client.

Fix:

```bash
export ROCKETRIDE_APIKEY="$ROCKETRIDE_AUTH"   # if ROCKETRIDE_AUTH is the only key you have
```

or pass the credential explicitly:

```python
client = RocketRideClient(uri=uri, auth=os.environ["ROCKETRIDE_AUTH"])
```

```typescript
const client = new RocketRideClient({ uri, auth: process.env.ROCKETRIDE_AUTH });
```

Never log key values. If debugging, log only whether a variable is present.

## Python vs TypeScript environment behavior

Problem: Python code sees `.env` values but TypeScript code does not.

Cause: Python `RocketRideClient` may load `.env` from the current process
working directory when `env` is not supplied. TypeScript copies `process.env` in
Node or uses `config.env`; it does not load `.env` by itself.

Fix TypeScript:

```bash
node --env-file=.env my-script.mjs
```

or load dotenv before constructing the client, or pass:

```typescript
const client = new RocketRideClient({ env: { ROCKETRIDE_URI: uri, ROCKETRIDE_APIKEY: key } });
```

Problem: `config.env` is provided but expected `process.env` values disappear.

Cause: TypeScript `config.env` replaces the process env map for the client; it
is not merged automatically.

Fix: include every needed `ROCKETRIDE_*` value in `config.env` or merge yourself.

## Task token lifecycle errors

Symptoms:

- `send`, `send_files`/`sendFiles`, `pipe`, `chat`, `get_task_status`/
  `getTaskStatus`, or `terminate` reports wrong token, missing token, task not
  running, or pipeline terminated.

Checks:

1. Confirm the value came from `use()` / `rocketride start`, not the API key.
2. Confirm the task has not already been terminated or expired by TTL.
3. Confirm you passed the token to every data/status operation.
4. For CLI, confirm `ROCKETRIDE_TOKEN` is a task token; otherwise pass
   `--token <task-token>` explicitly.
5. For long-lived/deployed runs, try resolving a token with `get_task_token` /
   `getTaskToken` if you have `project_id` and `source` metadata.

Safe Python pattern:

```python
result = await client.use(filepath="pipeline.pipe", ttl=3600)
token = result["token"]
try:
    await client.send(token, "payload")
finally:
    await client.terminate(token)
```

## `send` / `pipe` / `send_files` failures

Common causes:

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `data must be string or bytes` / `Uint8Array` error | Wrong payload type | Encode text/JSON to `bytes` in Python pipe writes; use `Uint8Array` for TypeScript pipe writes. |
| `Pipe not opened` | `write()` before `open()` | Use `async with await client.pipe(...)` in Python or call `await pipe.open()` in TypeScript. |
| `Pipeline isn't running` | Wrong/expired token | Start/reuse a valid task token. |
| Source/lane mismatch | Pipeline source cannot receive this MIME/provider | Route to pipeline-authoring for source/lane repair; try a clear MIME such as `text/plain` only when appropriate. |
| File not found | Local path in `send_files` or CLI upload is wrong | Validate paths from the process working directory. |
| Upload progress never appears | Events not subscribed or callback not registered | Set `on_event`/`onEvent`; call `set_events`/`setEvents` for specific task/pipe events when needed. |

Python tuple forms for file upload:

```python
await client.send_files([
    "document.pdf",
    ("data.csv", {"kind": "quarterly"}),
    ("records.jsonl", {"name": "records"}, "application/jsonl"),
], token)
```

TypeScript file upload expects `File` objects:

```typescript
await client.sendFiles([{ file, objinfo: { kind: 'report' }, mimetype: 'application/pdf' }], token, 5);
```

## SSE / event callback issues

Symptoms:

- `on_sse` / `onSSE` callback is never called.
- Upload progress appears in CLI but not in SDK code.
- Events stop after reconnect.

Checks:

1. Verify the pipeline node emits SSE or the relevant event type.
2. For pipe-scoped SSE, pass `on_sse`/`onSSE` to `pipe()` or `send()`/`chat()`.
3. Ensure callbacks are async where the SDK expects async callbacks.
4. For long-lived TypeScript clients with `persist: true`, do not call
   `disconnect()` inside `onDisconnected`; it cancels reconnect.
5. Re-subscribe monitors after manual `detach()`/`attach()` flows if not using
   the SDK's built-in restoration path.

## File-store path mistakes

Symptoms:

- SDK `fs_*` method rejects a path.
- CLI store command works with `/path`, but SDK method fails.

Fix:

- CLI examples use `/` for store root.
- SDK methods require relative paths. Use `''` to list root and
  `reports/result.json` instead of `/reports/result.json`.
- `fs_open`/`fsRead` binary flows must close handles in `finally` blocks.

## CLI command mismatch

Symptoms:

- `unknown option --pipeline_path` or `unknown option --pipeline`.
- `events` or `list` command is missing.
- `--max-concurrent` is not recognized.

Cause: the `rocketride` command on `PATH` is the other implementation.

Fix:

1. Run `rocketride --help`.
2. Use the implementation-specific flags:
   - TypeScript: `rocketride start --pipeline ./x.pipe`; `rocketride upload --pipeline ./x.pipe ...`; optional `--max-concurrent`.
   - Python: `rocketride start ./x.pipe`; `rocketride upload --pipeline_path ./x.pipe ...`; Python-only `events` and `list`.
3. Use separate virtual environments or package manager scripts so the intended
   CLI wins on `PATH`.

## Validation versus execution confusion

`validate()` checks a pipeline with a live server but does not start a task.
`use()` starts a task and returns a token. If the user only needs offline `.pipe`
repair, route to pipeline-authoring. If the user needs to know why a live engine
rejects a pipeline, use `validate()` and then route details according to whether
the failure is schema/lane-related or runtime/provider-related.

## Browser versus Node TypeScript issues

- `use({ filepath })` is Node-only. In browsers, pass a pipeline object.
- `sendFiles()` expects `File` objects. In Node scripts, use a runtime with
  `File` support or construct compatible `File` objects from file contents.
- TypeScript SDK does not load `.env`; make environment variables available to
  `process.env` before construction or pass `env` explicitly.

## What not to do while troubleshooting

- Do not start Docker, Helm, or a native engine build just to debug SDK imports.
- Do not print API keys, task tokens in shared logs, or full DAP auth frames.
- Do not use an `http://`/`ws://` Cloud URI to "see if it connects".
- Do not edit `.pipe` internals here when the root cause is lane/schema design;
  route to pipeline-authoring.
