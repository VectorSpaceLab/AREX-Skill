---
name: server-webui-and-protocols
description: "Operate gptme server, Web UI, REST/SSE API, TUI, ACP, deployment,
  security, and protocol integration workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# server-webui-and-protocols

Use this sub-skill for tasks about `gptme-server`, the REST/SSE API, the bundled or Vite Web UI, `gptme-tui`, ACP editor integration, deployment hardening, reverse proxies, or desktop sidecar behavior.

Keep this file as the router. Open the bundled references for details; do not depend on a target checkout's documentation when answering operational questions.

## Route here for

- starting or probing `gptme-server`, choosing server options, or checking server route availability
- HTTP API, Server-Sent Events, auth cookies, bearer token handling, CORS, Host validation, or Local Network Access
- Web UI connection setup, multi-server settings, message metadata, streaming state, markdown rendering, or frontend/backend protocol mismatches
- ACP shim/direct/module launch, editor protocol lifecycle, stdout/stderr protocol failures, or server-side ACP step mode
- `gptme-tui` install, options, key limitations, or switching between TUI and CLI conversations
- Docker Compose self-hosting, nginx reverse proxy, systemd service shape, public exposure hardening, or parent-death sidecar cleanup

## Route away

- Generic terminal conversation usage, prompts, slash commands, log browsing, or `gptme-agent` CLI: route to `cli-and-conversations`.
- Provider keys, model selection, credential storage, provider plugins, or local model config: route to `configuration-and-providers`.
- Built-in tools, plugins, hooks, browser/computer tool internals, MCP, skills, or lessons: route to `tools-and-extensibility`.
- Evaluation suites, benchmark runs, SWE-bench/T-bench, Docker eval isolation, or leaderboards: route to `evals-and-benchmarks`.
- Maintainer-only checkout work such as frontend test selection, package release checks, lint/typecheck strategy, or code-review policy: route to `repo-development`.

## Read first

- [references/server-api.md](references/server-api.md) — install/serve options, safe help checks, auth/CORS/Host validation, route families, SSE events, message metadata, and `GptmeApiClient`.
- [references/webui-api.md](references/webui-api.md) — bundled vs Vite Web UI, multi-backend behavior, frontend development gotchas, markdown paths, message metadata/SSE flow, Step grouping, and `ChatInput` state.
- [references/acp-and-tui.md](references/acp-and-tui.md) — ACP shim/direct/module launch, protocol lifecycle, stdio failure modes, and TUI options/limitations.
- [references/deployment.md](references/deployment.md) — Docker Compose, nginx reverse proxy, systemd service pattern, self-hosting security, and sidecar parent-death behavior.
- [references/troubleshooting.md](references/troubleshooting.md) — concrete symptoms, causes, and recovery steps for connection, streaming, metadata, ACP, TUI, and deployment failures.

## Safe helper scripts

- [scripts/probe_gptme_server.py](scripts/probe_gptme_server.py) probes a running server's root page, `/api/v2`, `/api/v2/version`, and `/api/v2/server/health` with an optional bearer token. It performs only read-only requests and supports `--help`.
- [scripts/check_webui_message_metadata.py](scripts/check_webui_message_metadata.py) validates representative REST/SSE message dictionaries and compares the metadata fields expected by the Web UI. It supports JSON, JSON lines, and `data: {...}` SSE samples and supports `--help`.

## Fast operating checklist

1. Identify the surface: local server, hosted Web UI, Vite frontend development, TUI, ACP, deployment, or sidecar cleanup.
2. For browser connection failures, check token, exact CORS origin, and Local Network Access together; each is a separate gate.
3. For message badge/rendering problems, compare REST conversation payloads with SSE `message_added` and `generation_complete` payloads before changing frontend code.
4. For ACP, treat stdout as JSON-RPC-only; logs and diagnostics must go to stderr.
5. For persistent deployments, prefer a stable `GPTME_SERVER_TOKEN`, loopback bind plus reverse proxy, disabled proxy buffering for SSE, and explicit parent-death watching for sidecars.
