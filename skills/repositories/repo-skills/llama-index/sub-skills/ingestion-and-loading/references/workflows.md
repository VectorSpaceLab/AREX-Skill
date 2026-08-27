# Ingestion Workflows

## Load Markdown and PDFs Only

Use this pattern when a user asks to load only selected extensions, exclude hidden files, keep stable file IDs, and then build metadata-aware chunks.

```python
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter

reader = SimpleDirectoryReader(
    input_dir="data",
    recursive=True,
    required_exts=[".md", ".pdf"],
    exclude=["**/drafts/**", "*.tmp"],
    exclude_hidden=True,
    exclude_empty=True,
    filename_as_id=True,
    file_metadata=lambda path: {"file_path": path, "source_type": path.rsplit(".", 1)[-1]},
)
documents = reader.load_data(show_progress=True)

for doc in documents:
    doc.excluded_embed_metadata_keys.extend(["file_path"])
    doc.excluded_llm_metadata_keys.extend(["source_type"])

splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=200, include_metadata=True)
nodes = splitter.get_nodes_from_documents(documents, show_progress=True)
```

Notes:

- Keep `required_exts` values dotted, for example `.md` and `.pdf`.
- If PDF parsing fails, keep the reader configuration but add the relevant optional parser/reader dependency in the user's project environment; provider/package selection belongs to the integrations/storage sub-skill.
- Excluding metadata from LLM/embed text does not remove metadata from the node dictionary; it only changes metadata rendered into prompts or embedding input.

## Load Explicit File Lists

Use `input_files` when the user already has a curated file list or wants to bypass directory filtering.

```python
reader = SimpleDirectoryReader(
    input_files=["README.md", "guide/intro.md"],
    filename_as_id=True,
    raise_on_error=True,
)
documents = reader.load_data()
```

`exclude`, `exclude_hidden`, `recursive`, and `required_exts` are directory-discovery controls; do not rely on them to filter `input_files`.

## Create Documents from Raw Text

```python
from llama_index.core import Document

documents = [
    Document(text=body, metadata={"source": "support-ticket", "ticket_id": ticket_id}, id_=ticket_id)
    for ticket_id, body in tickets
]
```

Use stable `id_` values when re-running ingestion with a docstore, or changed parser settings may appear as duplicated content rather than updates.

## Pick a Parser

- `SentenceSplitter`: default general-purpose text parser; preserves sentence/paragraph boundaries where possible.
- `TokenTextSplitter`: deterministic token windows; useful for very regular chunks or model-token budgeting.
- `MarkdownNodeParser`: Markdown section chunks with `header_path` metadata; useful for docs and README files.
- `HierarchicalNodeParser`: parent/child chunk hierarchy; use `get_leaf_nodes()` for fine retrieval and keep parents for context expansion.

## Run a Minimal Pipeline Without Embeddings

```python
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter

pipeline = IngestionPipeline(
    transformations=[SentenceSplitter(chunk_size=512, chunk_overlap=50)],
    disable_cache=True,
)
nodes = pipeline.run(documents=documents, show_progress=True)
```

Explicit transformations avoid the default `Settings.embed_model` step when the user only wants nodes.

## Cache and Docstore Refresh Pattern

Use this when a user changed parser settings, metadata, or file IDs and sees stale nodes or duplicate IDs.

```python
from llama_index.core.ingestion import IngestionCache, IngestionPipeline
from llama_index.core.ingestion.pipeline import DocstoreStrategy
from llama_index.core.node_parser import SentenceSplitter

cache = IngestionCache(collection="my-ingestion-v2")
cache.clear()

pipeline = IngestionPipeline(
    transformations=[SentenceSplitter(chunk_size=768, chunk_overlap=80)],
    cache=cache,
    docstore=docstore,
    vector_store=vector_store,
    docstore_strategy=DocstoreStrategy.UPSERTS,
)
nodes = pipeline.run(documents=documents, cache_collection="parser-768-v1")
pipeline.persist("pipeline_storage")
```

Refresh checklist:

- Use `filename_as_id=True` or stable `Document(id_=...)` values before relying on docstore upserts.
- Change `cache_collection` or clear the `IngestionCache` after changing splitters, metadata extraction, or transformations.
- Use both `docstore` and `vector_store` for true upsert/delete behavior. With only a docstore, LlamaIndex falls back to duplicate-only handling.
- If removing source files should delete old stored content, use `DocstoreStrategy.UPSERTS_AND_DELETE` with a vector store and a complete current document set.

## Async and Parallel Ingestion

```python
nodes = await pipeline.arun(documents=documents, num_workers=None)
nodes = pipeline.run(documents=documents, num_workers=4)
```

Guidance:

- Start sequentially; enable `num_workers` only after correctness is proven.
- Multiprocessing uses spawned workers, so transformations must be picklable and cannot depend on open handles or local closures that cannot be serialized.
- Async only helps if transformations or downstream clients support async work; CPU-bound splitting alone may not improve.
