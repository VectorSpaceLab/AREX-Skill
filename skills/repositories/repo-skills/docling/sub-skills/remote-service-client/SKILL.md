---
name: remote-service-client
description: "Use Docling through a remote docling-serve service: convert-remote
  CLI, service client SDK, async jobs, batches, chunking, credentials, timeouts,
  and network-safe troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Remote Service Client

Use this sub-skill when the task involves a running `docling-serve` endpoint, the `docling convert-remote` CLI, or the `docling.service_client` SDK.

## Route Here

- Convert documents through a remote service instead of local `DocumentConverter`.
- Configure `DOCLING_SERVICE_URL`, `DOCLING_SERVICE_API_KEY`, `--service-url`, or `--api-key`.
- Use `DoclingServiceClient` or `AsyncDoclingServiceClient` for `convert`, `convert_all`, async task jobs, batch sources, result targets, or chunk endpoints.
- Diagnose remote auth, service reachability, task timeouts, websocket/polling behavior, quotas, missing tasks, or presigned artifact access.

## Route Elsewhere

- Local file conversion, local CLI output/export behavior, and non-service `DocumentConverter` usage belong in the conversion/CLI sub-skill.
- Local pipeline internals that call remote model APIs, such as picture-description API models, belong in the advanced-pipelines sub-skill; note those pipeline internals require explicit remote-service enablement on the service side.
- ASR, VLM, GPU, MLX, or model-download setup belongs in the relevant pipeline/backend sub-skill unless the issue is only service-client connectivity.

## Start Points

- For Python SDK usage, read `references/service-client.md`.
- For `docling convert-remote`, read `references/remote-cli.md`.
- For failures and safe preflight checks, read `references/troubleshooting.md` and use `scripts/check_service_config.py`.

## Safety Defaults

- Do not upload documents during configuration checks unless the user explicitly asks for a real conversion.
- Prefer no-network validation first; use `scripts/check_service_config.py --ping` only when the user authorizes a service health request.
- Treat service URLs, API keys, private artifact URLs, and presigned result links as credentials or sensitive infrastructure details.
