# Ingestion Troubleshooting

## No Files Loaded

Symptoms: `ValueError: No files found`, an empty-looking reader, or fewer documents than expected.

Checks:

- Confirm exactly one source is configured: `input_dir="..."` for discovery or `input_files=[...]` for explicit files.
- Run `scripts/validate_ingestion_inputs.py` with the same `--recursive`, `--required-ext`, `--exclude`, `--include-hidden`, and `--exclude-empty` choices.
- Remember `exclude_hidden=True` by default; any path segment beginning with `.` is skipped.
- `recursive=False` only walks one directory level; set `recursive=True` for nested folders.
- `required_exts` requires dotted suffixes like `.md`; `md` will not match.
- `exclude` patterns are glob-style and are applied during directory discovery, not when `input_files` is supplied.

## Hidden, Empty, or Excluded Files Are Missing

- Hidden files: pass `exclude_hidden=False` only when the user explicitly wants dotfiles or files inside dot-directories.
- Empty files: default `exclude_empty=False` keeps zero-byte files; if the user set `exclude_empty=True`, zero-byte files are intentionally skipped.
- Excluded directories: an excluded directory pattern rejects all child files whose parent path starts with that rejected directory.

## Encoding and Parser Failures

- `errors="ignore"` is the default and can silently drop undecodable characters; use `errors="strict"` and `raise_on_error=True` to reveal bad encodings.
- Set `encoding="utf-8"`, `"latin-1"`, or a known source encoding explicitly when text appears corrupted.
- PDF and rich document parsing may require optional parser packages. Keep this sub-skill focused on reader arguments; route package/provider installation choices to integrations/storage.
- When one bad file should not abort the load, keep `raise_on_error=False`; when debugging, set it to `True`.

## Metadata Too Large for Chunks

Symptoms: `Metadata length (...) is longer than chunk size (...)` or warnings about chunks under 50 tokens.

Fixes:

- Increase `chunk_size` or reduce metadata values before splitting.
- Add noisy keys to `excluded_embed_metadata_keys` and/or `excluded_llm_metadata_keys` before calling metadata-aware splitters.
- Keep high-cardinality metadata for filtering, but exclude long raw fields from LLM/embed rendered text.

## Chunk Overlap or Chunk Size Errors

- `SentenceSplitter` and `TokenTextSplitter` raise when `chunk_overlap > chunk_size`; lower overlap first.
- Very small `chunk_size` values interact poorly with metadata and separators; test with `splitter.get_nodes_from_documents(documents[:1])` before processing a corpus.
- Markdown splitting ignores headers inside fenced code blocks; if no sections are produced as expected, inspect Markdown header syntax and code fences.

## Stale Cache, Stale Docstore, or Duplicate Node IDs

Symptoms: old chunks remain after parser changes, changed files do not update, duplicates appear after reload, or deletions do not propagate.

Fixes:

- Clear or version `IngestionCache`: `cache.clear()` or pass a new `cache_collection` when transformations change.
- Use stable file/document IDs: `filename_as_id=True` for file loading or `Document(id_=...)` for raw text.
- Rebuild docstore/vector store state when switching ID strategy or parser hierarchy.
- Use `DocstoreStrategy.UPSERTS` or `UPSERTS_AND_DELETE` with both a `docstore` and `vector_store`; with only a docstore, upsert/delete semantics fall back to duplicate-only for that run.
- Persist and load cache/docstore together via `pipeline.persist()` and `pipeline.load()` to avoid mismatched state.

## Async and Parallel Caveats

- `num_workers` above CPU count is reduced with a warning.
- Multiprocessing uses spawned workers; avoid lambdas, local closures, open files, or non-picklable clients inside transformations.
- Parallel cache writes are merged after worker results; if results look inconsistent, reproduce with `num_workers=None` first.
- Async ingestion still depends on async-capable transformations or clients; it is not a guaranteed speedup for local text splitting.
