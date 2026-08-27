# Kotaemon RAG Workflows

This guide shows provider-agnostic composition patterns for Kotaemon's core RAG classes. Replace fake embeddings or fake QA components with real provider objects only after model setup is known to work; provider setup belongs in `model-providers`.

## Minimal Metadata-Preserving Documents

Create documents with stable ids and source metadata before indexing:

```python
from kotaemon.base import Document

source_docs = [
    Document(
        text="Kotaemon components are callable pipeline units.",
        id_="doc-components-1",
        metadata={"file_name": "architecture.md", "page_label": "1", "section": "components"},
    ),
    Document(
        text="RetrievedDocument carries score and retrieval_metadata.",
        id_="doc-schema-1",
        metadata={"file_name": "schema.md", "page_label": "2", "section": "schema"},
    ),
]
```

Preserve metadata in every custom component. The most common traceability bug is returning new `Document(text=...)` objects without copying `metadata`, `doc_id`, or retrieval scores.

## Provider-Free Test Doubles

For local pipeline tests, implement small `BaseEmbeddings` and QA components instead of using external providers:

```python
from kotaemon.base import BaseComponent, Document, DocumentWithEmbedding
from kotaemon.embeddings import BaseEmbeddings

class LengthEmbedding(BaseEmbeddings):
    def invoke(self, text, *args, **kwargs):
        docs = self.prepare_input(text)
        return [
            DocumentWithEmbedding(
                embedding=[float(len(doc.text)), float(doc.text.count(" ") + 1)],
                text=doc.text,
                metadata=dict(doc.metadata),
                id_=doc.doc_id,
            )
            for doc in docs
        ]

class TraceQA(BaseComponent):
    def run(self, question, retrieved_documents, **kwargs):
        return Document(
            text="; ".join(doc.text for doc in retrieved_documents),
            metadata={
                "question": question,
                "sources": [doc.metadata for doc in retrieved_documents],
                "scores": [doc.score for doc in retrieved_documents],
            },
        )
```

This checks component wiring, metadata preservation, and score propagation without API keys.

## Build a Simple Vector Pipeline

Use a docstore and vectorstore together. `VectorRetrieval` needs `doc_store` to reconstruct full documents from vectorstore ids.

```python
from kotaemon.base import Document
from kotaemon.indices import VectorIndexing, VectorRetrieval
from kotaemon.storages import InMemoryDocumentStore, InMemoryVectorStore

vector_store = InMemoryVectorStore()
doc_store = InMemoryDocumentStore()
embedding = LengthEmbedding()

indexing = VectorIndexing(
    vector_store=vector_store,
    doc_store=doc_store,
    embedding=embedding,
)
indexing([
    Document(text="metadata must survive retrieval", id_="d1", metadata={"file_name": "notes.md"}),
    Document(text="citations depend on exact text spans", id_="d2", metadata={"file_name": "qa.md"}),
])

retrieval = VectorRetrieval(
    vector_store=vector_store,
    doc_store=doc_store,
    embedding=embedding,
    retrieval_mode="vector",
    top_k=2,
)
retrieved = retrieval("how do citations work?")
```

After retrieval, inspect:

```python
[(doc.doc_id, doc.score, doc.metadata) for doc in retrieved]
```

If this loses metadata, fix the document creation, docstore writes, or custom embedding/vectorstore wrapper before debugging QA.

## Compose Retrieval and QA

`TextVectorQA` expects a retrieval component and a QA component:

```python
from kotaemon.indices.vectorindex import TextVectorQA

qa = TraceQA()
pipeline = TextVectorQA(retrieving_pipeline=retrieval, qa_pipeline=qa)
answer = pipeline("Which files mention citations?")
print(answer.text)
print(answer.metadata["sources"])
print(answer.metadata["scores"])
```

This pattern is useful for tests because `TraceQA` exposes retrieved source metadata and scores in the final answer.

## Convert Retrieved Docs to Evidence

Use `PrepareEvidencePipeline` when you need evidence strings in the same style as Kotaemon QA components:

```python
from kotaemon.indices.qa.format_context import PrepareEvidencePipeline

prepare_evidence = PrepareEvidencePipeline(max_context_length=4000)
evidence_doc = prepare_evidence(retrieved)
evidence_mode, evidence_text, images = evidence_doc.content
```

Metadata affects evidence rendering:

- `type="table"` uses `table_origin` and marks table mode.
- `type="chatbot"` uses `window` and marks chatbot mode.
- `type="image"` uses `image_origin`, image captions, and marks figure mode.
- `file_name` and `page_label` are included in source headings.

If evidence text is empty, check retrieval results first, then metadata keys, then trim settings.

## Trace Low-Confidence Cited Answers

When an answer looks weak or citations seem wrong, inspect both retrieval scores and QA metadata.

Suggested trace:

