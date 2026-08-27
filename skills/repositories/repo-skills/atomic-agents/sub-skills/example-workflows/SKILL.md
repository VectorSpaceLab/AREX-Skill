---
name: example-workflows
description: "Use the Atomic Agents example projects as concrete recipes for
  quickstart, multimodal, memory, search, orchestration, MCP, and integration
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Example Workflows

Use this subskill when a task is best answered by mapping the user request to one of the runnable example projects in `atomic-examples/`.

## Read first

- `references/example-index.md` for the categorized example map.
- `references/dependency-matrix.md` for dependency, credential, and backend notes.
- `references/workflows.md` for adaptation guidance.
- `references/troubleshooting.md` for example-specific failure modes.

## Owns

- Choosing the right example project for a user task.
- Explaining what each example demonstrates and what it does not.
- Flagging dependency groups, provider keys, and network needs for examples.
- Translating a repo example into a reusable recipe for another project.

## Does not own

- Core agent construction, memory internals, or hooks; use `../agent-core/SKILL.md`.
- Base tool and CLI / Forge details; use `../tooling-and-forge/SKILL.md`.
- MCP transport internals; use `../mcp-integrations/SKILL.md`.
- Repo maintenance or release commands; use `../repo-development/SKILL.md`.

## Common triggers

- "Which example should I start from?"
- "How do I adapt the quickstart?"
- "Where is the multimodal / RAG / YouTube / memory / hooks example?"
- "Which example demonstrates MCP or progressive disclosure?"
- "Does this example need an API key or network access?"
