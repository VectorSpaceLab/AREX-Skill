---
name: integrations-and-storage
description: "Choose and verify LlamaIndex integration packages, namespace
  imports, storage/vector-store/readers/LLM/embed providers, and optional
  dependency or service boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Integrations and Storage

Use this sub-skill when a task is blocked on selecting, installing, importing, or troubleshooting a LlamaIndex provider package or storage backend.

## Route Here For

- Deciding between the `llama-index` starter package and `llama-index-core` plus specific integration packages.
- Mapping a distribution such as `llama-index-llms-openai` or `llama-index-vector-stores-qdrant` to imports such as `llama_index.llms.openai` or `llama_index.vector_stores.qdrant`.
- Choosing categories of integrations: LLMs, embeddings, vector stores, readers, tools, postprocessors, callbacks, storage/docstores/index stores, or `llama-index-utils` helpers.
- Determining whether a storage choice is local/in-memory, local persistent, remote filesystem-backed, self-hosted service-backed, or cloud service-backed.
- Diagnosing missing optional packages, provider credentials, service/network availability, import namespace mismatches, and plugin/core version compatibility.

## Do Not Use For

- End-to-end RAG code after the provider/storage choice is made; use `../indexing-and-querying/SKILL.md`.
- File loading, parsing, chunking, `SimpleDirectoryReader`, `SentenceSplitter`, or `IngestionPipeline`; use `../ingestion-and-loading/SKILL.md`.
- Prompt templates, structured outputs, Pydantic output models, and provider-specific generation parameters; use `../customization-and-structured-outputs/SKILL.md`.
- Agent/workflow composition with tools and memory; use `../agents-and-workflows/SKILL.md`.

## Fast Triage

1. Identify the requested capability and category: LLM, embedding, vector store, reader, tool, utility, or core storage.
2. If the code imports `llama_index.core...`, check `llama-index-core`; if it imports `llama_index.<category>.<provider>`, check the matching integration distribution.
3. Prefer installing one narrow package such as `llama-index-llms-ollama`, `llama-index-embeddings-huggingface`, or `llama-index-vector-stores-qdrant` instead of broad optional extras.
4. Verify import and distribution metadata before changing code:

```bash
python sub-skills/integrations-and-storage/scripts/check_integration_imports.py \
  --dist llama-index-core \
  --module llama_index.core \
  --dist llama-index-llms-openai \
  --module llama_index.llms.openai
```

5. Separate local persistence from backend persistence: `StorageContext.persist(persist_dir=...)` applies to core/simple stores, while many vector-store integrations persist in their own database or cloud service.
6. If a provider call fails after import succeeds, inspect credentials, endpoint/base URL, region, local service process, collection/index existence, and network policy before blaming LlamaIndex APIs.

## Required References

- `references/package-selection.md`: package split, namespace rules, category-to-distribution naming, and how to verify imports.
- `references/storage-and-provider-patterns.md`: storage decision tree, vector-store persistence assumptions, and provider wiring patterns.
- `references/troubleshooting.md`: install/import, credential, service, persistence, and compatibility failure modes.

## Bundled Helper

`check_integration_imports.py` is a safe offline checker for importability and installed distribution metadata. It does not call provider APIs, open network connections, or require credentials; it only imports requested modules and reads package metadata.
