---
name: extensions
description: "Route plugin, tool, skill, pipeline, MCP, and multimodal extension
  workflows in Open WebUI."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Extensions

Use this sub-skill for Open WebUI extension surfaces: functions, tools, skills, pipelines, MCP/OpenAPI integrations, browser helpers, image/audio add-ons, and terminal-backed helpers.

## When to use this sub-skill

Use `extensions` when the user asks about:

- tools, functions, skills, pipelines, or plugin manifests
- MCP or OpenAPI tool servers
- browser-assisted helpers or Playwright-backed workflows
- image generation/editing or audio/voice extension features
- terminal, code-interpreter, or webhook-backed add-ons

## Read these bundled files first

- `references/workflows.md` for the extension map and setup sequence.
- `references/troubleshooting.md` for manifest, tool-server, browser, and multimodal failures.
- `../../references/configuration.md` for shared extension-related variables.
- `../deployment/references/deployment.md` if the runtime service itself is not available yet.

## Core capabilities

- Extension manifests and function/tool wiring.
- Skill and pipeline routing.
- MCP/OpenAPI connection patterns.
- Browser-based helpers and Playwright-backed loaders.
- Image/audio/voice extensions and terminal-style integrations.

## Typical user questions

- "How do I add a tool or skill to Open WebUI?"
- "How do I connect an MCP server?"
- "Why does the browser helper fail to start?"
- "How do I enable image generation or audio features?"
- "Why does a tool server timeout or fail SSL validation?"

## Important boundaries

- Chat/model routing belongs in `chat-models`.
- Files, notes, memories, and retrieval belong in `knowledge-files`.
- Auth, users, groups, storage, and telemetry belong in `admin-collaboration`.
- Deployment issues such as missing secret keys or bad image tags belong in `deployment`.

## Success shape

A future agent should be able to:

1. Explain the extension surface being used.
2. Name the required backend or helper service.
3. Separate tool-server failures from startup or provider failures.
4. Recover from the most common manifest, browser, or SSL problems.
