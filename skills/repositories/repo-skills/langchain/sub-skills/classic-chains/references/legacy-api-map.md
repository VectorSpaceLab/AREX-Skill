# Legacy API Map

## Package Position

`langchain-classic` contains legacy chains, `langchain-community` re-exports, indexing APIs, and deprecated functionality. In most new work, users should prefer the current `langchain` package and shared `langchain-core` primitives. Treat this sub-skill as a maintenance and migration guide for existing classic applications.

Known package facts sampled for this skill:

- Distribution name: `langchain-classic`.
- Import package: `langchain_classic`.
- Sampled version: `1.0.8`.
- Python range: `>=3.10.0,<4.0.0`.
- Core dependencies include `langchain-core`, `langchain-text-splitters`, `langsmith`, `pydantic`, `SQLAlchemy`, `requests`, and `PyYAML`.
- Optional extras route provider/community integrations through packages such as `langchain-community`, `langchain-openai`, `langchain-anthropic`, and other partner packages.

## Classic-Owned Areas

| Area | Common modules | Maintenance focus |
| --- | --- | --- |
| Chains | `langchain_classic.chains`, `chains.base`, `chains.llm`, `chains.conversational_retrieval`, `chains.retrieval`, `chains.combine_documents`, `chains.router`, `chains.qa_with_sources`, `chains.summarize`, `chains.sequential` | Preserve `Chain` inputs/outputs, callback propagation, sync/async parity, serialization-compatible fields, and deprecation behavior. |
| Classic agents | `langchain_classic.agents`, `agents.initialize`, MRKL, ReAct, structured chat, XML, OpenAI functions/tools formatters and output parsers | Maintain legacy agent executors, output parsers, scratchpad formatting, and import compatibility. Route new v1 agent creation to `../agents-and-middleware/SKILL.md`. |
| Retrievers | `langchain_classic.retrievers`, `multi_vector`, `parent_document_retriever`, `multi_query`, `contextual_compression`, `self_query`, `ensemble`, `time_weighted_retriever` | Preserve `BaseRetriever` contracts, returned `Document` lists, vectorstore/docstore interactions, and optional dependency boundaries. |
| Document loading and transformation | `langchain_classic.document_loaders`, `document_loaders.blob_loaders`, `document_loaders.parsers`, `document_transformers`, `text_splitter.py` | Maintain imports and parsing behavior; many concrete integrations require optional packages or community/provider packages. For splitter primitives, check sibling `../core-primitives/SKILL.md` if ownership is shared. |
| Memory | `langchain_classic.memory`, `base_memory`, chat message histories, buffer/window/summary/token/vectorstore memories | Preserve `memory_key`, `input_key`, `output_key`, `return_messages`, `load_memory_variables`, `save_context`, and async variants. Many memory classes are deprecated in favor of v1 agent checkpointing/store APIs. |
| Indexes | `langchain_classic.indexes` | Maintain legacy indexing helper compatibility and avoid adding new index abstractions. |
| Evaluation | `langchain_classic.evaluation`, criteria, comparison, exact/regex/string distance, QA, scoring, parsing, agents | Preserve evaluator construction and deterministic unit behavior; skip LLM/provider calls unless explicitly configured. |
| Callbacks | `langchain_classic.callbacks`, tracers, streamlit callbacks | Maintain legacy import compatibility and callback handler behavior. Shared callback primitives generally belong to `../core-primitives/SKILL.md`. |
| Schema compatibility | `langchain_classic.schema` | Maintain compatibility re-exports and old import paths; most underlying primitives are from `langchain_core`. |

## Dynamic Community Re-exports

Several classic modules use dynamic import helpers to keep old import paths working while forwarding symbols to `langchain_community`. Examples include retrievers such as `PubMedRetriever`, `WeaviateHybridSearchRetriever`, `ZillizRetriever`, `OutlineRetriever`, `RemoteLangChainRetriever`, and many entries in `langchain_classic.retrievers.__init__`.

When editing one of these surfaces:

1. Identify whether the symbol is implemented locally or appears in a `DEPRECATED_LOOKUP` mapping.
2. If it is re-exported, fix routing/deprecation/import messaging in classic only when the legacy path is broken; implementation changes usually belong in the community or provider package.
3. Keep the warning and missing-dependency message actionable: name the modern package or module the user must install/import.
4. Add import-level tests when practical; avoid provider/network execution for a pure import compatibility fix.

## Chain Key Contracts

Classic chains expose `input_keys` and `output_keys`; many bugs come from mismatched names between prompt variables, memory variables, and downstream combine chains.

Important examples:

- `ConversationalRetrievalChain` expects inputs `question` and `chat_history`, outputs `answer` by default, optionally adds `source_documents` and `generated_question`, and calls the combine-documents chain with `input_documents` plus the current input mapping.
- Conversation chains and memory classes coordinate `memory_key`, `input_key`, `output_key`, prompt variables, and saved context.
- Combine-document chains commonly require `input_documents` and any prompt-specific variables such as `question`.
- Sequential chains must avoid overlapping input, output, and memory keys unless tests explicitly cover the legacy behavior.

## Sibling Routing

- New v1 `create_agent`, middleware, checkpointing, and store-backed agent memory belong in `../agents-and-middleware/SKILL.md`.
- Shared `langchain_core` objects such as `Document`, messages, prompt templates, `BaseRetriever`, runnables, callback manager interfaces, vector store base classes, and output parser base classes belong in `../core-primitives/SKILL.md`.
- Provider packages and community integrations should be handled by their owning integration skill when available. Classic should only preserve legacy import paths and compatibility behavior.
