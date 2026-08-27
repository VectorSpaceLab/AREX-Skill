# Workflows: Pretrained Indexing and Search

These recipes are self-contained patterns for RAGatouille 0.0.9post2 persisted-index workflows. Treat model loading, indexing, and search as potentially network/GPU/CPU-expensive unless the user has already approved the environment and downloads.

## 1. Build a New Persisted Index

Use `from_pretrained` when the task starts from a model checkpoint or Hugging Face model id.

```python
from ragatouille import RAGPretrainedModel


def main():
    model = RAGPretrainedModel.from_pretrained(
        "colbert-ir/colbertv2.0",
        index_root="./ragatouille-indexes",
    )
    documents = [
        "Hayao Miyazaki co-founded Studio Ghibli.",
        "Studio Ghibli is an animation studio based in Koganei, Tokyo.",
    ]
    index_path = model.index(
        collection=documents,
        document_ids=["miyazaki", "ghibli"],
        document_metadatas=[
            {"entity": "person", "source": "internal"},
            {"entity": "organisation", "source": "internal"},
        ],
        index_name="ghibli_demo",
        split_documents=False,
        overwrite_index=True,
    )
    print(index_path)


if __name__ == "__main__":
    main()
```

Checklist:

- Pick a stable `index_root` and `index_name`; record the returned `index_path` for later `from_index` calls.
- Validate `len(collection) == len(document_ids) == len(document_metadatas)` before loading models.
- Keep `document_ids` unique, non-empty, and all the same type.
- Use `split_documents=False` when documents are already chunked. Use `split_documents=True` plus `max_document_length` when RAGatouille should chunk long texts.

## 2. Build a Split-Document Index

The default splitter uses LlamaIndex `SentenceSplitter`. It can turn one long document into many passages while preserving the original `document_id` for every passage.

```python
index_path = model.index(
    collection=[long_article_text],
    document_ids=["article-001"],
    document_metadatas=[{"section": "profile", "source": "wiki"}],
    index_name="article_index",
    max_document_length=180,
    split_documents=True,
)
```

Expected persisted effect:

- `collection.json` contains multiple passage strings if the source document is split.
- `pid_docid_map.json` maps each passage id back to `article-001`.
- `docid_metadata_map.json` maps `article-001` to the metadata dictionary.
- Search results include both `document_id` and `passage_id`, so downstream code can distinguish source document and passage.

## 3. Use Custom Splitting or Preprocessing

Pass a custom `document_splitter_fn` when the default sentence splitter is not appropriate. The function should return dictionaries with `document_id` and `content` keys.

```python
def split_on_paragraphs(documents, document_ids, chunk_size=256):
    chunks = []
    for document, document_id in zip(documents, document_ids):
        for paragraph in document.split("\n\n"):
            paragraph = paragraph.strip()
            if paragraph:
                chunks.append({"document_id": document_id, "content": paragraph})
    return chunks


def normalize_chunks(chunks, document_ids):
    return [
        {"document_id": chunk["document_id"], "content": " ".join(chunk["content"].split())}
        for chunk in chunks
    ]

index_path = model.index(
    collection=documents,
    document_ids=document_ids,
    index_name="paragraph_index",
    split_documents=True,
    document_splitter_fn=split_on_paragraphs,
    preprocessing_fn=normalize_chunks,
)
```

Do not return plain strings from a custom splitter/preprocessor in this workflow; RAGatouille expects the processed corpus to carry document ids.

## 4. Search an Existing Index

Use `from_index` when the persisted index already exists. This is the preferred production shape because the index stores model configuration.

```python
from ragatouille import RAGPretrainedModel

model = RAGPretrainedModel.from_index("./ragatouille-indexes/colbert/indexes/ghibli_demo")
results = model.search("Who founded Studio Ghibli?", k=5)

for result in results:
    print(result["rank"], result["document_id"], result["score"])
    print(result["content"])
```

Validate result shape:

- Single string query: `results` is `list[dict]`.
- List of queries: `results` is `list[list[dict]]`.
- Each persisted-index hit should include `content`, `score`, `rank`, `document_id`, and `passage_id`.
- `document_metadata` appears only when metadata was present for the hit's `document_id` at index time.

## 5. Search Multiple Queries

