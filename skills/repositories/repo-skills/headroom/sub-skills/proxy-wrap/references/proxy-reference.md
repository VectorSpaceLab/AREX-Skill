# Headroom proxy reference

## Public proxy entry points

- `headroom proxy` starts the local optimization proxy.
- `headroom wrap` starts a proxy and configures an agent or editor to send traffic through it.
- `headroom unwrap` removes durable wrap changes when the command supports it.

## Verified foreground proxy flags

The proxy CLI exposes the following core options:

- `--host` and `--port` for bind target.
- `--workers` for process count.
- `--limit-concurrency`, `--max-connections`, and `--max-keepalive` for transport limits.
- `--http2/--no-http2` for upstream HTTP/2 behavior.
- `--http-proxy` for upstream HTTP proxy URL.
- `--keepalive-expiry` for idle upstream connection lifetime.
- `--mode token|cache` for optimization mode selection.

The help text also documents environment variables such as `HEADROOM_HOST`, `HEADROOM_PORT`, `HEADROOM_WORKERS`, `HEADROOM_LIMIT_CONCURRENCY`, `HEADROOM_MAX_CONNECTIONS`, `HEADROOM_MAX_KEEPALIVE`, `HEADROOM_HTTP2`, `HEADROOM_HTTP_PROXY`, and `HEADROOM_KEEPALIVE_EXPIRY`.

## Routing and backends

Headroom's proxy can route through several provider families:

- Anthropic-style messages.
- OpenAI-compatible chat/completions and responses.
- Codex / ChatGPT backend handling.
- GitHub Copilot variants.
- Bedrock and Vertex-native backends.
- any-LLM and LiteLLM-based backends.

The proxy and wrap layers are intentionally separate from the durable install layer. If the user wants a persistent service, route them to `ops` rather than using these foreground commands.

## Agent wrapping behavior

Typical routing signals:

- `headroom wrap claude` configures Claude Code to send traffic through the local proxy.
- `headroom wrap codex` handles OpenAI Codex CLI launch env and base URLs.
- `headroom wrap copilot` has special subscription/auth handling and can preserve model selection.
- `headroom wrap vscode` and `headroom wrap vscode-claude` modify editor integration without replacing the editor itself.
- `headroom wrap openclaw` and `headroom wrap opencode` install plugin or provider-route layers.

For a durable setup, prefer `headroom init` or `headroom install` only when the user explicitly wants persistent local configuration outside the current shell.

## Health and telemetry

- `/health` and `/livez` are the primary health probes.
- `/dashboard` is the local savings dashboard.
- `/metrics` exposes Prometheus-format metrics.
- `inspect` and `perf` surface log-based details and can be used to confirm whether routing or compression is actually happening.

## Common proxy failure cues

- Claude Code in Bedrock mode may bypass `ANTHROPIC_BASE_URL` and never hit the proxy.
- A base URL that points at the wrong path or port can look like a successful CLI launch but still send traffic directly to the provider.
- OpenClaw and OpenCode may fall back to PATH/npm/python launchers if a local proxy is missing.
- Corporate TLS inspection can affect downloads or model asset resolution even when the proxy itself is reachable.
