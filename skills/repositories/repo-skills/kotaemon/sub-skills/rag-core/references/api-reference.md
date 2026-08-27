# Kotaemon RAG Core API Reference

This reference covers the programmatic RAG layer in the `kotaemon` package: schemas, components, indexing/retrieval, storage contracts, QA/citation components, prompt templates, and reasoning helpers. It intentionally avoids app UI operation, provider credential setup, and parser-specific ingestion details.

## Import Map

| Need | Primary imports | Notes |
| --- | --- | --- |
| Document and message schemas | `from kotaemon.base import Document, RetrievedDocument, DocumentWithEmbedding, HumanMessage, AIMessage, SystemMessage, LLMInterface` | `Document` wraps LlamaIndex document behavior and adds Kotaemon fields. |
| Component contract | `from kotaemon.base import BaseComponent, Node, Param, lazy` | Subclass `BaseComponent` and implement `run(...)`. |
| Index/retrieval | `from kotaemon.indices import VectorIndexing, VectorRetrieval` | `TextVectorQA` is available from `kotaemon.indices.vectorindex`. |
| Storage contracts | `from kotaemon.storages import BaseDocumentStore, BaseVectorStore, InMemoryDocumentStore, InMemoryVectorStore` | Concrete stores include Chroma, LanceDB, Milvus, Qdrant, simple-file, and in-memory variants. |
| Embedding contract | `from kotaemon.embeddings import BaseEmbeddings` | Concrete embedding classes live in provider-specific modules; route credential setup to `model-providers`. |
| LLM contract | `from kotaemon.llms import BaseLLM, PromptTemplate, BasePromptComponent` | Concrete chat/completion classes are provider-specific. |
| QA and citations | `from kotaemon.indices.qa.citation import CitationPipeline`; `from kotaemon.indices.qa.citation_qa import AnswerWithContextPipeline`; `from kotaemon.indices.qa.format_context import PrepareEvidencePipeline` | Some QA classes import `ktem` or optional renderer dependencies; use direct imports knowingly. |
| Reranking | `from kotaemon.indices.rankings import BaseReranking, LLMReranking` | Provider-backed rerankers require model setup. |
| Reasoning helpers | `from kotaemon.llms.cot import Thought, ManualSequentialChainOfThought`; `from kotaemon.llms.linear import SimpleLinearPipeline, GatedLinearPipeline`; `from kotaemon.llms.branching import SimpleBranchingPipeline, GatedBranchingPipeline` | Reasoning helpers still need explicit LLM objects when they call models. |

## Schema Classes

### `Document`

`Document` accepts `content`, `text`, and standard LlamaIndex document kwargs. Kotaemon uses it as the common payload for component IO.

Important fields:

- `content`: raw object carried by the document. When constructed with a positional value, this is that value.
- `text`: string representation used by retrieval, prompts, evidence formatting, and citations.
- `metadata`: dict for source, page, parser, retrieval, UI, and QA metadata.
- `source`: optional source identifier.
- `channel`: optional display channel: `chat`, `info`, `index`, `debug`, or `plot`.
- `doc_id` / `id_`: inherited identifier used to align docstore records with vectorstore ids.

Constructor behavior to remember:

- `Document("hello")` sets `content="hello"` and `text="hello"`.
- `Document(text="hello", metadata={...})` keeps `text` as the content source.
- `Document(existing_doc, metadata={...})` copies the existing document and overlays kwargs.
- A falsey positional value such as `None` or `""` creates an empty `text`; `bool(document)` follows `bool(content)`.

### `DocumentWithEmbedding`

`DocumentWithEmbedding(embedding=[...], metadata={...})` is a `Document` with an embedding vector. `BaseVectorStore.add(...)` can accept either raw `list[list[float]]` embeddings or `list[DocumentWithEmbedding]`.

### Messages and LLM outputs

- `SystemMessage`, `HumanMessage`, and `AIMessage` are `BaseMessage` subclasses and expose `to_openai_format()` with roles `system`, `user`, and `assistant`.
- `LLMInterface` extends `AIMessage` with `candidates`, token counts, `total_cost`, `logits`, nested `messages`, and `logprobs`.
- `StructuredOutputLLMInterface` adds `parsed` and `refusal`.

### `RetrievedDocument`

`RetrievedDocument` extends `Document` with:

- `score: float = 0.0` - vectorstore or retrieval score.
- `retrieval_metadata: dict = {}` - scratchpad for retrieval-stage details.

Common metadata keys used by RAG and QA flows:

- Source display: `file_name`, `page_label`, `section`, `source`.
- Evidence type: `type` with values like `table`, `chatbot`, `image`, or `thumbnail`.
- Evidence body alternates: `window`, `table_origin`, `image_origin`.
- Thumbnail linking: `thumbnail_doc_id`.
- Reranker/QA scores: `llm_reranking_score`, `llm_trulens_score`, `qa_score`.

