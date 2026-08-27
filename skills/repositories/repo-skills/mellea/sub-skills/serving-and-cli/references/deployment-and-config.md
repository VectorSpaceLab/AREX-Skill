# Deployment and configuration

`m serve` is a lightweight application loader and OpenAI-compatible FastAPI
process. Use it directly for local or trusted-network development. Production
exposure needs an external security and process boundary.

## Installation matrix

Use the project's active `uv` environment and install only the selected
features:

```bash
uv add "mellea[cli]"       # command discovery, decompose, eval, fix
uv add "mellea[server]"    # adds FastAPI and Uvicorn; includes cli
uv add "mellea[hf]"        # only for Hugging Face inference or m alora
```

The server extra does not install every model provider. Add only the backend
extra required by the served application. Provider packages, model identifiers,
credentials, endpoints, and device compatibility belong to
`backends-and-models`.

Before runtime work:

```bash
uv run python scripts/check_cli_surface.py --mode static
uv run python scripts/check_cli_surface.py --mode help --target serve
```

These checks parse installed files or render help; neither imports the target
application nor starts a server.

## Application design checklist

Keep the app file narrow and review it before launch:

- Define exactly one top-level `serve` callable accepting `input`,
  `requirements`, and `model_options`; add `format` and `client_options` only
  when needed.
- Validate an empty message list, accepted roles/content, request-specific size
  limits, allowed requirements, and unknown generation options.
- Convert multimodal input with `ChatMessage` helpers rather than indexing raw
  dictionaries.
- Map client model IDs through a fixed internal allowlist.
- Keep provider URLs, tokens, and credential lookup server-side.
- Raise short, sanitized `ValueError` messages for intended 400 responses.
  Unexpected failures should remain generic to clients and detailed only in
  protected logs.
- Do not make downloads, provider calls, remote writes, or migrations at import
  time. Import occurs before the socket starts.
- Return an uncomputed thunk only for a streaming request and only when the
  backend supports incremental async output.

A module-level backend or stateless session can avoid per-request setup cost.
A module-level `MelleaSession` with mutable chat context, however, is shared by
all requests and can mix user histories under concurrency. For multi-user
service, create request-local context or partition context by an authenticated
server-side identity; do not use the unauthenticated request `user` field as an
authorization boundary. Protect non-thread-safe shared objects with appropriate
concurrency controls.

## Local launch plan

`m serve` has no dry-run, reload, worker-count, or daemon flags. Launch only
after app review:

```bash
# Safe read-only port inspection; absence of output means no listener was shown.
ss -ltn '( sport = :8080 )' 2>/dev/null || true

# Long-running, side-effectful launch.
uv run m serve app.py --host 127.0.0.1 --port 8080
```

The installed defaults are `0.0.0.0:8080`; specify both values so behavior is
reviewable. Do not rely on older material that uses port 8000. Do not rely on
the command's illustrative default script path.

In a second terminal, liveness is:

```bash
curl --fail --silent http://127.0.0.1:8080/health
```

A minimal completion call is:

```bash
curl --fail-with-body http://127.0.0.1:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{
  "model": "local-default",
  "messages": [{"role": "user", "content": "Reply in one sentence."}],
  "temperature": 0.2,
  "max_tokens": 128
}
JSON
```

For streaming, use `curl -N`, set `"stream":true`, and optionally set
`"stream_options":{"include_usage":true}`. Preserve `text/event-stream` and
disable response buffering in any proxy.

An OpenAI Python client points its base URL at `/v1`:

```python
from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:8080/v1", api_key="unused-locally")
response = client.chat.completions.create(
    model="local-default",
    messages=[{"role": "user", "content": "Reply in one sentence."}],
)
print(response.choices[0].message.content)
```

The placeholder key is only appropriate because the built-in local service does
not authenticate. Never infer that a public deployment can safely use a dummy
key.

## Configuration layers

Keep four concerns separate:

1. **Process:** app path, host, and port supplied to `m serve`.
2. **Route:** fixed mapping from client-facing model aliases to preconfigured
   internal sessions/backends.
3. **Generation:** allowlisted `model_options` such as temperature, max new
   tokens, seed, stream, and permitted tool fields.
4. **Provider:** endpoint, credential source, model identifier, device, and
   provider-specific timeout owned by the backend configuration.

Do not let unknown HTTP fields cross those layers unchecked. The request parser
allows extras and the current server forwards unknown top-level fields into
`model_options`. Filter before backend use.

Use environment variables or a secret manager for provider credentials, not
request JSON, source files, command-line history, generated decomposition
programs, or debug output. Keep a separate non-secret deployment configuration
for allowed model aliases and limits.

## Production boundary

The built-in process does not add authentication, TLS, quotas, rate limits,
body-size limits, tenant isolation, CORS, or authorization. Before exposure to
an untrusted network, place it behind a controlled gateway or wrapper that
provides:

- TLS and authenticated identity;
- authorization for model routes and tool capabilities;
- request size, timeout, concurrency, and rate limits;
- SSE-aware proxy settings and idle timeouts;
- protected, redacted logs and request correlation;
- process supervision, restart policy, and graceful shutdown;
- readiness that checks the selected backend when appropriate;
- network egress restrictions for provider and multimodal URLs.

`GET /health` proves only that the FastAPI process can respond. It is not a
backend readiness check and should not trigger an expensive generation.

The command's wildcard default exposes every interface. Binding to loopback and
using a local reverse proxy is safer. Cross-origin browser use is not configured
by default; add an explicit, narrow CORS policy in a controlled application
boundary rather than enabling every origin.

## Observability and failure handling

Capture startup output and protected server logs. A normal non-streaming
unexpected error intentionally hides provider detail from the client, so logs
are needed to distinguish app, backend, schema, and network failures. Streaming
failures occur after status 200 and appear as SSE error payloads; clients must
parse events through `[DONE]` rather than relying only on HTTP status.

Apply bounded provider retries outside the HTTP client loop and do not retry
non-idempotent tool actions blindly. Define request and backend timeouts at the
appropriate layer. If a route includes sampling loops, evaluate its worst-case
latency and generation count in `sampling-and-evaluation` before setting gateway
timeouts.

## Change control

Before deployment, record and test:

- Mellea version and installed extras;
- app checksum or release identifier;
- allowed client model aliases and actual backend routes;
- supported request fields and ignored fields;
- streaming and structured-output capabilities per route;
- maximum request size, token cap, timeout, and concurrency;
- expected 400, 500, and stream-error behavior;
- rollback procedure and a local-only smoke request.

Do not use `m decompose`, `m fix`, or `m alora` inside service startup. Generate,
review, migrate, or train in a separate controlled workflow, then deploy a fixed
artifact.
