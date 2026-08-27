# Memory, Knowledge, and RAG Troubleshooting

Start by identifying the failing surface:

1. `Memory` learned facts and scopes.
2. `Knowledge` source indexing and query injection.
3. Native RAG clients (`crewai.rag`) or `RagTool` ingestion/query.
4. Embedding provider or vector DB setup.
5. CLI/runtime reset behavior.

Use [scripts/check_rag_imports.py](../scripts/check_rag_imports.py) to inspect imports without network calls, credentials, LLM calls, or destructive operations.

## Embedding Dimension Mismatch

Symptoms:

- Error mentions “Embedding dimension mismatch.”
- Error mentions vectors such as `1536-dimensional` vs `3072-dimensional`.
- Knowledge save logs suggest `crewai reset-memories -a` or `--all`.
- Searches return no usable results after switching embedding providers.
- LanceDB or vector-store operations fail on save/search/update.

Likely causes:

- Existing collection was built with one embedder and now the app uses another.
- Default embedder changed between CrewAI versions or app configs.
- `Memory`, `Knowledge`, and `RagTool` use inconsistent provider specs for a shared collection.
- Qdrant vector params were created for one dimension and queried with another.

Fixes:

1. Determine the collection owner: unified memory, crew knowledge, agent knowledge, direct RAG, or `RagTool`.
2. Keep one embedder provider/model/dimension per collection.
3. If old vectors can be discarded, reset the smallest target:
   - `crewai reset-memories --memory`
   - `crewai reset-memories --knowledge`
   - `crewai reset-memories --agent-knowledge`
   - `crewai reset-memories --all` only when several stores are affected.
4. Re-index knowledge sources or `RagTool` sources after reset.
5. For custom storage paths, use a fresh path when a collection-level reset cannot change the stored vector schema.

Prevention:

- Pin the embedding provider/model in code instead of relying on changing defaults.
- Treat embedding model migrations like data migrations.
- Do not share a collection name across experiments with different embedders.

## Missing Vector DB Optional Dependencies

Symptoms:

- Import fails for `chromadb`, `qdrant_client`, `fastembed`, or provider config modules.
- Instantiating a missing provider raises `RuntimeError` like provider `chromadb` or `qdrant` requested but not installed.
- `RagTool` construction fails when selecting a provider.

Checks:

```bash
python scripts/check_rag_imports.py --json
```

Fixes:

- Install only the provider extra or package needed for the selected workflow after approval.
- Use ChromaDB only when `chromadb` and its embedding function dependencies are available.
- Use Qdrant only when `qdrant_client` and default embedding dependencies are available, or provide a compatible custom embedding function/config.
- If installation is not allowed, fall back to local string/file knowledge with already installed dependencies or avoid RAG indexing for that run.

## Missing Embedding Provider Credentials

Symptoms:

- Default memory embedder fails asking for `OPENAI_API_KEY`.
- Knowledge indexing fails during `add_sources()`.
- `RagTool.add(...)` logs “Failed to generate embeddings.”
- Querying works structurally but returns provider auth errors.

Fixes:

- For default OpenAI-based memory or Chroma config, set the appropriate OpenAI credential in the runtime environment or pass a different `embedder`.
- For local-only retrieval, use local providers such as `onnx`, `sentence-transformer`, or `ollama` only when their dependencies and local services are available.
- Do not place API keys inside skill Markdown, generated examples, logs, or code snippets. Use placeholders like `runtime_token` and runtime configuration.
- Route chat/completion LLM auth questions to [../../llm-and-providers/SKILL.md](../../llm-and-providers/SKILL.md); this sub-skill covers embedding auth only.

## Local Storage Path or Cache Confusion

Symptoms:

- Reset command appears to succeed but old results remain.
- Two projects see unexpected shared knowledge.
- A custom storage path works in one process but not another.
- `crewai memory` TUI opens an empty store.

Checks:

- Confirm whether the code passes explicit `Memory(storage=...)`, `ChromaDBConfig(settings=...)`, `QdrantConfig(options=...)`, or `RagTool(collection_name=...)`.
- Confirm which project directory the reset command is run from.
- Confirm collection names: `knowledge_crew`, agent-role-derived collections, `rag_tool_collection`, or custom names.
- Avoid printing full local paths in shared reports; use relative or redacted descriptions.

Fixes:

- Run reset commands from the project that defines the crews/flows.
- Use explicit collection names for experiments and production collections.
- If a custom path was used, instantiate the same path for inspection or migrate to a fresh path.
- Use `Memory.tree()`, `Memory.info()`, native RAG collection counts, or `RagTool` collection info to confirm where data was written.

## Reset-Memories Target Confusion

Symptoms:

- `crewai reset-memories` prints “Please specify at least one memory type.”
- `--knowledge` does not clear learned memories.
- `--memory` does not clear `knowledge_sources` content.
- Deprecated `--long`, `--short`, or `--entities` flags behave unexpectedly.

Correct targets:

