---
name: kag
description: "Routes KAG knowledge-construction, question-answering, MCP, and
  benchmark workflows for the OpenSPG KAG package."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# KAG

Use this repo skill for the OpenSPG **KAG** package when the user wants to create, inspect, or use a KAG project, not when they want a generic graph database or generic RAG answer.

## What this skill covers

KAG is a Python toolkit for knowledge augmented generation with three major surfaces:

- project and schema setup through `knext`
- knowledge construction through builder chains and index managers
- query-time reasoning, MCP serving, and benchmark automation

If the task is about a KAG checkout that may be stale, read `references/repo-provenance.md` first.

## First checks

1. Confirm the package is installed with `scripts/check_kag_install.py`.
2. Inspect any `kag_config.yaml` with `scripts/inspect_kag_config.py`.
3. Read `references/configuration-and-registry.md` when you need config keys, registry names, or config discovery rules.
4. Read `references/troubleshooting.md` when imports, config discovery, model keys, or CLI behavior look wrong.

## Choose the right sub-skill

### `sub-skills/knowledge-construction/`
Use this when the user wants to create or restore a project, commit schema, run a builder, choose readers/splitters/extractors/vectorizers/writers, inspect index managers, or validate a project layout before building.

### `sub-skills/question-answering/`
Use this when the user wants to ask questions against a KAG project, inspect solver pipelines, use `knext reasoner` or `knext thinker`, or debug query-time retrieval and answer generation.

### `sub-skills/mcp-and-automation/`
Use this when the user wants to launch or validate `kag mcp-server`, plan MCP tool configs, submit builder jobs to a cluster, or dry-run benchmark automation.

## Shared files

- `references/cli-reference.md` — CLI groups, flags, and when to use each command.
- `references/configuration-and-registry.md` — config discovery, registries, and dynamic component loading.
- `references/troubleshooting.md` — cross-cutting import, config, and runtime failures.
- `scripts/check_kag_install.py` — safe install/import/CLI smoke check from any working directory.
- `scripts/inspect_kag_config.py` — redacted summary of a KAG config file.

## Runtime expectations

- The published distribution name is `openspg-kag`.
- The import names used by future agents are `kag` and `knext`.
- Console entry points are provided by the same distribution.
- `import kag` may need a discoverable `kag_config.yaml`; the bundled install check creates a temporary minimal config so the import can be tested from any directory.
- Keep runtime instructions self-contained. Do not refer future agents to original repo docs or examples outside this skill tree.

## Common requests

- "Help me set up a KAG project"
- "Which KAG index should I use for this corpus?"
- "Why is my KAG answer missing references?"
- "Can I launch KAG as an MCP server or benchmark runner?"

## Working style

- Start with a safe local check before a live server or graph mutation.
- Prefer bundled config and layout helpers over guessing from source tree names.
- Route the task to a sub-skill as soon as the workflow becomes specific.
- Keep provenance in mind before reusing the skill on a different checkout.
- Treat knowledge construction, query answering, and service automation as separate concerns until the user asks to connect them.

## When to stop and read more

- If a request mentions project creation, schema commits, builder chains, or index selection, go to `knowledge-construction`.
- If a request mentions solver pipelines, GQL queries, answer traces, or `knext reasoner`, go to `question-answering`.
- If a request mentions `mcp-server`, builder submission, or benchmark planning, go to `mcp-and-automation`.

## Provenance

Read `references/repo-provenance.md` before refreshing this skill or before deciding whether the current checkout still matches the generated knowledge.
