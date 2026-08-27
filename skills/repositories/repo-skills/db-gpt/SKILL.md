---
name: db-gpt
description: "Use DB-GPT 0.8.1 as an agentic AI data platform: install and
  configure provider profiles, operate its CLI and services, build agents and
  AWEL flows, ingest and retrieve data with RAG, call client/API surfaces, and
  execute code through explicitly bounded sandbox runtimes."
metadata:
  disco-role: operating
license: Apache 2.0
disable-model-invocation: true
---

# DB-GPT

Use this repo skill when a task names **DB-GPT**, `dbgpt`, `dbgpt-app`,
`dbgpt-client`, `dbgpt-ext`, `dbgpt-serve`, or `dbgpt-sandbox`, or asks for an
agentic data assistant that combines models, SQL/code, files, knowledge bases,
RAG, skills, AWEL workflows, APIs, or sandboxed execution.

## Choose the route

- **Install, profiles, TOML configuration, `dbgpt` command routing, web start/stop,
  knowledge/repo/app/trace/migration CLI** → [setup-and-cli](sub-skills/setup-and-cli/SKILL.md).
- **LLM/embedding/reranker providers, model TOML, controller/worker/API-server,
  local models, CUDA, vLLM, llama.cpp, Ollama, or serving** →
  [models-and-serving](sub-skills/models-and-serving/SKILL.md).
- **Agents, tools, skills, middleware, teams, memory/context, AWEL/DAG/flow, or
  HTTP-triggered workflow construction** → [agents-and-awel](sub-skills/agents-and-awel/SKILL.md).
- **Local documents, datasource schemas, chunking, embeddings, retrieval,
  knowledge indexing, vector/full-text/graph stores, or RAG** →
  [data-and-rag](sub-skills/data-and-rag/SKILL.md).
- **Python client, HTTP CRUD/API routes, files/apps/flows, service integration,
  or sandbox execution** →
  [apis-client-and-sandbox](sub-skills/apis-client-and-sandbox/SKILL.md).

When a request spans routes, establish the runtime boundary in this order:
**configuration/provider → data or workflow construction → API/service execution**.
Do not claim that a parsed config, imported package, registry entry, or health
endpoint proves a provider, model, vector store, database, or sandbox is usable.

## Baseline installation and inspection

For the recorded 0.8.1 baseline, use a clean Python 3.10+ environment and
install the public package without relying on a source checkout:

```bash
uv pip install 'dbgpt-app==0.8.1'
dbgpt --version
python -c "import dbgpt, dbgpt_app, dbgpt_client, dbgpt_ext; print('imports ok')"
```

Use `pip` if `uv` is unavailable. Add only the extras needed by the route:
provider, RAG/parser, vector-store, database, local-model, or sandbox variants.
Read [installation](references/installation.md) before adding optional
backends, and [configuration](references/configuration.md) before writing a
profile or TOML file. The bundled [package smoke script](scripts/package_import_smoke.py)
is a read-only import/version check; it never starts a server or contacts a provider.

## Cross-cutting operating rules

1. Keep credentials in environment variables or the user's secret manager. Do
   not print resolved TOML, API keys, passwords, bearer tokens, or provider
   responses containing secrets.
2. Separate local/import/config validation from live provider, model, database,
   vector, graph, API, and sandbox checks. Record the exact boundary and skipped
   prerequisites.
3. Prefer tiny deterministic fixtures and disposable paths. Do not run a
   network installer, download a model, mutate a database, launch a daemon, or
   execute untrusted code as an implicit smoke test.
4. Use the installed package's live Click help and signatures when a flag or
   object is version-sensitive. In particular, model command discovery may
   query a controller even while rendering help; an unreachable controller is
   not a successful deployment.
5. Default DB-GPT's web API is commonly `http://localhost:5670`; confirm the
   actual profile, API version, route prefix, and authentication policy before
   making client calls. Close async clients and clean temporary uploads/sessions.
6. Treat local sandbox execution as a weaker, explicitly opted-in boundary, not
   container isolation. Container runtime/image availability and network policy
   must be verified separately.

Read [cross-cutting troubleshooting](references/troubleshooting.md) for
installation/import, optional dependency, configuration, service, backend, and
safety failures. Source/version context is recorded in
[repo provenance](references/repo-provenance.md); it is not a runtime dependency.
