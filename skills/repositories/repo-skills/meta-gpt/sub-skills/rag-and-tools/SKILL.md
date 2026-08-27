---
name: rag-and-tools
description: "Use MetaGPT RAG pipelines, retrievers, document stores,
  search/browser/data tools, and tool registry diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MetaGPT RAG and Tools

Use this sub-skill when a request involves MetaGPT retrieval-augmented generation, vector/document stores, retriever/ranker selection, search or browser engines, data/editor/tool libraries, tool registration, tool recommendation, or safe optional-dependency diagnosis.

## Route Here For

- Building a MetaGPT RAG pipeline from documents or objects with `metagpt.rag.engines.SimpleEngine`.
- Choosing or debugging retrievers, rankers, vector stores, persisted indexes, and document-store wrappers.
- Using web/search/browser/editor/data tools from `metagpt.tools` and `metagpt.tools.libs`.
- Registering custom tools with `ToolRegistry`, selecting registered tools by name/tag/path, or using tool recommenders.
- Diagnosing missing optional packages for `[rag]`, search providers, browser engines, vector stores, and tool recommendation.

## Route Elsewhere

- Data Interpreter orchestration, plans, and DI execution loops: use the `data-interpreter` sub-skill; return here only for tool prerequisites or tool-specific failures.
- Core software-company CLI, `Role`/`Action` basics, and multi-role project workflows: use `software-company`.
- Extension optimizers, Android/browser environments, and environment integrations outside RAG/tools: use `extensions-and-environments`.
- Maintainer serialization, memory, experience pools, and internal persistence APIs: use `maintainer-apis`.
- Installation/config basics before optional services or API keys exist: use the root MetaGPT installation/config guidance, then return here.

## Reference Map

- `references/workflows.md`: RAG construction, indexing, querying, retriever/ranker choices, search/browser usage, and tool registration recipes.
- `references/api-reference.md`: key modules, classes, config schemas, factories, and registry/recommender concepts.
- `references/dependencies.md`: optional extras, package groups, service/key/browser prerequisites, and missing-dependency symptoms.
- `references/troubleshooting.md`: vector-store, embedding/LLM, search, browser, data schema, and tool-safety failure handling.
- `scripts/rag_import_check.py`: safe import/spec diagnostic helper for selected RAG/tool modules and optional dependencies.

## Quick Start

1. Read `references/dependencies.md` first if base MetaGPT is installed without `metagpt[rag]`, search extras, browser extras, or vector-store clients.
2. Use `scripts/rag_import_check.py --group rag` or `--group tools` to identify missing optional packages before writing code that imports deep RAG/tool modules.
3. Use `references/workflows.md` for minimal recipes; avoid running network search, browser automation, external vector DBs, or long LLM/reranker calls unless the user confirms prerequisites and safety.