Keep user-facing provenance in `metadata`; keep transient retrieval-stage details in `retrieval_metadata`.

## Component Contract

`BaseComponent` is the core composable abstraction. Subclasses should implement `run(...)`; normal callers should execute components with `component(...)`, not by calling `run(...)` directly unless they deliberately bypass component middleware.

Key behavior:

- `run(...)` is the abstract subclass contract.
- `component(...)` invokes the component through TheFlow's callable path.
- `invoke(...)`, `ainvoke(...)`, `stream(...)`, and `astream(...)` are optional; many base classes declare them but do not implement useful behavior.
- `flow()` requires `component.inflow` to be another `BaseComponent`, then calls this component on the upstream flow result.
- `set_output_queue(queue)` propagates an output queue into child components stored as flow nodes.
- `report_output(output)` pushes optional `Document` progress into that queue.

Practical rule: when debugging a custom component, check whether the component implements `run`, `invoke`, or `stream` and then call the method that actually has behavior. For most Kotaemon components, `component(...)` is safest.

## Indexing and Retrieval

### Base classes

- `BaseIndexing` defines `to_retrieval_pipeline(...)` and `to_qa_pipeline(...)` extension points.
- `BaseRetrieval.run(...)` returns `list[RetrievedDocument]`.
- `DocTransformer.run(documents: list[Document]) -> list[Document]` is the base for splitter/transformer components.

### `VectorIndexing`

`VectorIndexing(vector_store=..., embedding=..., doc_store=...)` accepts `str`, `list[str]`, `Document`, or `list[Document]`.

Pipeline behavior:

1. Converts strings to `Document(text=..., id_=uuid)`.
2. Calls `embedding(docs)`.
3. Writes vectors to `vector_store.add(..., ids=[doc.doc_id for doc in docs])`.
4. Writes full documents to `doc_store.add(docs)` when a docstore is configured.
5. Optionally writes markdown chunk debug files if `KH_CHUNKS_OUTPUT_DIR` is configured.

`to_retrieval_pipeline(...)` returns a `VectorRetrieval` sharing the same vector store, docstore, and embedding object.

### `VectorRetrieval`

`VectorRetrieval(vector_store=..., doc_store=..., embedding=..., top_k=5, retrieval_mode="hybrid", rerankers=[...])` returns `list[RetrievedDocument]`.

Important parameters:

- `top_k`: final number of retrieved documents.
- `first_round_top_k_mult`: multiplier used when `do_extend=True`.
- `retrieval_mode`: `vector`, `text`, or `hybrid`.
- `scope`: optional doc id filter passed through kwargs.
- `do_extend`: retrieve a larger first round before filtering.
- `thumbnail_count`: number of linked thumbnail documents to include for image evidence.

Mode behavior:

- `vector`: embeds the query, calls `vector_store.query(...)`, then loads full docs from `doc_store.get(ids)`.
- `text`: calls `doc_store.query(...)` when `scope` is provided; in-memory docstore text query returns no results.
- `hybrid`: runs vector query and scoped docstore text query concurrently, merges results, then applies rerankers.

Retrieval requires a docstore. Without `doc_store`, `VectorRetrieval` raises a value error because vector ids alone are not enough to reconstruct full `Document` metadata and text.

### `TextVectorQA`

`TextVectorQA(retrieving_pipeline=..., qa_pipeline=...)` is a simple coordinator:

1. Calls `retrieving_pipeline(question, **kwargs)`.
2. Calls `qa_pipeline(question, retrieved_documents, **kwargs)`.

Use it for provider-free tests by supplying a custom QA component that accepts `(question, retrieved_documents)` and returns a `Document` with answer text and trace metadata.

## Storage Contracts

### `BaseDocumentStore`

Required methods:

- `add(docs, ids=None, **kwargs)`
- `get(ids) -> list[Document]`
- `get_all() -> list[Document]`
- `count() -> int`
- `query(query, top_k=10, doc_ids=None) -> list[Document]`
- `delete(ids)`
- `drop()`

`InMemoryDocumentStore` stores documents by `doc_id`, supports `exist_ok=True`, and can save/load JSON. Its `query(...)` method returns an empty list, so full-text retrieval requires a different docstore implementation.

### `BaseVectorStore`

Required methods:

- `add(embeddings, metadatas=None, ids=None) -> list[str]`
- `query(embedding, top_k=1, ids=None, **kwargs) -> tuple[list[list[float]], list[float], list[str]]`
- `delete(ids, **kwargs)`
- `drop()`

