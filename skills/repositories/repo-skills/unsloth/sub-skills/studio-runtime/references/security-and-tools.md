# Studio Security and Tool Policy

Studio is designed for local-first operation, but it can expose powerful API and tool capabilities. Treat host binding, tunnel choice, API keys, external providers, MCP tools, code execution, and document ingestion as security-sensitive.

## Exposure Modes

| Mode | Command Shape | Raw Server Bind | Public URL | Security Posture |
| --- | --- | --- | --- | --- |
| Local-only | `unsloth studio -p 8888` | `127.0.0.1` | none | Safest default; reachable only from the same machine unless another tunnel/proxy is added. |
| Secure tunnel | `unsloth studio --secure -p 8888` | forced `127.0.0.1` | Cloudflare HTTPS quick tunnel | Recommended for remote browser/API access; fails closed if the tunnel cannot start. |
| Raw network bind | `unsloth studio -H 0.0.0.0 -p 8888` | all interfaces | raw `http://host:port`; Cloudflare may also be printed | Operator-owned exposure; use only on trusted networks or behind firewall/VPN/reverse proxy. |
| API-only | `unsloth studio --api-only` | as selected | API routes only | No frontend serving; still exposes API and tools according to auth/policy. |

`--secure` and `--no-cloudflare` are contradictory; Studio rejects them together. Without `--secure`, `--cloudflare` on a raw `0.0.0.0` bind can add a HTTPS link, but it does not remove the raw network port.

## Host Binding Warnings

When advising a remote launch:

- Prefer `--secure` if the user needs a browser link or quick remote API access.
- Warn before `-H 0.0.0.0`: the server is reachable by other machines that can route to that port.
- Warn that anyone with both URL and API key can use Studio API endpoints.
- Recommend `--disable-tools` for any network-exposed server unless server-side tools are essential and the user controls all clients.
- If raw binding is required, recommend firewall/VPN/security group restrictions and a private API key.
- Do not claim Cloudflare quick tunnels provide user authentication by themselves; Studio auth/API keys still matter.

## API Keys and Auth

Studio uses browser login/JWTs and API keys. API keys are bearer secrets.

Key facts:

- `/api/auth/api-keys` returns the raw API key once; later list calls show only metadata/prefixes.
- `unsloth studio run` creates an API key in-process after local server health succeeds.
- `unsloth connect` can auto-mint a local key only for verified loopback Studio servers.
- Remote Studio servers require an explicit API key via `--api-key` or `UNSLOTH_API_KEY`.
- Saved keys are scoped per exact server base URL; this avoids replaying a key to unrelated servers.
- OpenAI-compatible clients authenticate with bearer keys against `/v1/*`.
- If a key may have been exposed, revoke it through `/api/auth/api-keys/{key_id}` or the Studio UI and create a new one.

Do not paste API keys into public logs, issue trackers, screenshots, or skill/report files. In guidance, use placeholders such as `sk-...`.

## Server-Side Tools

Studio supports server-side tools such as web search, Python/terminal code execution, MCP-backed tools, and artifact/sandbox flows. Tools run with the privileges of the Studio server process.

Policy controls:

| Control | Effect |
| --- | --- |
| No flag | Tools are enabled by default; per-request/per-chat UI settings are honored. |
| `--disable-tools` | Forces server-side tools off for every request. |
| `--enable-tools` | Forces server-side tools on for every request. |
| Request/UI `enable_tools` | Resolved against process-level policy; process policy wins when explicit. |

Important warnings:

- On a network-exposed or Cloudflare-exposed server, server-side tools can let anyone with the API key execute code/tools as the server user.
- `--secure` gives HTTPS transport and fail-closed tunnel behavior; it does not make a shared API key safe.
- For demos, shared links, classrooms, support sessions, or untrusted networks, use `--disable-tools` unless code/tool execution is the point and the environment is disposable.
- When troubleshooting tool behavior, confirm both the launch flag and the request/UI setting.

## MCP and Stdio Tool Gate

MCP servers can be HTTP(S) or stdio command transports. Stdio MCP is more dangerous because it starts local commands.

Observed policy:

- HTTP(S) MCP server URLs are accepted as remote endpoints.
- Stdio command transports are gated by `UNSLOTH_STUDIO_ALLOW_STDIO_MCP=1`.
- Loopback launches can auto-enable stdio MCP unless explicitly disabled; network binds do not auto-enable it.
- `--disable-tools` turns off auto-enabled loopback stdio MCP, but an explicit `UNSLOTH_STUDIO_ALLOW_STDIO_MCP=1` opt-in can still allow it.
- Explicit `UNSLOTH_STUDIO_ALLOW_STDIO_MCP=0` disables stdio even on loopback.
- Colab/proxied hosted environments do not auto-enable stdio MCP just because the backend sees loopback.

Guidance:

