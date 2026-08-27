---
name: provider-connectors
description: "AgentScope provider, embedding, formatter, and TTS configuration workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# provider-connectors

Use this sub-skill when the task is about provider classes, credentials, provider extras, model names, embeddings, formatters, or TTS.

## Read first

- `references/model-overview.md` for chat model families and credential shapes.
- `references/embedding-overview.md` for embedding model families and dimension notes.
- `references/tts-overview.md` for TTS constructors and streaming defaults.
- `references/troubleshooting.md` for missing-extra, credential, and provider-specific failures.
- `scripts/provider_matrix.py` for a safe availability/import check.

## Typical triggers

- Choose the right extra for OpenAI, Anthropic, DashScope, Gemini, Ollama, Moonshot, DeepSeek, or XAI.
- Compare chat, embedding, formatter, or TTS constructor defaults.
- Fix a provider import or credential problem.
- Check which providers are available in the current environment.

## What belongs here

- `agentscope.credential`
- `agentscope.model`
- `agentscope.embedding`
- `agentscope.formatter`
- `agentscope.tts`
- provider-specific configuration, env vars, and model names

## What does not belong here

- Agent/tool/permission basics → `agent-core`
- RAG and memory workflows → `rag-memory`
- Service deployment and API bootstrap → `service-platform`
- Workspace or sandbox backend setup → `workspace-sandboxes`

## Use pattern

1. Identify the provider family first.
2. Read the matching overview reference for the constructor and default values.
3. Check whether the provider needs a dedicated extra or only the base package.
4. Use `scripts/provider_matrix.py` when you need a safe current-environment status check.
5. Escalate to `rag-memory` only if the issue is really an embedding dimension or retrieval workflow.

## Shared diagnostics

- Run `../../scripts/check_env.py` if the entire package looks stale.
- Read `references/troubleshooting.md` before changing code if the problem is a missing extra, credential class, or model name.

## Cross-links

- If the task needs the agent/tool layer, switch to `agent-core`.
- If the task needs RAG or memory, switch to `rag-memory`.
- If the task needs service bootstrapping or deployment, switch to `service-platform`.
