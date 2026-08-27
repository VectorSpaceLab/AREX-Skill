---
name: utilities
description: "Use PocketFlow utility patterns for LLM wrappers, search,
  embeddings, vector search, chunking, TTS/audio, visualization, tracing, and
  other external integrations."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# PocketFlow Utilities

Use this sub-skill when the user needs supporting functions that PocketFlow nodes can call: provider wrappers, search helpers, embedding helpers, vector search, audio, visualization, tracing, or environment validation.

## What this sub-skill covers

- Provider-neutral LLM wrapper patterns.
- Search utilities and search-result parsing.
- Chunking helpers.
- Embedding and vector search helpers.
- TTS/audio wrapper patterns.
- Mermaid graph generation and call-stack debugging.
- Tracing and observability integration caveats.
- Safe env-var and dependency validation.

## What to read first

- [Utility recipes](references/utility-recipes.md)
- [Visualization and observability](references/visualization-and-observability.md)
- [Troubleshooting](references/troubleshooting.md)
- [Utility helper](scripts/pocketflow_utilities.py)

## Typical user requests

- "How do I wrap OpenAI/Anthropic/other LLM calls for PocketFlow?"
- "How do I chunk text or build embeddings?"
- "How do I wire a vector search helper?"
- "How do I visualize or debug a graph?"
- "How do I add tracing or handle API-key failures?"

## Route map

| Need | Read |
| --- | --- |
| Provider-neutral utility patterns | `references/utility-recipes.md` |
| Mermaid/debugging/tracing guidance | `references/visualization-and-observability.md` |
| Environment and provider troubleshooting | `references/troubleshooting.md` |
| Safe local utility checks | `scripts/pocketflow_utilities.py` |

## Design principles

1. Keep provider calls outside the graph runtime.
2. Make env vars and credentials explicit.
3. Validate dimensions, schemas, and return types early.
4. Separate local smoke checks from networked or credentialed integrations.
5. Prefer small, reusable helpers over huge mixed-purpose utility modules.

## Boundaries

- Do not duplicate PocketFlow core runtime semantics; read `core-abstraction` for node/flow behavior.
- Do not claim the skill bundles vendor services or paid APIs; document them as optional dependencies or external integrations.
- Do not keep tracing, browser, audio, or cloud service assumptions hidden in prose; list them explicitly.