| Target | Clears |
| --- | --- |
| `--memory` / `command_type="memory"` | Unified crew/flow memory. Deprecated long/short/entity/external names map here. |
| `--knowledge` / `command_type="knowledge"` | Crew knowledge and agent knowledge collections available on the crew. |
| `--agent-knowledge` / `command_type="agent_knowledge"` | Agent-only knowledge collections. |
| `--kickoff-outputs` / `command_type="kickoff_outputs"` | Latest kickoff task output storage. |
| `--all` / `command_type="all"` | All available memory systems for discovered crews and flow memory. |

Fixes:

- Use `--memory` for learned facts stored by `Memory`.
- Use `--knowledge` or `--agent-knowledge` for indexed source documents.
- Use `--all` for dimension-mismatch migrations only when targeted reset is insufficient.
- If there is no crew or flow in the current project, the command cannot discover anything to reset.

## Unsupported Loader File Type

Symptoms:

- `RagTool.add(...)` treats a path as raw text instead of a file.
- A file extension is not recognized.
- Loader says no loader/chunker is defined for a type.
- Directory ingestion silently skips files.

Supported direct RAG loader values include `pdf_file`, `text_file`, `csv`, `json`, `xml`, `docx`, `mdx`, `directory`, `website`, `docs_site`, `github`, `youtube_video`, `youtube_channel`, `mysql`, `postgres`, and `text`.

Fixes:

- Pass `data_type` explicitly when auto-detection is ambiguous.
- Convert unsupported formats to `.txt`, `.md`, `.csv`, `.json`, or another supported format before ingestion.
- For low-level file conversion, MIME validation, or multimodal file handling, use [../../files-and-multimodal/SKILL.md](../../files-and-multimodal/SKILL.md).
- For directory ingestion, narrow with `include_extensions`, `exclude_extensions`, or `max_files`; inspect counts afterward because unprocessable files may be skipped.

## Network-Backed Loaders Need Approval or Credentials

Symptoms:

- Web, docs-site, GitHub, or YouTube loaders time out or fail authentication.
- GitHub loader cannot access a private repository.
- YouTube loader reports missing transcript package or no transcript.
- Database loaders ask for connection details or fail with DB errors.

Boundaries:

- `website`, `docs_site`, `github`, `youtube_video`, and `youtube_channel` perform network retrieval.
- `mysql` and `postgres` connect to databases and may read private data.
- Some loaders need optional packages such as `youtube-transcript-api`, `PyGithub`, database drivers, `requests`, `beautifulsoup4`, `python-docx`, or PDF parsing libraries.
- URL validation rejects unsafe schemes, `file://`, unresolved hosts, and private/reserved IP targets by default.

Fixes:

- Ask for explicit approval before network, database, or credential-bound ingestion.
- Use user-provided local snapshots when credentials are unavailable.
- For GitHub, request a scoped token only when accessing private or rate-limited repositories.
- For databases, use a read-only connection string and limit tables/queries where loader options allow.
- For YouTube, install the transcript dependency only when the user accepts network access and the source has transcripts.

## Knowledge Source File Not Found

Symptoms:

- `FileNotFoundError` says to add sources to the `knowledge` directory.
- `file_path` deprecation warning appears.
- Text/PDF/CSV/JSON source works in tests with `Path` but fails in a project run with a string path.

Fixes:

- Prefer `file_paths=[...]`, not deprecated `file_path`.
- For string paths in knowledge source classes, place files under the project `knowledge/` directory and pass paths relative to that directory.
- Use `Path(...)` only when deliberately passing an already resolved path from application code.
- Check optional parser dependencies for PDF, Excel, Docling, DOCX, and other formats.

## Knowledge Returns Irrelevant or No Results

Symptoms:

- Agent ignores known source facts.
- Crew or agent injects unrelated snippets.
- `Knowledge.query(...)` returns an empty list.

Checks and fixes:

- Confirm sources were indexed by calling `add_sources()` or letting crew/agent initialization do it.
- Lower `score_threshold` if relevant snippets are filtered out; raise it if unrelated snippets are injected.
- Increase `results_limit` for broad questions.
- Re-chunk large documents by setting source `chunk_size` and `chunk_overlap`.
- Confirm crew-level and agent-level knowledge are not confused: crew uses collection `crew`, agent uses the agent role.
- Keep the same embedder for indexing and querying.

## Memory Requires LLM or Embedder

Symptoms:

- `Memory` raises a runtime message saying it requires an LLM for analysis.
- `Memory` raises a runtime message saying it requires an embedder for vector search.
- Deep recall fails but shallow recall or explicit fields may work.

Fixes:

- Pass explicit `scope`, `categories`, and `importance` to `remember(...)` to reduce reliance on save-time LLM analysis.
- Use `depth="shallow"` for direct vector search when LLM-guided deep recall is not available.
- Provide a configured `llm` only after LLM provider auth is handled in [../../llm-and-providers/SKILL.md](../../llm-and-providers/SKILL.md).
- Provide a configured `embedder` or embedding callable for vector search.

## Source Evidence Notes

This troubleshooting reference distills current CrewAI docs, implementation, and tests for memory, knowledge, RAG, loaders, optional imports, and reset behavior. It intentionally does not direct future agents to reopen source repository files.
