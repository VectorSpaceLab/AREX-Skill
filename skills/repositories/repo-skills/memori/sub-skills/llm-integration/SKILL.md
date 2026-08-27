---
name: llm-integration
description: "Routes Memori Python LLM registration, provider/framework recipes,
  and wrapper troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# LLM Integration

Use this sub-skill for Python-side LLM client registration, provider choice,
framework adapters, and wrapper troubleshooting.

## Use when

- The request mentions `llm.register(...)`, OpenAI, Anthropic, Gemini, xAI,
  LangChain, Agno, PydanticAI, OpenAI-compatible clients, or unsupported
  provider errors.
- The user is choosing between direct clients and named framework arguments.
- The task is about Python provider wiring, not cloud API keys or database
  setup.

## Read first

- `references/registration-api.md` for exact signatures and routing rules.
- `references/provider-and-framework-recipes.md` for supported provider
  patterns.
- `references/troubleshooting.md` for mixed-registration and provider errors.
- `scripts/inspect_llm_registration.py` for a safe local inspection helper.

## What this sub-skill owns

- Unified `Memori().llm.register(...)` usage.
- Direct client registration and named framework registration.
- Deprecated accessor migration notes.
- Provider wrapper troubleshooting and optional SDK presence checks.

## What it does not own

- Cloud API key and MCP setup: use `cli-and-cloud`.
- BYODB storage or provisioning: use `byodb-storage`.
- Recall/session/embeddings/native runtime: use `memory-and-search`.
- TypeScript `llm.register` details: use `typescript-sdk`.

## Safe first check

Run the bundled inspection helper before suggesting provider-specific code:

```bash
python scripts/inspect_llm_registration.py
```

That helper only reads installed package metadata and optional SDK presence; it
never contacts a provider.
