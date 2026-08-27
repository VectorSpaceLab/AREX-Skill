---
name: ingestion-and-loading
description: "Load local files or raw text into LlamaIndex Documents, split them
  into metadata-aware nodes, and run ingestion pipelines with cache/docstore
  controls. Use for SimpleDirectoryReader configuration, Document/TextNode
  metadata,
  SentenceSplitter/TokenTextSplitter/MarkdownNodeParser/HierarchicalNodeParser,
  IngestionPipeline, and ingestion troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Ingestion and Loading

Use this sub-skill when the user needs to get data into `llama_index.core` before indexing or querying.

## Route Here For

- Loading files with `SimpleDirectoryReader`, including `input_dir`, `input_files`, `exclude`, `exclude_hidden`, `exclude_empty`, `recursive`, `required_exts`, `filename_as_id`, `file_extractor`, `file_metadata`, and `raise_on_error`.
- Creating or inspecting `Document`, `TextNode`, node IDs, metadata, `excluded_embed_metadata_keys`, and `excluded_llm_metadata_keys`.
- Splitting documents into nodes with `SentenceSplitter`, `TokenTextSplitter`, `MarkdownNodeParser`, or `HierarchicalNodeParser`.
- Running `IngestionPipeline` with transformations, `IngestionCache`, optional docstores, `DocstoreStrategy`, `persist()`, `load()`, `run()`, `arun()`, and `num_workers`.
- Diagnosing no files loaded, skipped hidden/empty/excluded files, encoding failures, optional parser dependencies, oversized metadata, bad chunk overlap, stale caches/docstores, duplicate IDs, and async/parallel ingestion caveats.

## Do Not Use For

- Choosing index classes, retrievers, query engines, or response synthesizers; use `../indexing-and-querying/SKILL.md`.
- Selecting external vector stores, embedding providers, file parser integrations, or optional provider packages; use `../integrations-and-storage/SKILL.md`.
- Building agents, tools, memory, or workflows; use `../agents-and-workflows/SKILL.md`.

## Fast Start

```python
from llama_index.core import Document, SimpleDirectoryReader
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter

reader = SimpleDirectoryReader(
    input_dir="data",
    recursive=True,
    required_exts=[".md", ".pdf"],
    exclude_hidden=True,
    filename_as_id=True,
)
documents = reader.load_data()

splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=200)
nodes = splitter.get_nodes_from_documents(documents)

pipeline = IngestionPipeline(transformations=[splitter])
nodes = pipeline.run(documents=documents, show_progress=True)
```

For raw text, bypass readers:

```python
from llama_index.core import Document

doc = Document(text="Release notes...", metadata={"source": "manual"}, id_="release-notes")
```

## Required References

- Read `references/workflows.md` for loading recipes, metadata-aware chunking, and cache/docstore refresh patterns.
- Read `references/api-reference.md` for signatures, defaults, imports, and parser selection rules.
- Read `references/troubleshooting.md` when ingestion loads nothing, parsing fails, chunks look wrong, or cache/docstore results are stale.
- Run `scripts/validate_ingestion_inputs.py --help` before proposing a `SimpleDirectoryReader` setup for unfamiliar local file trees.

## Bundled Helper

Use the safe validator to inspect planned local inputs and print likely reader arguments without importing LlamaIndex or reading file contents:

```bash
python sub-skills/ingestion-and-loading/scripts/validate_ingestion_inputs.py data --required-ext .md --required-ext .pdf --recursive --filename-as-id
```

It reports matched, hidden, empty, excluded, and extension-filtered files plus a copyable `SimpleDirectoryReader(...)` argument sketch.