- Do not recommend stdio MCP on a server reachable by untrusted clients.
- Review command strings before enabling stdio MCP; examples include `npx ...`, `python -m ...`, or absolute binaries.
- Prefer HTTP(S) MCP endpoints for remote integrations.
- If a tool list is unexpectedly empty, check `UNSLOTH_STUDIO_ALLOW_STDIO_MCP`, host bind, and `--disable-tools`.

## Provider Credentials

External provider routes support provider registry, saved metadata, encrypted key tests, and model listing. Treat provider credentials as live billing/secrets.

Safe handling:

- Use `/api/providers/public-key` before sending encrypted provider API keys from a UI/client.
- If decryption fails, refresh the frontend/client because the RSA public key fingerprint may have changed.
- Provider tests decrypt the key server-side and use it for a lightweight request; raw keys are not stored in provider metadata.
- Custom providers require a base URL and a model ID for a chat-completions probe.
- For Gemini/custom proxies, model filtering depends on host/provider type; if model lists are empty, check base URL and provider type.
- Never persist provider keys in generated public skill files or logs.

## RAG, Uploads, and Signed File Previews

RAG routes ingest user documents into `rag/uploads` and `rag.db`. Security-relevant behavior:

- Upload filenames are sanitized; stored paths are server-owned UUID-style paths.
- Empty files and unsupported extensions are rejected.
- If `sqlite-vec` is unavailable, routes return `503` rather than partially operating.
- Search can target knowledge base, thread, or project scopes.
- File previews use short-lived HMAC-signed URLs so PDF range requests can work without bearer headers.
- Signed file serving checks the token and confines the served path under the RAG uploads root.

Guidance:

- Do not upload secrets to a shared Studio server unless the server operator is trusted.
- If previews fail, distinguish auth failure, expired signed URL, missing stored file, and unsupported media type.
- If ingestion fails, inspect job status/events before retrying or deleting files.

## Remote Code and Model Trust

Model loading can involve remote code or unsafe model files. Studio exposes remote-code scanning and explicit approval fields.

Guidance:

- Keep `trust_remote_code` false unless the user trusts the repo and understands code execution risk.
- Use the remote-code scan route/UI before approving custom model code.
- Pin approvals to the fingerprint of the scanned code when possible.
- Treat local model paths and native path leases as sensitive filesystem access; do not expose arbitrary host paths to untrusted users.

## llama.cpp and GGUF Pass-Through Boundaries

Studio owns some llama-server arguments for safety and consistency. It rejects managed flags such as model identity, host/port/path/API prefix/reuse-port, auth/TLS, llama-server UI/model-autoload flags, embedding/rerank server-mode switches, `--tools`, `--mmproj`, and parallel slots.

Allowed pass-through settings can still affect safety/performance:

- `-c` / `--ctx-size` increases context and KV cache memory.
- `--cache-type-k` / `--cache-type-v` changes memory/quality tradeoffs.
- `--chat-template-file`, `--jinja`, and template flags alter prompt/tool formatting.
- `--no-mmproj` or `--no-mmproj-auto` disables vision companion auto-loading.
- Thread, GPU offload, split mode, and speculative decoding flags can change resource use.

When debugging, report the full intended pass-through args and check Studio's validation error before trying to bypass it.

## Reverse Proxy and Forwarded Headers

Studio's login rate limiting trusts the direct client address by default. `X-Forwarded-For` / `Forwarded` headers are honored only when `UNSLOTH_STUDIO_TRUST_FORWARDED` is set to a truthy value.

Guidance:

- Only set forwarded-header trust behind a trusted reverse proxy that strips untrusted incoming forwarded headers.
- Do not enable it for raw internet exposure without a controlled proxy.

## Secure Launch Recipes

Local private work:

```bash
unsloth studio -p 8888
```

Remote browser/API with no raw port exposure:

```bash
unsloth studio --secure -p 8888 --disable-tools
```

Trusted LAN raw bind with explicit tool disable:

```bash
unsloth studio -H 0.0.0.0 -p 8888 --disable-tools
```

One-line GGUF serving for a coding agent, secure tunnel, tools disabled:

```bash
unsloth studio run --model org/model-GGUF --gguf-variant Q4_K_M --secure --disable-tools
```

If the user needs tools remotely, make the tradeoff explicit:

```bash
unsloth studio --secure -p 8888 --enable-tools
```

Then tell them not to share the API key and to use a disposable or tightly controlled environment.

## Security Triage Checklist

1. Identify bind mode: loopback, `--secure`, raw `0.0.0.0`, reverse proxy, or SSH tunnel.
2. Identify who has URL access and who has API key access.
3. Check whether `--disable-tools` or `--enable-tools` was used.
4. Check stdio MCP env: `UNSLOTH_STUDIO_ALLOW_STDIO_MCP`.
5. Revoke and rotate API keys after accidental exposure.
6. For provider failures, rotate provider keys if they were logged or pasted.
7. For remote-code model loads, require scan/approval before `trust_remote_code`.
8. For RAG/file-preview incidents, delete affected documents and verify signed URLs expire.
