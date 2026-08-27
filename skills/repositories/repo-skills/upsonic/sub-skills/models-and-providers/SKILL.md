---
name: models-and-providers
description: "Owns provider/model selection, profile tuning, registry lookups,
  and credential guidance for Upsonic's model layer."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# models-and-providers

Use this route for provider/model strings, provider inference, model profiles, model settings, registry lookups, and credential troubleshooting.

## Include

- `infer_model`, `infer_provider`, provider classes, and `provider/model` normalization.
- `ModelProfile`, `ModelProfileSpec`, default profile behavior, and structured-output capability hints.
- Credential and environment-variable guidance for model providers.
- Registry and selection workflows that need to know which model names are available.

## Exclude

- Core task execution and streaming semantics → [agent-runtime](../agent-runtime/SKILL.md)
- Tools and MCP wiring → [tools-and-mcp](../tools-and-mcp/SKILL.md)
- Session persistence and memory → [chat-memory-storage](../chat-memory-storage/SKILL.md)
- Retrievers, loaders, OCR, and vector databases → [knowledge-rag](../knowledge-rag/SKILL.md)

## Start here

- [references/provider-reference.md](references/provider-reference.md)
- [references/model-selection.md](references/model-selection.md)
- [references/troubleshooting.md](references/troubleshooting.md)
- [scripts/list_model_registry.py](scripts/list_model_registry.py)
