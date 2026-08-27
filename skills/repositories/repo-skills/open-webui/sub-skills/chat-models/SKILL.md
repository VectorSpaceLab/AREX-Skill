---
name: chat-models
description: "Route chat, model-selection, prompt, streaming, and
  provider-integration workflows in Open WebUI."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Chat and Models

Use this sub-skill for Open WebUI's day-to-day chat experience, provider setup, model routing, prompt behavior, and playback of model interactions.

## When to use this sub-skill

Use `chat-models` when the user asks about:

- choosing or changing models in the chat UI
- connecting Ollama, OpenAI-compatible, or hosted model providers
- prompt, chat-variable, or message-flow behavior
- streaming responses, multi-model chats, playground usage, or evaluation hooks
- provider / model routing errors that are not file, plugin, or admin problems

## Read these bundled files first

- `references/workflows.md` for the workflow map and provider/model patterns.
- `references/troubleshooting.md` for provider, model, prompt, and streaming failures.
- `../deployment/references/deployment.md` if the user still needs to get the app running first.
- `../../references/configuration.md` for the cross-cutting environment variables.

## Core capabilities

- Provider routing between local and hosted model backends.
- Model selection and model access control.
- Chat prompt handling and variable normalization.
- Streaming and responses plumbing.
- Playground-style testing and evaluation hooks.

## Typical user questions

- "How do I point Open WebUI at Ollama?"
- "How do I connect an OpenAI-compatible provider?"
- "Why does the model not show up in chat?"
- "Why is the response timing out or streaming poorly?"
- "How do I configure fallback or passthrough behavior?"

## Important boundaries

- File uploads, folders, notes, memories, and retrieval belong to `knowledge-files`.
- Plugins, functions, tools, skills, pipelines, and multimodal add-ons belong to `extensions`.
- Auth, groups, users, SCIM, storage, and telemetry belong to `admin-collaboration`.
- Docker or secret-key startup issues belong to `deployment` unless the only issue is a model/provider variable.

## Success shape

A future agent should be able to:

1. Identify the model/provider signal in the request.
2. Explain which provider settings matter.
3. Give a concrete chat-side recovery path.
4. Distinguish model routing failures from general startup, file, or admin failures.
