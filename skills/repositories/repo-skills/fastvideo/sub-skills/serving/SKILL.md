---
name: serving
description: "Guides FastVideo HTTP and WebSocket serving, typed request contracts, health checks, session state, and server configuration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Serving

Use for `fastvideo serve`, OpenAI-compatible HTTP generation, streaming WebSocket
sessions, liveness, continuation state, and operator defaults.

## Choose the transport

- No `streaming` block: stateless HTTP server with video/image endpoints.
- A `streaming` block: WebSocket `/v1/stream` sessions with JSON control frames
  and binary fMP4 media.
- `router-serve`: separate routing/load-balancing configuration; treat it as
  deployment infrastructure, not the generation request API.

Launch with a nested config:

```bash
fastvideo serve --config serve.yaml
fastvideo serve --config serve.yaml --server.port 9000
```

Read [HTTP contract](references/http-contract.md), [streaming contract](references/streaming-contract.md),
and [server troubleshooting](references/troubleshooting.md). Use the bundled
[config helper](scripts/make_serve_config.py) to create a safe template; review
model, host, port, output, and credential settings before starting a listener.

## Operational rules

Health checks should be cheap and should not require a full generation unless an
operator explicitly wants that. HTTP request fields override explicit
`default_request` fields, which override hardcoded fallbacks; omitted schema
defaults do not become operator intent. Streaming sessions have timeout and
segment caps and terminal states; clients must send the correct opening frame.

Do not expose a server publicly without authentication/network controls supplied
by the deployment environment. Prompt enhancement and safety integrations are
optional and may require credentials or model files.
