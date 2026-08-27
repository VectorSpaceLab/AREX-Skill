---
name: design-patterns
description: "Use PocketFlow to design LLM apps and agentic workflows with
  workflows, agents, RAG, map-reduce, structured output, multi-agent queues, and
  service/background patterns."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# PocketFlow Design Patterns

Use this sub-skill when the user wants to turn a task into a PocketFlow application design rather than debug a single node or utility function.

## What this sub-skill covers

- Workflow decomposition for article-writing, extraction, planning, and approval flows.
- Agent decision loops and tool/action routing.
- RAG pipelines with offline indexing and online retrieval.
- Map-reduce style document or record processing.
- Structured output with validation-friendly prompts.
- Multi-agent or message-queue style coordination.
- FastAPI/Streamlit/Gradio-style service and background job shapes when they are part of the PocketFlow app structure.
- Cookbook-derived pattern selection and dependency caveats.

## What to read first

- [Pattern recipes](references/pattern-recipes.md)
- [Agentic coding guide](references/agentic-coding-guide.md)
- [Cookbook map](references/cookbook-map.md)
- [Troubleshooting](references/troubleshooting.md)
- [Templates](scripts/design_pattern_templates.py)

## Typical user requests

- "How should I structure this PocketFlow app?"
- "Should I use workflow, agent, or RAG?"
- "How do I add a review/retry loop?"
- "How do I process many docs or files?"
- "How do I design a service-backed or background-job PocketFlow app?"

## Route map

| Need | Read |
| --- | --- |
| Pattern choice and node-level recipe shape | `references/pattern-recipes.md` |
| Docs-first process and project skeleton | `references/agentic-coding-guide.md` |
| Cookbook-style task matching | `references/cookbook-map.md` |
| Architectural failure modes and repair steps | `references/troubleshooting.md` |
| Safe local skeleton output | `scripts/design_pattern_templates.py` |

## Design principles

1. Start with the smallest useful graph.
2. Put schema and task state into the shared store.
3. Keep `exec()` focused on compute and utility calls.
4. Use `post()` to write results and choose the next action.
5. Add validation on outputs that an LLM may produce in an unreliable format.
6. Prefer explicit recipes over clever, over-general node abstractions.

## Boundaries

- Do not use this sub-skill for core runtime signatures or retry semantics; read `core-abstraction` instead.
- Do not use this sub-skill to implement provider-specific LLM wrappers, vector stores, tracing clients, or audio functions; read `utilities` instead.
- Do not bundle credentialed or network-heavy cookbook scripts. Distill them into safe reusable recipes and note optional dependencies.
