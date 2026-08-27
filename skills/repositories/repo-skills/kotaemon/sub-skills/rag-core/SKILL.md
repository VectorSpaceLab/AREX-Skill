---
name: rag-core
description: "Build and troubleshoot programmatic Kotaemon RAG pipelines with
  core components, documents, indexes, retrieval, reranking, QA, reasoning, and
  citations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Kotaemon RAG Core

Use this sub-skill when an agent needs to compose or debug Kotaemon's programmatic RAG layer: component graphs, document schemas, vector indexing/retrieval, reranking, evidence formatting, prompt templates, reasoning chains, QA output metadata, and citation traces.

Route elsewhere when the task is primarily:

- App setup, `.env`, `flowsettings.py`, Gradio login, Docker, PDF.js, or migration operations: use `app-deployment`.
- Model credentials, provider endpoints, local LLM servers, embedding model setup, reranker provider setup, or GraphRAG provider toggles: use `model-providers`.
- Loading/parsing/splitting source files, OCR, table extraction, or parser optional dependencies: use `document-ingestion`.
- ktem app extensions, custom pages, flow registration, templates, or plugin UI work: use `extensions`.

## Start Here

1. Identify the layer: schema/component contract, indexing, retrieval, reranking, QA/citation, prompt/reasoning, or storage abstraction.
2. Use `references/api-reference.md` for class contracts and import paths.
3. Use `references/rag-workflows.md` for composition patterns and metadata-preserving examples.
4. Use `references/troubleshooting.md` for common failure modes before changing provider or ingestion code.
5. Run `scripts/inspect_pipeline_components.py --repo-root <repo>` when source or environment drift is suspected.

## Core Mental Model

- `BaseComponent` is the composable unit. Implement `run(...)`; call components directly with `component(...)` for normal execution. `invoke`, `stream`, and async variants exist for components that implement them, but `run` is the common subclass contract.
- `Document` carries `content`, `text`, `metadata`, optional `source`, and optional `channel`. `RetrievedDocument` extends it with `score` and `retrieval_metadata`.
- `VectorIndexing` embeds documents, writes vectors to a `BaseVectorStore`, and optionally stores full `Document` objects in a `BaseDocumentStore`.
- `VectorRetrieval` embeds the query, fetches ids/scores from the vector store, loads documents from the docstore, returns `RetrievedDocument` objects, and can apply rerankers.
- QA flows convert retrieved documents to evidence text, generate answers, and attach metadata such as `citation`, `qa_score`, `mindmap`, and `citation_viz`.

## Difficult Cases

- Low-confidence cited answer: trace `RetrievedDocument.score`, `retrieval_metadata`, reranker output, `qa_score`, and citation spans through `references/rag-workflows.md`; route provider scoring failures to `../model-providers/SKILL.md` and parser evidence gaps to `../document-ingestion/SKILL.md`.
- Custom component pipeline loses metadata: check the `BaseComponent.run(...)` boundary, preserve `Document.metadata` when transforming chunks, and use `scripts/inspect_pipeline_components.py` to confirm the expected schema/index classes are present.

## Bundled References

- `references/api-reference.md` - core classes, import paths, method contracts, and metadata expectations.
- `references/rag-workflows.md` - indexing/retrieval/QA wiring patterns, prompt and reasoning usage, and safe introspection.
- `references/troubleshooting.md` - provider object, embedding/vectorstore mismatch, empty retrieval, metadata loss, citation confidence, prompt variables, missing reranker, and call-style failures.

## Bundled Script

```bash
python skills/kotaemon/sub-skills/rag-core/scripts/inspect_pipeline_components.py --repo-root <repo-root>
```

The inspector attempts import-light discovery for key Kotaemon modules, then falls back to AST parsing if imports fail because optional provider dependencies are absent. It reports public classes/functions, base classes, method names, signatures when available, and the discovery mode used per module.
