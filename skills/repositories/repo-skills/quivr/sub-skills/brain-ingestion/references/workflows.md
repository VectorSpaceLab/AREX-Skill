# Brain Ingestion Workflows

## Canonical path from text file to brain

Use this pattern when the user has a small text file and wants a brain they can
inspect or query later.

```python
from uuid import uuid4

from quivr_core import Brain
from quivr_core.files.file import load_qfile
from quivr_core.llm import LLMEndpoint
from quivr_core.processor.implementations.simple_txt_processor import SimpleTxtProcessor
from quivr_core.processor.splitter import SplitterConfig
from quivr_core.rag.entities.config import LLMEndpointConfig
from quivr_core.storage.local_storage import TransparentStorage

brain_id = uuid4()
qfile = await load_qfile(brain_id, "note.txt")
processor = SimpleTxtProcessor(splitter_config=SplitterConfig(chunk_size=400, chunk_overlap=100))
processed = await processor.process_file(qfile)
brain = await Brain.afrom_langchain_documents(
    name="notes",
    langchain_documents=processed.chunks,
    storage=TransparentStorage(),
    llm=LLMEndpoint.from_config(LLMEndpointConfig(llm_api_key="test")),
)
```

Why this path works:

- `load_qfile(...)` captures file metadata and the current `original_file_name`.
- `process_file(...)` returns a `ProcessedDocument`; the chunks live in `.chunks`.
- `Brain.afrom_langchain_documents(...)` avoids the current `Brain.from_files`
  bug and builds the vector store directly from the chunk list.

## Local storage path

Use `LocalStorage` when the user needs the uploaded files persisted on disk.
The storage object still feeds the same chunking flow, so the key decision is
whether the runtime should keep a physical copy of the uploaded file.

## Save and load path

Use `await brain.save(out_dir)` only after the brain uses a serializable embedder
and vector store.

- Supported save path: FAISS plus OpenAI embeddings.
- Safe load path: `Brain.load(saved_path)` where `saved_path` came from `save(...)`.

## Metadata hygiene

When you construct `langchain_core.documents.Document` objects by hand, include
`original_file_name` in metadata when you expect readable source labels later.
That keeps downstream citations and source displays stable.
