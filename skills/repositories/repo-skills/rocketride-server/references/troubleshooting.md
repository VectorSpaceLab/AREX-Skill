# Cross-cutting Troubleshooting

Use this root reference when a failure spans multiple RocketRide surfaces or when the correct sub-skill is not yet clear. For workflow-specific failures, route to the nearest sub-skill troubleshooting reference.

## Triage route

| Symptom | Likely owner | First checks |
|---|---|---|
| `.pipe` JSON does not load or wires incorrectly | `pipeline-authoring` | Unique component ids, source component, lane names, `input` vs `control`, no hardcoded secrets. |
| SDK script cannot connect or authenticate | `sdk-clients` + `runtime-deployment` | URI scheme, `/ping`, task token, auth env variable, local vs Cloud endpoint. |
| CLI command not found or wrong flags | `sdk-clients` | Which package installed the `rocketride` CLI; Python and TypeScript flag names differ. |
| Engine not listening or deployment health check fails | `runtime-deployment` | Port `5565`, `/ping`, process command, Docker/Helm service routing, TLS/auth boundary. |
| Node provider cannot be selected or docs are stale | `nodes-catalog` + `development-build-docs` | Service JSON shape, generated params block, co-located README, focused node tests/docs generation. |
| MCP assistant cannot see or call pipelines | `mcp-and-integrations` + `sdk-clients` | Running tasks, `ROCKETRIDE_URI`, `ROCKETRIDE_AUTH`/`ROCKETRIDE_APIKEY`, file path reachability. |
| n8n cannot reach RocketRide or RocketRide cannot call n8n | `mcp-and-integrations` + `runtime-deployment` | Host/container boundary, production webhook activation, public API key only for async/listing. |
| VS Code editor/app surface misbehaves | `ide-and-apps` | File association, connection mode, extension settings, app descriptor ids, shell remote entry. |
| Build/docs task fails before real tests run | `development-build-docs` | pnpm/Corepack, builder task name, generated docs rule, focused package command. |

## URI and auth pitfalls

- Local/self-hosted engine: normally use `ws://localhost:5565` or an HTTP(S) URL that the SDK normalizes to WebSocket.
- Cloud: use an encrypted `https://` or `wss://` endpoint. Do not use `http://`, `ws://`, or a bare Cloud host.
- SDK/CLI auth primarily uses `ROCKETRIDE_APIKEY` or explicit constructor/flag auth.
- MCP docs and server config also accept `ROCKETRIDE_AUTH`; when both auth names are present, know which component reads which variable.
- Never paste API keys into `.pipe` files. Use environment placeholders such as `${ROCKETRIDE_OPENAI_KEY}` or provider-specific variables expected by the node.

## Task-token failures

Most runtime data operations need a running task token. If `send`, `pipe`, `chat`, `status`, or `stop` fails:

1. Confirm a pipeline was started by SDK/CLI/IDE and the token belongs to that run.
2. Confirm the source node supports the payload type: chat/webhook/dropper-style sources are common for external input.
3. Confirm the task has not completed or been terminated.
4. Use events/status before re-running a slow or externally billed pipeline.

## Optional dependencies and external services

RocketRide has many optional node providers and integrations. A successful base SDK import does not mean every provider, vector database, OCR/model stack, Docker service, n8n instance, Slack/Guild tool, or Cloud feature is available.

When a task names an optional surface:

- Identify the exact provider or integration.
- Check required environment variables, credentials, service URLs, and network reachability.
- Check whether the node has a dedicated requirements file, optional package, or runtime service.
- Prefer static validation or safe `--help`/config checks before starting services.
- Treat provider API calls, downloads, model loads, database writes, and billed external sessions as explicit side-effecting work.

## pnpm and builder failures

The repo uses a pnpm workspace and a `./builder` wrapper. If `./builder` fails with `spawn pnpm ENOENT` or `pnpm is required`:

- Verify Node is installed and use the repo's package-manager version when possible.
- Use Corepack or a user-approved pnpm installation in a real development task.
- Do not confuse missing pnpm with a failing TypeScript test or docs contract.
- For skill verification or static analysis, use bundled static probes when a full workspace install is unnecessary.

## Generated documentation rules

Generated docs and references must be updated through their generators. Do not hand-edit generated blocks or generated reference pages.

- Node parameter blocks come from `services*.json` and the node docs generator.
- TypeScript reference docs and `.pipe` schema reference are generated from package sources.
- Public Python SDK, MCP, server protocol, VS Code, and docs landing pages each have co-located source prose.
- After changing a public contract, update the corresponding co-located prose in the same change.

## Static probe usage

Use the bundled static probe before runtime checks:

```bash
python scripts/rocketride_static_probe.py --skill-root .
python scripts/rocketride_static_probe.py --pipe ./candidate.pipe
python scripts/rocketride_static_probe.py --service-json ./candidate-service.json
```

The probe catches structural issues only. Engine-side `validate()` or a real runtime run is still required before claiming a production pipeline is correct.

## Do not over-verify by default

Avoid these unless the user explicitly asks and required dependencies/services are ready:

- full engine source builds,
- Docker Compose or Helm deployments,
- live Cloud/provider/database calls,
- VS Code extension launches,
- n8n live workflow executions,
- GPU/model downloads or long training/benchmark runs,
- release automation.

Use focused static checks, import checks, and targeted native tests first.