```python
queries = [
    "What animation studio did Miyazaki found?",
    "Where is Studio Ghibli based?",
]
all_results = model.search(query=queries, k=3)

for query, query_results in zip(queries, all_results):
    print("QUERY:", query)
    for hit in query_results:
        print(hit["rank"], hit["document_id"], hit["content"][:120])
```

Common mistake: treating multi-query output as a flat list. Always iterate one level per input query.

## 6. Filter Search by Document IDs

Use `doc_ids` when the loaded index contains many source documents and the task needs a scoped search.

```python
results = model.search(
    query="Which film won major awards?",
    k=5,
    doc_ids=["miyazaki", "ghibli"],
    zero_index_ranks=True,
)
```

Notes:

- `doc_ids` filters to all passages belonging to those document ids.
- All ids must exist in the loaded index's `docid_pid_map`.
- With `zero_index_ranks=True`, the top hit has `rank == 0`; without it, the top hit has `rank == 1`.
- If `k` exceeds the available passage count after filtering, expect fewer hits or internal capping.

## 7. Use Fast Search Settings

```python
fast_results = model.search(
    query="short latency query",
    k=10,
    force_fast=True,
)
```

`force_fast=True` uses a smaller search budget and can be less accurate. It is useful for latency-sensitive experiments, not for final quality comparisons unless the trade-off is intentional.

## 8. Add Documents to an Existing Index

CRUD support is experimental. Prefer rebuilding the index when correctness is more important than incremental update behavior, especially for small collections.

```python
model = RAGPretrainedModel.from_index("./ragatouille-indexes/colbert/indexes/ghibli_demo")
model.add_to_index(
    new_collection=["Princess Mononoke is a 1997 film directed by Hayao Miyazaki."],
    new_document_ids=["mononoke"],
    new_document_metadatas=[{"entity": "film", "source": "internal"}],
    index_name="ghibli_demo",
    split_documents=False,
)
```

After adding, inspect or search for the new `document_id`. Existing duplicate ids are skipped in the update path.

## 9. Delete Documents from an Existing Index

```python
model = RAGPretrainedModel.from_index("./ragatouille-indexes/colbert/indexes/ghibli_demo")
model.delete_from_index(
    document_ids=["mononoke"],
    index_name="ghibli_demo",
)
```

Deletion removes every passage mapped to the selected document ids and rewrites metadata files. Because CRUD is experimental, verify with a follow-up search or by inspecting `pid_docid_map.json` and `docid_metadata_map.json`.

## 10. Validate Inputs Before Model Work

Use the bundled validator to catch common `document_ids` and `document_metadatas` problems without importing RAGatouille or downloading models.

From this sub-skill directory:

```bash
python scripts/validate_index_inputs.py \
  --collection-json collection.json \
  --document-ids-json document_ids.json \
  --document-metadatas-json document_metadatas.json \
  --json
```

For quick shell checks, JSON values can be passed inline:

```bash
python scripts/validate_index_inputs.py \
  --collection-json '["doc one", "doc two"]' \
  --document-ids-json '["a", "b"]' \
  --document-metadatas-json '[{"source":"x"}, {"source":"y"}]'
```

## 11. Validate Search Results in Downstream Code

Use schema checks instead of assuming README-only fields:

```python
def validate_persisted_search_results(results, multi_query=False):
    groups = results if multi_query else [results]
    required = {"content", "score", "rank", "document_id", "passage_id"}
    for group in groups:
        assert isinstance(group, list)
        for hit in group:
            missing = required - set(hit)
            if missing:
                raise ValueError(f"Missing result keys: {sorted(missing)}")
            if "document_metadata" in hit and not isinstance(hit["document_metadata"], dict):
                raise TypeError("document_metadata must be a dictionary when present")
```

## 12. Choose Persisted Index vs In-Memory Reranking

Choose this sub-skill's persisted index workflow when:

- The corpus is reused across sessions or services.
- Indexing cost should be paid once and search run many times.
- You need `document_id`, `passage_id`, metadata, and optional `doc_ids` filtering.
- The document set is large enough that in-memory reranking is too slow.

Route to `../../index-free-reranking/SKILL.md` when the document set is small, transient, already retrieved by another system, or should not be persisted.
