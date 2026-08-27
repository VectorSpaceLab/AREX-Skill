---
name: kotaemon
description: "Use Kotaemon to build, deploy, configure, extend, and troubleshoot
  document QA, RAG, model-provider, ingestion, and Gradio app workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Kotaemon

Use this repo skill when a task involves Kotaemon, ktem, document QA, RAG app deployment, document ingestion, model provider setup, GraphRAG, local-model configuration, custom Kotaemon components, or ktem app/index extensions.

Kotaemon is a Python workspace with:

- `kotaemon` - core composable RAG library for components, documents, loaders, embeddings, LLMs, indexes, retrieval, ranking, reasoning, and QA.
- `ktem` - Gradio document-QA application with Resources, File Index, Chat, Settings, extension, MCP, and persistence layers.
- root app entry points and deployment scripts for the user-facing document QA web UI.

## Start Here

1. For install or launch questions, first read `references/package-overview.md`, then route to `sub-skills/app-deployment/SKILL.md`.
2. For code/API work, identify whether the task is ingestion, RAG pipeline composition, provider setup, or extension development and open the matching sub-skill.
3. Run `scripts/check_install.py` for a safe local diagnostic when a checkout or environment may be incomplete. It checks metadata/imports and optional package signals without starting the app or calling providers.
4. Read `references/troubleshooting.md` for cross-cutting dependency, optional integration, credential, and configuration failures before changing code.
5. Read `references/repo-provenance.md` before deciding whether this skill is stale for a current checkout.

## Route By Task

| Task signal | Read |
| --- | --- |
| Docker/local install, `uv sync`, `python app.py`, Gradio launch, `.env`, `flowsettings.py`, app data, login, PDF.js, update scripts, Chroma migration | `sub-skills/app-deployment/SKILL.md` |
| File upload ingestion, PDF/DOCX/HTML/XLSX/TXT/web readers, OCR/table parsing, splitters, document metadata validation | `sub-skills/document-ingestion/SKILL.md` |
| Programmatic RAG, `BaseComponent`, `Document`, vector indexing/retrieval, reranking, QA/citations, prompt templates, reasoning chains | `sub-skills/rag-core/SKILL.md` |
| OpenAI/Azure/Ollama/GGUF/local servers, embeddings, rerankers, web search, provider env keys, GraphRAG/NanoGraphRAG/LightRAG | `sub-skills/model-providers/SKILL.md` |
| Custom components, reasoning modes, file-index/retriever classes, pages/settings, pluggy extensions, project templates | `sub-skills/extensions/SKILL.md` |

## Installation Context

- End users should prefer the documented Docker images or the repo's `uv sync --python 3.10` path when using a checkout.
- Manual developer setup commonly installs `libs/kotaemon` and `libs/ktem` editable in the same environment.
- The project has broad runtime dependencies: Gradio, LangChain provider integrations, LlamaIndex, ChromaDB/LanceDB, document parsers, provider SDKs, and optional local-model/GraphRAG packages. Install the smallest set needed for the selected workflow.
- Many integrations require external services, credentials, model downloads, or optional binaries. The bundled diagnostics are offline by default and should not be treated as provider connectivity tests.

## Safe Diagnostics

```bash
python skills/kotaemon/scripts/check_install.py --repo-root <repo-root>
```

The root diagnostic reports Python version, discovered distributions, top-level import status, console script metadata, and whether common optional packages are installed. It does not run `python app.py`, start Gradio, call LLM APIs, download assets, or mutate data.

## Runtime Boundaries

- This skill is self-contained for agent guidance; do not require future agents to open the original repo docs or scripts to use it.
- Bundled scripts are safe diagnostics or static validators. They intentionally avoid app startup, provider calls, model downloads, database migrations, and destructive writes.
- For repository development tasks, use this skill to choose focused evidence and tests, but verify against the current checkout before editing because public APIs and optional dependencies may drift.

## References

- `references/package-overview.md` - workspace package map, install variants, entry points, and dependency surfaces.
- `references/troubleshooting.md` - cross-cutting install/import/config/provider/app failures and routing guidance.
- `references/repo-provenance.md` - source snapshot and refresh baseline.
- `references/repo-routing-metadata.json` - structured metadata consumed by the managed repo-skills router during import.