1. Log each retrieved doc: `doc_id`, `score`, `metadata["file_name"]`, `metadata["page_label"]`, `metadata.get("llm_reranking_score")`, `metadata.get("llm_trulens_score")`.
2. Generate evidence with `PrepareEvidencePipeline` and confirm the cited phrase exists in `evidence_text`.
3. Inspect `answer.metadata.get("qa_score")`; missing `logprobs` usually means the provider did not return token probabilities.
4. Inspect `answer.metadata.get("citation")`; `None` means citation extraction failed or no tool call was returned.
5. If inline citations are used, verify the start/end phrases copied exact spans from retrieved document text.
6. Compare cited doc ids with uncited high-score docs; uncited high-score docs can indicate prompt, reranking, or evidence-formatting issues.

A compact diagnostic record can look like:

```python
trace = {
    "question": question,
    "retrieved": [
        {
            "doc_id": doc.doc_id,
            "score": doc.score,
            "source": doc.metadata.get("file_name"),
            "page": doc.metadata.get("page_label"),
            "rerank": doc.metadata.get("llm_reranking_score"),
        }
        for doc in retrieved
    ],
    "qa_score": answer.metadata.get("qa_score"),
    "citation": answer.metadata.get("citation"),
}
```

## Preserve Metadata Through a Custom Component

Custom components should copy document dictionaries or explicitly copy metadata. Avoid returning plain strings when downstream components need source traceability.

```python
from kotaemon.base import BaseComponent, RetrievedDocument

class ScoreFloorFilter(BaseComponent):
    min_score: float = 0.2

    def run(self, documents):
        kept = []
        for doc in documents:
            if doc.score >= self.min_score:
                cloned = RetrievedDocument(**doc.to_dict(), score=doc.score)
                cloned.retrieval_metadata = dict(doc.retrieval_metadata)
                cloned.metadata = dict(doc.metadata)
                cloned.metadata["score_floor"] = self.min_score
                kept.append(cloned)
        return kept
```

Use this pattern before QA or citation stages so source labels, page labels, table/image markers, and scores remain available.

## Add Reranking Safely

A reranker is any `BaseReranking` that accepts `(documents, query)` and returns documents.

```python
from kotaemon.indices.rankings import BaseReranking

class MetadataBoostReranker(BaseReranking):
    def run(self, documents, query):
        for doc in documents:
            if doc.metadata.get("section") == "faq":
                doc.metadata["metadata_boost"] = 1.0
        return sorted(documents, key=lambda doc: doc.metadata.get("metadata_boost", 0), reverse=True)

retrieval.rerankers = [MetadataBoostReranker()]
```

When using `LLMReranking` or provider rerankers, route provider construction and credentials to `model-providers`. If an optional reranker import fails, first remove the reranker and confirm base retrieval works.

## Prompt Template Workflow

Use `PromptTemplate` to catch missing variables before calling a model:

```python
from kotaemon.llms import PromptTemplate

template = PromptTemplate("Answer in {lang}: {question}\nContext:\n{context}")
assert template.placeholders == {"lang", "question", "context"}
prompt = template.populate(lang="English", question="What is RAG?", context="...")
```

For partial templates:

```python
partial = template.partial_populate(lang="English")
```

If `populate(...)` raises `ValueError: Missing keys in template`, inspect `template.placeholders` and the kwargs passed by the component.

## Reasoning Components

Use reasoning helpers for explicit multi-step prompts, not hidden magic.

Sequential chain example:

```python
from kotaemon.llms.cot import Thought, ManualSequentialChainOfThought

summarize = Thought(prompt="Summarize {context}", post_process=lambda text: {"summary": text})
answer = Thought(prompt="Answer {question} from {summary}", post_process=lambda text: {"answer": text})
chain = ManualSequentialChainOfThought(thoughts=[summarize, answer], llm=my_llm)
result = chain(question="What changed?", context="...")
```

`Thought` outputs are dicts stored in `Document.content`. Each step receives the accumulated dict from earlier steps. Use `terminate=lambda values: ...` to stop early.

Branching/gating helpers are useful when routing prompts based on conditions, but they still call the LLM branches you attach. For provider-free tests, replace LLM calls with deterministic components.

## Component Introspection Checklist

When inheriting unfamiliar Kotaemon components:

1. Run the bundled inspector against the repo.
2. Confirm the class base: `BaseComponent`, `BaseEmbeddings`, `BaseLLM`, `BaseReranking`, `BaseDocumentStore`, or `BaseVectorStore`.
3. Check whether `run`, `invoke`, or `stream` contains the real implementation.
4. Check pydantic/TheFlow fields declared as class attributes, especially `Node(...)` defaults.
5. Read imports at the top of the module; optional app/provider dependencies may fail even when AST inspection works.
6. Instantiate with explicit objects for providers, stores, retrievers, and QA components instead of relying on app defaults unless you are inside the app context.

## Native Test Clues

The repository's tests demonstrate expected behavior:

- Document tests verify constructor behavior and `RetrievedDocument` defaults.
- Vectorstore tests verify `add`, `query`, `delete`, `save`, and `load` contracts.
- Indexing/retrieval tests patch provider calls and assert one indexed doc produces one retrieval result.
- Prompt tests assert missing variables raise errors and extra variables warn.
- Chain-of-thought tests assert `Thought` and `ManualSequentialChainOfThought` pass accumulated dict values between steps.

Use those as behavior references, but do not make runtime skill usage depend on local test files.
