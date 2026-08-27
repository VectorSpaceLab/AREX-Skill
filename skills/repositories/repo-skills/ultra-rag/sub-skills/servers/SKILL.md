---
name: servers
description: "Routes UltraRAG MCP server workflows, backend choices, and
  server-level tool and prompt signatures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Servers

Use this sub-skill when the task is about the MCP servers under `servers/`.

## Typical triggers

- `servers/retriever`, `servers/generation`, `servers/prompt`, `servers/corpus`,
  `servers/evaluation`, `servers/custom`, `servers/memory`, `servers/benchmark`,
  `servers/router`, or `servers/sayhello`
- Questions about tool or prompt signatures, outputs, or parameter keys
- Adding a new server tool or prompt
- Choosing between retriever backends, generation backends, or corpus/index
  backends
- Understanding generated `server.yaml` files or server build metadata
- Optional dependency failures inside a server import or backend initialization

## What this sub-skill covers

- MCP server structure and the `UltraRAG_MCP_Server` wrapper.
- Verified tool/prompt signatures and output keys for the public server modules.
- Backend-specific configuration for retrieval, generation, corpus, evaluation,
  and web search.
- Source-level import problems such as missing optional dependencies or a stale
  package version.

## What stays elsewhere

- Pipeline composition, example recipes, and `ultrarag build/run` usage belong
  in `sub-skills/pipelines/`.
- Flask routes, KB storage, and case-study behavior belong in
  `sub-skills/ui-and-storage/`.

## Start here

- Read `references/api-reference.md` for the verified server signatures and
  output contracts.
- Read `references/backends-and-config.md` for backend choices, extras, and
  config keys.
- Read `references/troubleshooting.md` when a server import or backend choice
  fails.
- Run `scripts/inspect_servers.py` to print a live signature summary from a
  checkout-aware environment.

## Common user questions this sub-skill should answer

- How do I add a tool to the retriever or generation server?
- Which parameters does `retriever_search` or `generation.generate` expect?
- Which backend is appropriate for embeddings, BM25, web search, or vLLM?
- Why does a server import fail on this machine?
- What optional package is needed for `evaluate_trec`, `build_mineru_corpus`,
  or `show case`?

## Practical workflow

1. Identify the server family and the exact tool/prompt the task mentions.
2. Check the backend or extra that the server needs.
3. Confirm the registered input and output names before changing a pipeline.
4. Use the inspection script or the reference tables to validate the claim.

## Helpful commands

Use the bundled inspection helper so checkout paths and local server imports are
handled explicitly:

```bash
python sub-skills/servers/scripts/inspect_servers.py --repo-root <checkout>
python sub-skills/servers/scripts/inspect_servers.py --repo-root <checkout> --module servers.generation.src.generation
```

If the task is only about how to wire steps together, go back to the pipelines
sub-skill instead of rewriting server guidance here.
