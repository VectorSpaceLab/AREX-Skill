---
name: retrieval-doc-chat
description: "Document ingestion, parsing, chunking, embeddings, vector stores,
  retrieval, citations, URL crawling, and Lance RAG workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Retrieval Doc Chat

Use this sub-skill for document-centered retrieval work in Langroid.
It covers loading files and URLs, parsing and chunking, retrieval tuning,
vector-store selection, citations, and Lance RAG query planning.

## Use when

- answering questions from PDFs, DOCX, Markdown, text, spreadsheets, slides, URLs, or raw bytes
- configuring `DocChatAgentConfig` or `DocChatAgent`
- choosing parsing libraries, chunking settings, or embeddings
- comparing vector-store backends for retrieval or persistence
- debugging empty retrieval, parser extras, cleanup, or `full_eval` risk
- setting up Lance RAG query planning with filters and dataframe calculations

## Covered surface

- `DocChatAgentConfig`, `DocChatAgent`
- parsing configs, loaders, and chunking
- embeddings and vector-store configs
- BM25, fuzzy search, reranking, and enrichment
- citations and file attachments
- URL crawling and retrieval-only flows
- `LanceDocChatAgent` and `LanceRAGTaskCreator`

## Boundaries

- Provider and model configuration: [`../llm-provider-config/SKILL.md`](../llm-provider-config/SKILL.md)
- Generic agent, task, and tool mechanics: [`../agents-tasks-tools/SKILL.md`](../agents-tasks-tools/SKILL.md)
- SQL, table, and graph workflows: [`../data-sql-graph-agents/SKILL.md`](../data-sql-graph-agents/SKILL.md)

## Runtime entry points

- [`references/api-reference.md`](references/api-reference.md)
- [`references/doc-chat-workflows.md`](references/doc-chat-workflows.md)
- [`references/parsing-and-data-formats.md`](references/parsing-and-data-formats.md)
- [`references/vector-stores-and-embeddings.md`](references/vector-stores-and-embeddings.md)
- [`references/troubleshooting.md`](references/troubleshooting.md)
- [`scripts/rag_config_smoke.py`](scripts/rag_config_smoke.py)
