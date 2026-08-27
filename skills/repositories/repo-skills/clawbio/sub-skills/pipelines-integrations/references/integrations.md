# Integration reference

## MCP stdio server

The optional MCP layer is a thin stdio binding around three SDK-independent
operations:

- `list_skills(query="")` returns compact catalog entries and marks whether an
  entry is actually runnable.
- `describe_skill(name)` returns catalog metadata and the skill's `SKILL.md`.
- `run_skill(...)` dispatches through the same ClawBio CLI runner and truncates
  stdout/stderr to 20,000 characters while keeping full files in the output
  directory.

The command is:

```bash
clawbio mcp
```

A client configuration can use the published package without a checkout:

```json
{
  "mcpServers": {
    "clawbio": {
      "command": "uvx",
      "args": ["--from", "clawbio[mcp]", "clawbio", "mcp"]
    }
  }
}
```

The optional dependency is `mcp>=1.9,<2`. The server imports no MCP SDK until
`serve()` binds the transport. The current binding requires
`mcp.server.fastmcp`; MCP 2.x removed that import path, so a package import can
succeed while service startup still fails with an actionable version message.
Use `clawbio mcp --help` only as an argument-parser check; a real MCP readiness
check needs a client handshake and is outside a no-service diagnostic.

### Safe default and local files

`run_skill` permits demo mode without an environment opt-in. Supplying
`input_path` or `output_dir` is rejected unless the MCP process was deliberately
started with:

```bash
CLAWBIO_MCP_ALLOW_LOCAL_FILES=1 clawbio mcp
```

This is a local data access boundary, not a credential. Do not set it merely to
make a client connect. Spec-only catalog entries are readable through
`describe_skill` but are refused by `run_skill`; do not guess a CLI alias.
MCP is local over stdio, but the skills it invokes may have their own optional
network lookups. Demo inputs are not patient data; preserve each skill's
network and medical safety contract.

## RoboTerri adapters

The maintained adapters are separate, checkout/deployment-only processes
installed through the optional bot dependency group. They are intentionally not
bundled as runtime helpers here because they require platform credentials,
webhooks, and external services. In a deliberate checkout, follow its package
manager and deployment instructions; do not start an adapter during a
no-service diagnostic. The adapters use an OpenAI-compatible tool-calling layer
to plan local `clawbio run ...` commands, then render reports and media. They support structured intent
metadata (`INTENTS.json`) and action/result fields, but the core runner still
owns skill registration and extra-flag allowlists.

### Secrets and providers

Keep `.env` out of source control. The adapter credentials are process
configuration, not input files:

| Adapter/provider | Required or relevant settings | Boundary |
|---|---|---|
| Telegram | `TELEGRAM_BOT_TOKEN`; optional `TELEGRAM_CHAT_ID`/`AUTHORISED_CHAT_ID` for admin identity | Telegram Bot API network; received documents are downloaded locally by the bot |
| Discord | `DISCORD_BOT_TOKEN`; channel allowlist in `bot/.channels.json` or `DISCORD_CHANNEL_ID`; optional `DISCORD_ADMIN_USER_ID` | Discord Gateway/API network; enable Message Content Intent |
| WhatsApp | `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_APP_SECRET`; optional `WHATSAPP_ADMIN_PHONE`, `WHATSAPP_ALLOWED_NUMBERS`; `WHATSAPP_PUBLIC=1` is explicit public opt-in | Meta Graph API and webhook network; signature verification is fail-closed |
| LLM tool loop | `LLM_API_KEY`; optional `LLM_BASE_URL`; `CLAWBIO_MODEL` | Natural-language/tool prompts go to the configured provider unless it is a local endpoint; vision/TTS may require provider support |
| FLock routing bridge | `openai` package and `FLOCK_API_KEY`; optional model/base URL in `FlockRouter` | Sends routing query to `https://api.flock.io/v1`; `route_query_safe` returns a null skill on failure |

The adapters install logger filters for configured platform/provider tokens in
their integration loggers. Coverage is adapter/logger-specific, so do not rely
on redaction as a storage policy: never print environment values, include them
in prompts, or put them in result bundles.
The FLock bridge is a remote LLM router, not a local privacy-preserving
fallback: require the operator's consent and avoid sending patient/genetic
content through it. If the provider is unavailable, use deterministic local
routing or return an explicit unresolved route; do not fabricate a skill.

### Identity and received files

Every adapter stores received files and pending actions under the authenticated
chat/channel/phone key. `scoped_get` must return only that exact identity; an
empty or missing identity never falls back to the first stored file. WhatsApp
additionally checks `X-Hub-Signature-256` with HMAC-SHA256 and rejects missing,
malformed, or mismatched signatures. Its sender policy denies by default and
allows only the configured number/admin, unless public access is explicitly
enabled.

File handling is bounded and local before a skill run:

- Telegram upload limit is 20 MiB; Discord and WhatsApp use 50 MiB documents
  and 20 MiB photos.
- Accepted genetic/media extensions include text/CSV/VCF/FASTQ (including
  selected `.gz` compounds), `.h5ad`, microscopy/photo formats, and TSV;
  active-content formats such as HTML/Markdown/PDF are not accepted as uploads
  by RoboTerri's guarded paths.
- Names are reduced to a basename, control/path traversal characters are
  removed, and writes are confined under ClawBio's data root. Protected names
  include `.env`, agent instructions, bot scripts, `clawbio.py`, and
  `requirements.txt`.
- A bot may save only the most recently received file for that same identity.
  Temporary files can expire. Do not promise durable retention; use a deliberate
  local destination and check whether it already exists before overwriting.
- Rate limiting is per user/channel (default 10 messages/hour in the adapters)
  and admin bypass is explicit configuration, not authentication by itself.

A messenger or external LLM is not part of the local-only computation boundary.
State clearly when a file has crossed a platform/provider boundary. For purely
local operation, use the CLI or Python runner rather than a remote bot.

## Robotary and webchat

`robotary.server` is a small FastAPI catalog/static interface supplied by the
checkout deployment. It loads a curated core-skill catalog and defaults to port
5112; its current binding is broad, so do not expose it to an untrusted network
without authentication, TLS, and a reverse proxy. Importing the module builds
the app/catalog but does not prove that FastAPI, Uvicorn, static files, or a
reachable port are ready. A help/import diagnostic must not start it.

`bot/webchat/index.html` is a browser UI for an OpenClaw bridge, not a direct
ClawBio API. It opens a WebSocket at the current origin, sends an auth token
from the URL query, and expects bridge message types such as `connect`,
`connected`, `chat.send`, and `chat.stream`. The gateway, auth, TLS, and
network policy must be configured separately. Do not put long-lived secrets in
shareable URLs or claim the static HTML is a functioning backend.

## Structured action/result handoff

The runner promotes optional `result.json` fields for adapters:

- `chat_summary_lines`: exact concise summary lines authored by the skill.
- `preferred_artifacts`: files the UI should show first.
- `workflow_state`: lifecycle and state identity, not a global session store.
- `suggested_actions`: structured follow-ups with a stable action id/request.
- `contract_alerts`: path, intent, data, or state discrepancies.
- `report_md`: embedded report text where supplied.

Adapters render these fields and keep a short pending-action bundle scoped to the
sender/channel. A selected action is materialized back through the normal
`clawbio run --input ...` path; never execute fresh shell text from chat.
Without those fields, report and `result.json` remain the durable handoff. Use
[core-runner](../../core-runner/SKILL.md) for ordinary output inspection and
replay.
