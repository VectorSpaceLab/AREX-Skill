---
name: memory-knowledge-and-rag
description: "Guides agents using CrewAI memory, knowledge sources, RAG clients
  and loaders, embedding providers, vector stores, reset-memory commands, and
  optional retrieval dependencies."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Memory, Knowledge, and RAG

Use this sub-skill when work involves CrewAI `Memory`, `Knowledge`, `knowledge_sources`, memory scopes/slices, RAG vector clients, `RagTool`, official RAG loaders, embedding providers, ChromaDB/Qdrant/LanceDB storage, or `crewai reset-memories` behavior.

## Route First

- For memory construction, recall depth, scopes, slices, crew/agent memory behavior, and reset commands, read [references/memory-and-knowledge.md](references/memory-and-knowledge.md).
- For `Knowledge`, `knowledge_sources`, crew-level vs agent-level knowledge, source classes, storage collections, and score thresholds, read [references/memory-and-knowledge.md](references/memory-and-knowledge.md).
- For direct RAG clients, `RagTool`, data type detection, official loaders, and network/file loader boundaries, read [references/rag-loaders.md](references/rag-loaders.md).
- For embedding provider specs, vector DB configuration, LanceDB/ChromaDB/Qdrant storage defaults, optional dependencies, and dimension-mismatch prevention, read [references/embedding-and-storage.md](references/embedding-and-storage.md).
- For common failures and fixes, including embedder dimension mismatch, missing optional dependencies, storage path confusion, reset target confusion, unsupported file types, and credential-bound loaders, read [references/troubleshooting.md](references/troubleshooting.md).
- To safely check installed memory, knowledge, RAG, and optional loader imports without LLMs, credentials, network, or destructive operations, run [scripts/check_rag_imports.py](scripts/check_rag_imports.py) with `--help` first.

## Boundaries

- Stay here for retrieval architecture: `Memory`, `Knowledge`, `RagTool`, RAG clients, vector stores, embedders, loaders, reset commands, and optional retrieval dependencies.
- Use [../files-and-multimodal/SKILL.md](../files-and-multimodal/SKILL.md) for low-level file input resolution, MIME/provider constraints, multimodal task files, and non-RAG file processing.
- Use [../tools-and-mcp/SKILL.md](../tools-and-mcp/SKILL.md) for general tool wrappers, custom `BaseTool` design, MCP, and non-RAG `crewai_tools` exports.
- Use [../llm-and-providers/SKILL.md](../llm-and-providers/SKILL.md) for LLM provider credentials, model IDs, base URLs, streaming, and chat/completion auth.
- Use [../core-runtime/SKILL.md](../core-runtime/SKILL.md) for `Agent`, `Task`, `Crew`, kickoff, process, guardrail, callback, and output design that happens around retrieval.
- Return to [../../SKILL.md](../../SKILL.md) when a request spans multiple CrewAI capability areas and needs root routing context.

## Safe Defaults

- Prefer local `StringKnowledgeSource`, `TextFileKnowledgeSource`, JSON/CSV sources, or local `RagTool.add(path=...)` when the user has not approved network retrieval.
- Do not instantiate loaders that fetch web pages, GitHub repositories, YouTube transcripts, or databases unless the user authorizes network/database access and provides credentials if needed.
- Keep embedding provider secrets in runtime environment or user config; never put real API keys, tokens, database URIs, or full local storage paths in generated content.
- Use one embedding model per existing collection. If the embedder changes, reset or rebuild the relevant memory/knowledge/RAG collection rather than mixing vector dimensions.

## Usability Targets

- Diagnose a dimension mismatch after changing embedding providers and choose the smallest safe reset/rebuild target.
- Build a knowledge-enabled crew with local document loaders while avoiding accidental network retrieval.
