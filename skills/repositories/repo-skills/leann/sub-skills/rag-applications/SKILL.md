---
name: rag-applications
description: "Compose and validate LEANN RAG workflows for documents, code,
  personal or live data, semantic file search, images, and visual PDFs without
  exposing private data or triggering heavy setup."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LEANN RAG Applications

Use this sub-skill to turn a source into LEANN passages, preserve useful
metadata, build a searchable index, and choose retrieval or chat. Start with a
small bounded sample and keep private, live, and multimodal sources opt-in.

## Route by source

- For PDF/TXT/Markdown documents, code repositories, or mixed code and prose,
  use [document and code RAG](references/document-and-code-rag.md).
- For browser history, Apple Mail, Apple Calendar, iMessage, existing WeChat
  exports, Slack, or Twitter/X, use
  [personal and live data](references/personal-and-live-data.md).
- For CLIP image retrieval or ColQwen2/ColPali visual-PDF retrieval, use
  [multimodal RAG](references/multimodal-rag.md).
- For chunk sizes, Abstract Syntax Tree (AST) fallback, file layout, ignore
  rules, metadata schemas, filters, or temporal search, use
  [chunking, metadata, and layout](references/chunking-metadata-and-layout.md).
- For parser, permission, export, Model Context Protocol (MCP), PDF, image,
  dependency, or empty-corpus failures, use
  [troubleshooting](references/troubleshooting.md).
- To produce a validated public `leann` command without executing it, use the
  bundled [command planner](scripts/build_rag_command.py).

## Operating sequence

1. Classify the source as local public files, private local data, live MCP data,
   image data, or vision-PDF data. State platform, permissions, export format,
   dependency, model-cache, and compute prerequisites before access.
2. Define a passage contract: non-empty `text` plus a flat `metadata` mapping.
   Select stable source identifiers and use one field name and type per concept.
3. Load a bounded sample. Exclude hidden, ignored, generated, oversized, empty,
   corrupt, or unsupported inputs before chunking.
4. Chunk prose traditionally; use AST-aware chunking only for supported code.
   Keep the deterministic traditional fallback enabled.
5. Validate counts and inspect representative passage text and metadata. Stop if
   zero passages, required source identity is missing, or chunk metadata no
   longer matches its text.
6. Build, then search with a query whose expected source is known. Add metadata
   or time filters only after verifying those fields exist in stored passages.
7. Add chat only after retrieval is sound. Provider, credential, and model
   selection belongs to the provider sub-skill.

## Safety rules

- Never export private platform data, open private databases, start an MCP
  server, read credentials, install system packages, or download models merely
  to plan a workflow.
- Never print secrets or include them in generated commands. Pass credentials
  through the provider or server's documented environment only when the user
  separately authorizes execution.
- Treat Slack and Twitter/X readers, Spotlight collection, image encoders, and
  visual-PDF models as reference-only here. Preflight them; do not run them.
- Treat an existing WeChat export as input. Do not invoke an exporter or attempt
  to modify a running client.
- Do not force rebuilds or include hidden files by default. Preserve the source
  corpus and write indexes to a separate destination.

## Boundaries

- Backend choice, graph/search parameters, compact storage, recomputation, and
  index updates: [backends and storage](../backends-and-storage/SKILL.md).
- Embedding modes, model caches, API credentials, prompt templates, and LLM/chat
  providers: [embeddings and chat](../embeddings-and-chat/SKILL.md).
- MCP protocol details, server installation, transport, and deployment:
  [MCP and services](../mcp-and-services/SKILL.md).
- General Python builder/searcher lifecycle and custom precomputed-vector code:
  [API and indexing](../api-and-indexing/SKILL.md).
