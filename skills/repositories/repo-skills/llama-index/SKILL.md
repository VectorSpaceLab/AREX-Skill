---
name: llama-index
description: "Build, customize, troubleshoot, and maintain LlamaIndex Python
  applications and the LlamaIndex monorepo. Routes ingestion, indexing/querying,
  agents/workflows, structured outputs, integrations/storage, and
  repo-maintenance tasks to focused sub-skills."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LlamaIndex

Use this repo skill when a task involves LlamaIndex Python (`llama-index`, `llama-index-core`, or `llama_index.*`) application development, integration selection, RAG pipeline construction, agent workflows, structured outputs, or safe monorepo maintenance.

## Quick Install Decision

- Use `pip install llama-index` for the starter package when the user wants the default core + common OpenAI stack.
- Use `pip install llama-index-core` plus selected integration packages when the user wants a minimal or non-OpenAI install.
- Core imports use `llama_index.core.*`; integration imports usually use `llama_index.<category>.<provider>` after installing a matching `llama-index-<category>-<provider>` distribution.
- Verify a local environment with `python scripts/llama_index_core_smoke.py` or inspect installed packages with `python scripts/inspect_llama_index_install.py --json`.

## Route By Task

- **Data loading and ingestion**: use `sub-skills/ingestion-and-loading/SKILL.md` for `SimpleDirectoryReader`, `Document`, node parsers, `IngestionPipeline`, metadata, cache/docstore, and file parsing failures.
- **RAG indexing and querying**: use `sub-skills/indexing-and-querying/SKILL.md` for `VectorStoreIndex`, retrievers, query engines, response synthesizers, persistence, routing, fusion, and empty retrieval debugging.
- **Agents and workflows**: use `sub-skills/agents-and-workflows/SKILL.md` for `FunctionAgent`, `ReActAgent`, `AgentWorkflow`, tools, memory, chat engines, handoff, streaming, and agent orchestration.
- **Customization and structured outputs**: use `sub-skills/customization-and-structured-outputs/SKILL.md` for `Settings`, prompts, callbacks, instrumentation, output parsers, Pydantic schemas, evaluation, and test isolation.
- **Integrations and storage**: use `sub-skills/integrations-and-storage/SKILL.md` for provider package selection, import-path mismatches, vector stores, readers, LLM/embedding providers, credentials, and service-backed persistence.
- **Repo maintenance**: use `sub-skills/repo-maintenance/SKILL.md` only for work inside the LlamaIndex monorepo: package layout, `llama-dev`, targeted tests, package metadata, and safe docs/examples automation.

## Common Starting Patterns

For a tiny local RAG pipeline:

```python
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.llms import MockLLM
from llama_index.core import Settings

Settings.llm = MockLLM()
Settings.embed_model = MockEmbedding(embed_dim=8)
index = VectorStoreIndex.from_documents([Document(text="LlamaIndex connects data to LLM apps.")])
query_engine = index.as_query_engine()
print(query_engine.query("What does LlamaIndex connect?"))
```

For real provider-backed usage, set an LLM and embedding model from installed integration packages before creating indexes or agents. If imports fail, route to integrations/storage before changing RAG logic.

## Shared References and Scripts

- Read `references/package-map.md` for package naming, namespace conventions, and how this monorepo splits core from integrations.
- Read `references/troubleshooting.md` for cross-cutting install/import/provider/API-key/deprecation failures before diving into a narrower sub-skill.
- Read `references/repo-provenance.md` when deciding whether this skill is stale relative to a LlamaIndex checkout.
- Run `scripts/inspect_llama_index_install.py` to inspect installed LlamaIndex distributions and import roots without network calls.
- Run `scripts/llama_index_core_smoke.py` for a tiny core import and mock RAG smoke check.

## Boundary Rules

- Do not solve provider import failures by editing core RAG code; first verify the installed `llama-index-*` distribution and import path.
- Do not assume `ServiceContext` for new code; prefer `Settings` and route migration issues to customization.
- Do not run release, publishing, version-bump, credentialed docs sync, or broad integration test commands unless the user explicitly asks and understands the side effects.
- Do not make runtime guidance depend on a source checkout. Copy or adapt reusable checks into this skill’s `scripts/` tree and keep source repo examples/tests as evidence only.
