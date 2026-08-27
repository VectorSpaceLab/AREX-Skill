# Ingestion API Reference

This reference captures the ingestion/loading APIs verified for `llama-index-core==0.14.22`.

## Imports

```python
from llama_index.core import Document, SimpleDirectoryReader
from llama_index.core.schema import TextNode, MetadataMode
from llama_index.core.node_parser import (
    SentenceSplitter,
    TokenTextSplitter,
    MarkdownNodeParser,
    HierarchicalNodeParser,
    get_leaf_nodes,
    get_root_nodes,
)
from llama_index.core.ingestion import IngestionPipeline, IngestionCache
from llama_index.core.ingestion.pipeline import DocstoreStrategy
```

## Documents and Nodes

- `Document(text=..., metadata={...}, id_=...)` is the generic input object; legacy `doc_id` maps to `id_`, and legacy `extra_info` maps to `metadata`.
- `Document.text` returns the text content; `Document.doc_id` aliases `id_`.
- `TextNode` and `Document` share `metadata`, `excluded_embed_metadata_keys`, `excluded_llm_metadata_keys`, `relationships`, `metadata_template`, and `metadata_separator`.
- `get_metadata_str(mode=MetadataMode.LLM)` omits `excluded_llm_metadata_keys`; `MetadataMode.EMBED` omits `excluded_embed_metadata_keys`; `MetadataMode.NONE` returns no metadata string.
- Metadata is included in chunking for metadata-aware splitters, so large metadata reduces effective chunk size.

## `SimpleDirectoryReader`

Verified constructor shape:

```python
SimpleDirectoryReader(
    input_dir=None,
    input_files=None,
    exclude=None,
    exclude_hidden=True,
    exclude_empty=False,
    errors="ignore",
    recursive=False,
    encoding="utf-8",
    filename_as_id=False,
    required_exts=None,
    file_extractor=None,
    num_files_limit=None,
    file_metadata=None,
    raise_on_error=False,
    fs=None,
)
```

Key behavior:

- Exactly one loading source is needed: `input_files` or `input_dir`; `input_files` overrides directory discovery and `exclude`.
- `exclude` is a list of glob patterns. With `recursive=True`, each pattern is applied under `**/`; otherwise only at the top level.
- `exclude_hidden=True` skips any path segment that starts with `.`.
- `exclude_empty=True` skips zero-byte files; the default keeps them.
- `required_exts` compares suffixes exactly, so use values like `[".md", ".pdf"]`.
- `num_files_limit` limits files encountered during walking before final sorting; use only for sampling.
- `filename_as_id=True` uses file names as document IDs, useful for docstore upserts and avoiding regenerated random IDs.
- `file_metadata` receives the file path string and returns metadata for each `Document`.
- `file_extractor` maps extensions to reader instances for custom parsing. Optional formats such as PDFs may require installing a matching reader/parser dependency.
- `errors="ignore"` hides text decoding errors; set `errors="strict"` and `raise_on_error=True` while debugging bad encodings.

Useful methods:

```python
documents = reader.load_data(show_progress=True)
for batch in reader.iter_data():
    ...
documents = await reader.aload_data()
```

## Node Parsers

### `SentenceSplitter`

Verified defaults include `separator=" "`, `chunk_size=1024`, `chunk_overlap=200`, `paragraph_separator="\n\n\n"`, `include_metadata=True`, and `include_prev_next_rel=True`.

```python
splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=200)
nodes = splitter.get_nodes_from_documents(documents)
```

It prefers paragraphs and sentences before falling back to regex, words, and characters. It raises `ValueError` when `chunk_overlap > chunk_size` or when metadata consumes the whole effective chunk size.

### `TokenTextSplitter`

`TokenTextSplitter(chunk_size=1024, chunk_overlap=20, separator=" ", backup_separators=["\n"], keep_whitespaces=False, include_metadata=True)` uses tokenizer length directly and is useful when deterministic token windows matter more than sentence boundaries.

### `MarkdownNodeParser`

```python
parser = MarkdownNodeParser.from_defaults(header_path_separator="/")
nodes = parser.get_nodes_from_documents(markdown_documents)
```

It splits on Markdown headers outside fenced code blocks and, when `include_metadata=True`, adds `header_path` metadata such as `/Overview/Install/`.

### `HierarchicalNodeParser`

```python
parser = HierarchicalNodeParser.from_defaults(chunk_sizes=[2048, 512, 128], chunk_overlap=20)
all_nodes = parser.get_nodes_from_documents(documents)
leaf_nodes = get_leaf_nodes(all_nodes)
root_nodes = get_root_nodes(all_nodes)
```

It returns a flat list containing parent and child nodes with relationship metadata. Use leaf nodes for fine-grained retrieval and parent/root nodes when preserving context.

## `IngestionPipeline`

Verified constructor shape:

```python
IngestionPipeline(
    name="default",
    project_name="Default",
    transformations=None,
    readers=None,
    documents=None,
    vector_store=None,
    cache=None,
    docstore=None,
    docstore_strategy=DocstoreStrategy.UPSERTS,
    disable_cache=False,
)
```

Runtime methods:

```python
nodes = pipeline.run(
    documents=documents,
    show_progress=False,
    cache_collection=None,
    in_place=True,
    store_doc_text=True,
    num_workers=None,
)
nodes = await pipeline.arun(documents=documents)
pipeline.persist("pipeline_storage")
pipeline.load("pipeline_storage")
```

Important behavior:

- If `transformations=None`, defaults are `SentenceSplitter()` and `Settings.embed_model`; specify transformations explicitly when you want parsing without embeddings.
- `cache` defaults to `IngestionCache()` unless `disable_cache=True`.
- `IngestionCache.clear(collection=None)` removes cached transformation results for a collection.
- `persist()` stores cache and optional docstore; `load()` restores them.
- `DocstoreStrategy.UPSERTS` and `UPSERTS_AND_DELETE` require both `docstore` and `vector_store` to apply full upsert/delete semantics. With a docstore but no vector store, the run warns and falls back to duplicate-only handling for that run while leaving `pipeline.docstore_strategy` unchanged.
- `num_workers > 1` uses spawned multiprocessing. Keep transformations picklable and avoid shared mutable clients.
