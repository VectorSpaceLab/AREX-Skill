---
name: cloud-api-and-integrations
description: "Routes PaddleOCR users to the hosted API, MCP server, and
  LangChain integration surfaces."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Cloud API and Integrations

Use this route when the task depends on a hosted PaddleOCR service, an access token, a base URL, or an application integration such as MCP or LangChain.

## Handle these tasks here

- Hosted OCR and document parsing through `PaddleOCRClient` and `AsyncPaddleOCRClient`.
- The `paddleocr api` CLI.
- `paddleocr_mcp` server configuration and provider selection.
- LangChain `PaddleOCRVLLoader` usage and metadata handling.
- API option objects, result saving, and hosted-service troubleshooting.
- Reference-only guidance for the TypeScript/Go API SDK docs under `api_sdk/` when a user asks about the broader official API ecosystem.

## Route away from here

- Local OCR, predictor classes, and engine/device tuning belong in `local-ocr-pipelines`.
- Full structured document pipelines and Office conversion belong in `document-parsing-and-conversion`.
- Training, export, deployment, and TIPC evidence belong in `training-export-and-deployment`.

## Read these references

- [`references/official-api.md`](references/official-api.md) for the Python client, CLI payloads, job lifecycle, and result saving.
- [`references/mcp-and-langchain.md`](references/mcp-and-langchain.md) for MCP provider modes and the LangChain loader.
- [`references/troubleshooting.md`](references/troubleshooting.md) for token, URL, timeout, provider, and resource issues.

## Use the bundled script

- [`scripts/check_official_api_setup.py`](scripts/check_official_api_setup.py) validates hosted-API setup without making a network request by default.

## What future agents should know

- The hosted API client has a synchronous and an async form. Both use token-based auth and raise a dedicated PaddleOCR error hierarchy.
- The CLI and SDK distinguish OCR jobs from document-parsing jobs. Do not mix the wrong `model_type`, `model`, or options dataclass.
- MCP provider choice matters: local inference, AI Studio, Qianfan, and self-hosted modes have different env vars and model restrictions.
- The LangChain loader uses the hosted document-parsing API and returns `Document` objects with raw response metadata.
- Reference the integration docs before asking for a real remote call; a fake-client or payload-check test is often enough for diagnosis.

## Common triggers

- "I have a PaddleOCR access token"
- "Use the hosted API instead of local inference"
- "Set up the MCP server"
- "Load a document through LangChain"
- "Why is the API request failing or timing out?"
