---
name: adk-code
description: "Use this sub-skill when writing or revising Python ADK agent code
  in an agents-cli scaffolded project, including agent objects, tools,
  callbacks, state, A2A surfaces, event triggers, and recipe selection."
metadata:
  disco-role: operating
  author: Google
  license: Apache-2.0
  version: 1.3.1
  requires:
    bins:
      - agents-cli
    install: "uv tool install google-agents-cli"
disable-model-invocation: true
license: Apache 2.0
---

# ADK Code Patterns

Use this sub-skill inside the `google-agents-cli` repo skill. It is a router plus operating checklist; move into the bundled references for full command flags, schemas, and examples.

## When to Use

- The user wants to implement or modify agent Python code after scaffolding.
- The task asks about tools, callbacks, state, memory, A2A, event triggers, or recipes.
- You need to avoid hand-writing generated A2A/FastAPI surfaces.

## Workflow

1. Inspect the scaffolded app layout before editing.
2. Use recipes for retrieval, sandboxing, memory, OAuth, guardrails, and scheduling instead of inventing flags.
3. Edit agent instructions/tools/state deliberately and preserve generated serving glue.
4. Verify locally with `agents-cli run` and then with eval workflows.

## Read These References

- `references/adk-code-guide.md` — read for adk code guide details.
- `references/adk-python.md` — read for adk python details.
- `references/adk-workflows.md` — read for adk workflows details.
- `references/samples.md` — read for samples details.

## Verification and Safety

Safe checks: inspect scaffolded files and run local `agents-cli run` only when project dependencies and model credentials are ready.

## Boundaries

- Does not scaffold or deploy projects.
- Does not use pytest as the primary oracle for LLM response quality; use eval.

## Related Sub-Skills

- `../workflow/SKILL.md` — lifecycle routing and approval gates.
- `../scaffold/SKILL.md` — project creation/enhancement.
- `../adk-code/SKILL.md` — ADK Python implementation patterns.
- `../eval/SKILL.md` — evaluation loops and metrics.
- `../deploy/SKILL.md` — deployment and infrastructure.
- `../publish/SKILL.md` — Gemini Enterprise registration.
- `../observability/SKILL.md` — logging, tracing, and analytics.
