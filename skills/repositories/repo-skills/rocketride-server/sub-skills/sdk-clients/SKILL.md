---
name: sdk-clients
description: "Use RocketRide Python and TypeScript/Node SDKs and CLI safely for
  auth, task tokens, data transfer, events, file store, and API
  troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# SDK Clients

Use this sub-skill when a task is about calling RocketRide from Python,
TypeScript/Node, or the `rocketride` CLI: connecting, authenticating, starting a
pipeline, using the returned task token, sending data/files, streaming through a
pipe, subscribing to events, reading status, using the account file store, or
checking that the SDK imports cleanly.

## Use this for

- Python `RocketRideClient` scripts and async usage
- TypeScript/Node `RocketRideClient` scripts, browser/client usage, and `DataPipe`
- CLI command selection and Python-vs-TypeScript CLI flag differences
- URI/auth environment handling, especially `ROCKETRIDE_URI`, `ROCKETRIDE_APIKEY`,
  `ROCKETRIDE_AUTH`, `ROCKETRIDE_PIPELINE`, and `ROCKETRIDE_TOKEN`
- Task token lifecycle: `use()`/`start` -> data operations/status -> `terminate()`/`stop`
- Upload progress and server event callbacks
- Account file-store methods (`fs_*` / `fs*`) and direct URLs
- Safe import/signature smoke checks without starting services or connecting

## Do not use this for

- Designing `.pipe` JSON shape, lanes, sources, and recipes -> `../pipeline-authoring/`
- Starting engines, Docker, Helm, Cloud/self-hosting operations, or DAP protocol depth -> `../runtime-deployment/`
- Node provider/service schemas and generated node documentation -> `../nodes-catalog/`
- MCP server or n8n integration workflows -> `../mcp-and-integrations/`
- IDE/VS Code extension behavior -> `../ide-and-apps/`

## First decisions

1. Identify the client surface: Python SDK, TypeScript/Node SDK, browser SDK,
   or CLI. The method names and file-upload shapes differ.
2. Identify endpoint class: local/self-hosted (`ws://...` or `http://...`) versus
   Cloud (`https://...` or `wss://...`). For any Cloud host, never use `http://`,
   `ws://`, or a bare hostname because normalization can produce an unencrypted
   `ws://` connection.
3. Identify authentication source. Python/TypeScript SDKs and CLIs read
   `ROCKETRIDE_APIKEY`; MCP and some Cloud docs also use `ROCKETRIDE_AUTH`.
   For SDK/CLI tasks, set or pass `ROCKETRIDE_APIKEY` unless the code explicitly
   copies `ROCKETRIDE_AUTH` into the client auth value.
4. Identify whether a task token already exists. If not, start with `use()` or
   `rocketride start` and capture the returned token before `send`, `pipe`,
   `chat`, `status`, `stop`, or file-store task-scoped operations.

## Reference map

- [Python SDK API](references/python-sdk-api.md) — inspected Python signatures,
  async usage, token lifecycle, file store, events, and common pitfalls.
- [TypeScript SDK API](references/typescript-sdk-api.md) — `RocketRideClient`,
  `DataPipe`, browser/Node differences, env handling, namespaces, and examples.
- [CLI reference](references/cli-reference.md) — command matrix, Python vs
  TypeScript CLI flags, environment variables, and token use.
- [Troubleshooting](references/troubleshooting.md) — auth/URI mistakes, token
  errors, upload/SSE issues, CLI path conflicts, file-store path rules, and safe
  import checks.

## Safe smoke check

After installing the Python SDK in the environment that will run client code,
run the bundled import/signature check. It performs no network connection:

```bash
python scripts/sdk_import_smoke.py
```

Use `--json` when another tool needs structured output.

## Good output for SDK/CLI tasks

- Names the SDK/CLI surface and uses its exact method/flag names
- Uses secure Cloud URI schemes and avoids logging API keys
- Starts or reuses a task token before data operations
- Chooses `send` for one-shot payloads, `send_files`/`sendFiles` for files, and
  `pipe`/`DataPipe` for chunked or SSE-scoped streaming
- Terminates tasks when done unless the workflow is intentionally long-lived
- Keeps `.pipe` schema design and engine deployment details routed to the sibling
  sub-skills instead of expanding them here
