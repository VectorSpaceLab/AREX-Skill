---
name: proxy-wrap
description: "Run the Headroom proxy, route LLM providers through it, and wrap
  or unwrap coding agents safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Headroom proxy and agent wrapping

Use this sub-skill when the user needs a live Headroom proxy, provider routing, agent wrapping, or troubleshooting for requests that should pass through Headroom before reaching an LLM provider.

## Route here for

- `headroom proxy` foreground server flags, optimization modes, local endpoints, dashboard, health, metrics, and provider backends.
- `headroom wrap ...` and `headroom unwrap ...` for Claude, Codex, Copilot, VS Code, Aider, OpenClaude, Vibe, Kimi, Grok, Cursor, Grok Build, Cline, Continue, Goose, OpenHands, OpenClaw, OpenCode, OMP, and ZCode.
- Provider-specific base URL, auth, and model routing issues for Anthropic, OpenAI-compatible clients, Codex/ChatGPT backend, GitHub Copilot, Bedrock, Vertex, any-LLM, LiteLLM, and plugin integrations.
- OpenClaw/OpenCode plugin setup and proxy auto-detection.
- Proxy cache-safety, WebSocket/SSE behavior, and Prometheus metrics interpretation.

## Route elsewhere

- Durable deployment lifecycle with `headroom deploy` or `headroom install`: use `../ops/SKILL.md`.
- `headroom mcp`, `headroom memory`, `headroom learn`, and CCR tool registration: use `../memory/SKILL.md`.
- Direct `compress()` or TypeScript SDK application integration that does not need wrapping: use `../sdk/SKILL.md`.

## Fast start

Foreground proxy:

```bash
headroom proxy --host 127.0.0.1 --port 8787
```

Claude Code through a local proxy:

```bash
ANTHROPIC_BASE_URL=http://127.0.0.1:8787 claude
# or durable wrapper:
headroom wrap claude
```

OpenAI-compatible client through a local proxy:

```bash
export OPENAI_BASE_URL=http://127.0.0.1:8787/v1
```

Check a running proxy without sending model traffic:

```bash
python scripts/proxy_livez_check.py --url http://127.0.0.1:8787 --json
```

## References and helper

- `references/proxy-reference.md` covers proxy flags, modes, endpoints, telemetry, and backend routing concepts.
- `references/agent-routing.md` maps agent wrappers and provider-specific routing signals.
- `references/troubleshooting.md` covers common proxy, base URL, auth, cloud, plugin, and cache-safety failures.
- `scripts/proxy_livez_check.py` is a safe loopback health checker for `/livez`, `/health`, and optional `/stats`.

## Safety rules

- Do not run long-lived proxies or durable wrappers unless the user wants that side effect; for diagnosis, use read-only health probes first.
- Do not bind the proxy to non-loopback hosts without explicit user intent and network/security context.
- Do not put API keys, OAuth tokens, cloud credentials, or bearer tokens in shell examples.
- Cloud backends such as Bedrock and Vertex require valid credentials and permissions; local help and synthetic tests do not prove live cloud access.
