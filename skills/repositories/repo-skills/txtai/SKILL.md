---
name: txtai
description: "Use txtai for semantic search, embeddings databases, RAG, LLM
  orchestration, agents, deterministic workflows, and API deployment."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# txtai

txtai is an all-in-one Python AI framework for semantic search, embeddings databases, retrieval augmented generation (RAG), LLM orchestration, agents, deterministic workflows, and FastAPI/OpenAI-compatible services.

Use this root skill to choose the right txtai sub-skill, install the correct optional extras, and run safe environment checks. Keep detailed workflows in the linked sub-skills and references.

## Start Here

1. Confirm the package import and version.
   ```bash
   python - <<'PY'
   import importlib.metadata
   import txtai
   print(importlib.metadata.version("txtai"))
   print(txtai.Embeddings, txtai.Application, txtai.Workflow)
   PY
   ```
2. Read [references/installation-and-extras.md](references/installation-and-extras.md) before installing optional dependencies.
3. Run `python scripts/check_txtai_environment.py --help` to inspect imports and optional capabilities without downloading models.
4. Read [references/troubleshooting.md](references/troubleshooting.md) when imports, model backends, optional extras, config files, API startup, or offline runs fail.
5. Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a source checkout.

## Route By Task

| User task | Read |
| --- | --- |
| Build an embeddings index, semantic search, SQL search, hybrid sparse+dense search, graph search, object storage, subindexes, save/load, or index maintenance | [sub-skills/embeddings-search/SKILL.md](sub-skills/embeddings-search/SKILL.md) |
| Compose deterministic pipelines/workflows for extraction, chunking, summarization, translation, transcription, image/audio/data processing, YAML task chains, schedules, or lazy generator debugging | [sub-skills/pipelines-and-workflows/SKILL.md](sub-skills/pipelines-and-workflows/SKILL.md) |
| Build RAG, direct LLM calls, txtai `Agent` tools, embeddings-backed tools, agent teams, prompt templates, or backend selection for hosted/local models | [sub-skills/agents-and-llm-orchestration/SKILL.md](sub-skills/agents-and-llm-orchestration/SKILL.md) |
| Configure `Application`, serve FastAPI/Uvicorn APIs, OpenAI-compatible endpoints, MCP, auth, custom endpoints, clustering, Docker/cloud/serverless, observability, or console usage | [sub-skills/api-and-deployment/SKILL.md](sub-skills/api-and-deployment/SKILL.md) |

## Installation Choices

Install the smallest dependency set that matches the task:

```bash
pip install txtai
pip install "txtai[api]"       # FastAPI, OpenAI-compatible API, MCP/service routes
pip install "txtai[agent]"     # Agent support and smolagents integration
pip install "txtai[pipeline]"  # broad pipeline extras; prefer narrower groups when possible
pip install "txtai[workflow]"  # scheduling, file/data workflow extras
pip install "txtai[graph]"     # graph/network search extras
pip install "txtai[database]"  # DuckDB/SQLAlchemy database extras
```

Avoid `txtai[all]` unless the user explicitly needs nearly every optional subsystem. txtai optional groups can pull large ML, audio, image, database, API, cloud, or CUDA-adjacent packages. See [references/installation-and-extras.md](references/installation-and-extras.md) for the full group map.

## Public API Anchors

- `txtai.Embeddings(config=None, models=None, **kwargs)` builds and queries embeddings databases.
- `txtai.Application(config, loaddata=True)` loads YAML/dict application config for APIs, pipelines, workflows, agents, and embeddings.
- `txtai.Workflow(tasks, batch=100, workers=None, name=None, stream=None)` chains callable tasks and yields lazy generator output.
- `txtai.LLM(path=None, method=None, **kwargs)` runs local, hosted, or custom generation backends.
- `txtai.RAG(similarity, path, ..., template=None, context=None, output="default", system=None, **kwargs)` joins retrieval with generation.
- `txtai.Agent(model=..., tools=[...], max_steps=...)` requires the agent extra; without it, imports can resolve to a placeholder that raises when constructed.

## Common Routing Pitfalls

- If a prompt asks for a chatbot that answers from documents, split the work: use `embeddings-search` to build the store, then `agents-and-llm-orchestration` for `RAG` templates and generation.
- If a prompt asks for repeatable extraction/summarization/translation over many items, prefer `pipelines-and-workflows`; use agents only when tool choice or multi-step reasoning is required.
- If a prompt asks for a service endpoint, route to `api-and-deployment` even when the underlying route calls embeddings, workflows, or RAG.
- If a prompt names SQL, `similar(...)`, metadata filtering, graph traversal, or object retrieval, route to `embeddings-search` first.
- If a prompt names `CONFIG=app.yml`, `uvicorn`, `/v1/chat/completions`, `/mcp`, `TOKEN`, Docker, cloud, or console commands, route to `api-and-deployment`.

## Validation Helpers

- `python scripts/check_txtai_environment.py` checks core imports, package version, optional modules, and top-level constructor signatures.
- `python sub-skills/embeddings-search/scripts/semantic_search_smoke.py --run --sql` runs a no-download embeddings smoke check with external vectors.
- `python sub-skills/pipelines-and-workflows/scripts/workflow_smoke.py --mode all` runs no-download deterministic workflow checks.
- `python sub-skills/agents-and-llm-orchestration/scripts/rag_config_template.py --check` validates generated RAG template placeholders without calling a model.
- `python sub-skills/api-and-deployment/scripts/api_config_template.py --list` lists safe API config templates without starting a server.

## Self-Containment Rules

- Do not tell future users to open txtai source docs, examples, tests, Docker files, or notebooks from a checkout. Runtime guidance must come from this skill tree.
- If a task needs a reusable helper, use the bundled scripts above or create user project files from the references.
- Keep credentials, tokens, model cache paths, API keys, and local environment paths out of generated configs and answers.
- Treat model downloads, web tools, cloud APIs, GPU acceleration, audio/image system dependencies, and server startup as explicit user-environment decisions.
