# Brain Ingestion Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Brain.from_files` fails on non-empty input | The live snapshot still mishandles `ProcessedDocument` inside `process_files()` | Use `SimpleTxtProcessor.process_file(...).chunks` plus `Brain.afrom_langchain_documents(...)` instead |
| `process_file(...)` does not look like a list | `ProcessorBase.process_file()` returns a `ProcessedDocument` wrapper | Read `.chunks` for the real `Document` list |
| `load_qfile(...)` raises a file error | The path does not exist or the suffix is unsupported | Create the file first and make sure the extension is one the registry understands |
| `brain.save(...)` fails to serialize | The save path only supports FAISS plus OpenAI embeddings | Rebuild the brain with the supported serialization path |
| Sources or citations show the wrong filename | Custom docs are missing `original_file_name` metadata | Populate `original_file_name` when creating `Document` objects by hand |
| Chunking feels wrong | `SplitterConfig` does not match the document size | Adjust `chunk_size` and `chunk_overlap` |
| Optional parsers fail to import | The chosen backend is not installed | Stay on the core text path or install the optional backend explicitly |

## Quick recovery steps

1. Check whether the user needs the core text path or an optional parser.
2. If they only need core ingestion, route to the smoke script and the `.chunks`
   workaround.
3. If they need persistence, confirm the embedder and vector store are supported.
4. If the problem is metadata, preserve `original_file_name` before the brain is built.
