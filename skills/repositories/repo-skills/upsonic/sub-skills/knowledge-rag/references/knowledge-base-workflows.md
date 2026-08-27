# KnowledgeBase Workflows

## Verified constructor shape

`KnowledgeBase(sources, vectordb, embedding_provider=None, splitters=None, loaders=None, name=None, description=None, topics=None, use_case='rag_retrieval', quality_preference='balanced', loader_config=None, splitter_config=None, isolate_search=True, storage=None, **config_kwargs)`

## Primary methods

| Method | Use |
| --- | --- |
| `add_source(source, loader=None, splitter=None, metadata=None)` | Add one source document or path. |
| `add_text(...)` | Add raw text content into the KB. |
| `build_context(...)` | Assemble retrieval context for the current query. |
| `search(query)` | Return the most relevant retrieved text. |
| `query_async(...)` | Async query path. |
| `refresh()` | Re-index or refresh the KB. |
| `remove_document(...)` | Remove a document from the KB. |
| `update_document_metadata(...)` | Patch document metadata after ingestion. |
| `get_tools()` | Expose KB actions as tools for an agent. |

## Typical workflow

```python
from upsonic import KnowledgeBase

kb = KnowledgeBase(
    sources=["docs/"],
    vectordb=...
)
text = kb.search("What does the project do?")
```

## What to remember

- Choose the vector DB and embedding provider first; everything else hangs off that decision.
- Use `loaders` and `splitters` for format-specific ingestion control.
- Use `isolate_search=True` when you do not want retrieval to bleed across projects.
- Keep OCR and document-conversion details in the backend-specific extras reference.
