# Retrieval and RAG Workflows

## Local BM25 retrieval smoke test

Use this before involving embedders, providers, or generators.

```python
from haystack import Document
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
from haystack.components.writers import DocumentWriter
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.document_stores.types import DuplicatePolicy

store = InMemoryDocumentStore(index="rag-smoke")
writer = DocumentWriter(store, policy=DuplicatePolicy.OVERWRITE)
writer.run([
    Document(id="paris", content="Jean lives in Paris.", meta={"city": "Paris", "lang": "en"}),
    Document(id="berlin", content="Mark lives in Berlin.", meta={"city": "Berlin", "lang": "en"}),
])

retriever = InMemoryBM25Retriever(store, top_k=2)
result = retriever.run(query="Who lives in Paris?")
assert result["documents"]
assert result["documents"][0].id == "paris"
```

## Metadata-filtered retrieval

```python
filters = {"field": "meta.lang", "operator": "==", "value": "en"}
result = retriever.run(query="capital city", filters=filters, top_k=3)
```

If this returns no documents, check `store.count_documents()` and then `store.filter_documents(filters)` before changing scoring.

## Pipeline-only retrieval

```python
from haystack import Pipeline

pipeline = Pipeline()
pipeline.add_component("retriever", InMemoryBM25Retriever(store, top_k=5))
output = pipeline.run({"retriever": {"query": "Paris", "top_k": 2}})
documents = output["retriever"]["documents"]
```

Keep retrieval pipelines separate from RAG pipelines when debugging; a broken generator should not obscure a retrieval issue.

## Local RAG skeleton with generator placeholder

Use a small component placeholder when verifying RAG wiring without network credentials. Replace only the `answerer` with a real prompt builder plus generator when the retrieval path is proven.

```python
from haystack import Document, Pipeline, component
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
from haystack.document_stores.in_memory import InMemoryDocumentStore

@component
class ContextAnswerer:
    @component.output_types(reply=str)
    def run(self, query: str, documents: list[Document]) -> dict[str, str]:
        context = " | ".join(doc.content or "" for doc in documents)
        return {"reply": f"query={query}; context={context}"}

store = InMemoryDocumentStore()
store.write_documents([Document(content="Jean lives in Paris.")])

rag = Pipeline()
rag.add_component("retriever", InMemoryBM25Retriever(store, top_k=1))
rag.add_component("answerer", ContextAnswerer())
rag.connect("retriever.documents", "answerer.documents")

question = "Who lives in Paris?"
result = rag.run({"retriever": {"query": question}, "answerer": {"query": question}})
assert "Jean" in result["answerer"]["reply"]
```

For real generation, keep retrieval wiring the same and route documents into prompt builders/generators covered by `../../generation-and-model-components/SKILL.md`.

## Embedding retrieval pattern

1. Choose one embedding model family for both documents and queries.
2. Embed documents during indexing, then write documents with `.embedding` populated.
3. At query time, embed the query and pass the vector as `query_embedding`.

```python
retriever = InMemoryEmbeddingRetriever(store, top_k=5, return_embedding=False)
result = retriever.run(query_embedding=query_vector, filters=filters)
```

If embeddings are missing or mismatched, verify `len(document.embedding) == len(query_vector)` for at least one stored document and choose `embedding_similarity_function` to match the model guidance.

## Hybrid retrieval with joiner

```python
from haystack import Pipeline
from haystack.components.joiners import DocumentJoiner
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever, InMemoryEmbeddingRetriever

pipeline = Pipeline()
pipeline.add_component("bm25", InMemoryBM25Retriever(store, top_k=10))
pipeline.add_component("dense", InMemoryEmbeddingRetriever(store, top_k=10))
pipeline.add_component("joiner", DocumentJoiner(join_mode="reciprocal_rank_fusion", top_k=5))
pipeline.connect("bm25.documents", "joiner.documents")
pipeline.connect("dense.documents", "joiner.documents")

result = pipeline.run({"bm25": {"query": query}, "dense": {"query_embedding": query_vector}})
final_docs = result["joiner"]["documents"]
```

Use `merge` with explicit `weights` when scores are calibrated. Use rank fusion when BM25 and dense scores are not directly comparable.

## Multi-query retrieval

```python
from haystack.components.retrievers import MultiQueryTextRetriever

base = InMemoryBM25Retriever(store, top_k=2)
multi = MultiQueryTextRetriever(retriever=base, max_workers=3)
result = multi.run(queries=["Paris resident", "Who lives in Paris?", "Jean city"])
```

Multi-query retrievers deduplicate documents and sort by score. Pass base retriever runtime options through `retriever_kwargs`.

## Sentence-window retrieval

Use after splitting documents with metadata such as `source_id`, `split_id`, and preferably `split_idx_start`.

```python
from haystack.components.retrievers import SentenceWindowRetriever

window = SentenceWindowRetriever(store, window_size=2, raise_on_missing_meta_fields=True)
base_docs = retriever.run(query="third sentence", top_k=1)["documents"]
expanded = window.run(retrieved_documents=base_docs)
context_windows = expanded["context_windows"]
```

If using different metadata names, set `source_id_meta_field` and `split_id_meta_field` explicitly.

## Auto-merging retrieval

Use after hierarchical splitting and after a base retriever returns leaf documents.

```python
from haystack.components.retrievers.auto_merging_retriever import AutoMergingRetriever

merger = AutoMergingRetriever(parent_store, threshold=0.5)
merged = merger.run(documents=leaf_documents)["documents"]
```

The parent store must contain parent documents with `__children_ids`; leaf documents must include `__parent_id`, `__level`, and `__block_size`.

## Rank retrieved documents

```python
from haystack.components.rankers import LostInTheMiddleRanker, MetaFieldRanker

freshness_ranker = MetaFieldRanker(meta_field="date", meta_value_type="date", weight=0.3, top_k=5)
ranked = freshness_ranker.run(documents=documents)["documents"]

layout_ranker = LostInTheMiddleRanker(word_count_threshold=1200)
context_ready = layout_ranker.run(documents=ranked)["documents"]
```

Use `MetaFieldRanker` when business metadata matters. Use `LostInTheMiddleRanker` immediately before prompt construction for long contexts.

## Extractive reading

```python
from haystack.components.readers import ExtractiveReader

reader = ExtractiveReader(top_k=3)
reader.warm_up()
answers = reader.run(query="Who lives in Paris?", documents=documents)["answers"]
```

This path requires optional Hugging Face/transformers dependencies and model download access unless the model is already available. For new projects, check the current reader integration guidance because the core `ExtractiveReader` is deprecated for Haystack 3.

## Retrieval validation checklist

- Assert `store.count_documents() > 0` after indexing.
- For filters, compare `filter_documents(filters)` count with retriever output.
- For BM25, test a query containing an exact expected token.
- For embeddings, verify query/document embedding dimensionality and similarity function.
- For joiners, inspect duplicate document IDs and score distributions before and after joining.
- For RAG, include retriever outputs in pipeline results while debugging so answer quality can be traced to source documents.