`LlamaIndexVectorStore` adapts LlamaIndex vector stores. Its `query(...)` maps Kotaemon args to `VectorStoreQuery`, then returns embeddings, similarities, and ids.

## Embeddings and LLMs

### `BaseEmbeddings`

`BaseEmbeddings.run(...)` delegates to `invoke(...)` and returns `list[DocumentWithEmbedding]`. Custom embedding test doubles should preserve input text and metadata when constructing output documents so retrieval/QA traces remain explainable.

### `BaseLLM`

`BaseLLM.run(...)` delegates to `invoke(...)`. Concrete implementations may support `invoke`, `ainvoke`, `stream`, or `astream`; do not assume all providers implement streaming.

Route endpoint URLs, API keys, local server compatibility, and provider-specific constructor settings to `model-providers`.

## Prompt Templates

`PromptTemplate(template, ignore_invalid=True)` records placeholders and populates with Python-style format fields.

- `template.placeholders` exposes required variable names.
- `populate(..., safe=True)` raises `ValueError` when placeholders are missing.
- Extra kwargs produce a warning.
- Invalid placeholder names warn by default or raise when `ignore_invalid=False`.
- `partial_populate(...)` allows missing placeholders to remain in the template.

`BasePromptComponent(template=..., **values)` wraps a template as a `BaseComponent` and returns `Document(text=..., metadata={"origin": "PromptComponent"})`.

## QA, Evidence, and Citations

### `PrepareEvidencePipeline`

`PrepareEvidencePipeline(max_context_length=32000, trim_func=None)` converts `list[RetrievedDocument]` into a `Document` whose `content` is `(evidence_mode, evidence, images)`.

Evidence modes:

- `0`: text.
- `1`: table.
- `2`: chatbot scenario.
- `3`: figure/image.

It reads metadata such as `file_name`, `page_label`, `type`, `table_origin`, `window`, and `image_origin`. Preserve those keys before QA if source traceability matters.

### `CitationPipeline`

`CitationPipeline(llm=...)` asks an LLM to return exact supporting quotes via a `CiteEvidence` schema. It returns `None` on parsing or provider failures. Treat `None` as a citation failure, not as evidence that no citation exists.

### `AnswerWithContextPipeline`

`AnswerWithContextPipeline` prepares prompts for text, table, chatbot, and figure evidence. Its `stream(...)` yields chat `Document` chunks and returns a final `Document` with metadata:

- `citation_viz`
- `mindmap`
- `citation`
- `qa_score`

The base class has a non-implemented `invoke(...)`; use `stream(...)` or a subclass that implements `invoke(...)`.

`prepare_citations(answer, docs)` matches citations back to retrieved documents and separates cited from uncited evidence. It depends on rendering utilities, so keep fallback diagnostics that inspect `answer.metadata["citation"]`, retrieved `doc.score`, and source metadata directly.

### Inline citations

`AnswerWithInlineCitation` asks the LLM to return start/end phrases plus final answer citations. It parses phrases into `InlineEvidence` records and uses phrase matching to map citations back to document spans.

## Reranking

`BaseReranking.run(documents, query) -> list[Document]` transforms or filters retrieved documents.

- `LLMReranking` prompts an LLM for YES/NO relevance and filters results. If all are filtered out, it returns the first `top_k` documents to avoid empty output.
- `LLMScoring` keeps documents and writes `llm_reranking_score` metadata based on LLM logprobs.

If a reranker imports provider SDKs or fails due missing optional dependencies, either remove it for core debugging or route setup to `model-providers`.

## Reasoning Helpers

- `Thought(prompt=..., llm=..., post_process=...)` populates a prompt, calls an LLM, and returns a `Document` containing a dict from `post_process`.
- `thought1 + thought2` creates a `ManualSequentialChainOfThought`.
- `ManualSequentialChainOfThought(thoughts=[...], llm=..., terminate=...)` passes accumulated dict values between thoughts and can stop early.
- `SimpleLinearPipeline` runs prompt -> LLM -> optional post-processor.
- `GatedLinearPipeline` only runs when its condition component matches `condition_text`.
- `SimpleBranchingPipeline` runs all branches.
- `GatedBranchingPipeline` returns the first non-empty branch output and requires `condition_text`.

## Safe Introspection

Use the bundled inspector before relying on memory or stale docs:

```bash
python skills/kotaemon/sub-skills/rag-core/scripts/inspect_pipeline_components.py --repo-root <repo-root>
```

Read `discovery_mode` for each module:

- `import`: the module imported successfully and runtime signatures were inspected.
- `ast`: import failed or was skipped, so source was parsed without executing module code.

AST mode is expected when optional provider, rendering, telemetry, or app dependencies are absent. It is still useful for class names, bases, methods, and top-level functions.
