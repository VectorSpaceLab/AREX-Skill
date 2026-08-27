# Document and code RAG

## Choose the public workflow

| Corpus | Build shape | Chunking |
|---|---|---|
| PDF/TXT/Markdown and other supported documents | `leann build INDEX --docs PATH...` | Traditional document chunks |
| Supported source code only | Add `--file-types` and `--use-ast-chunking` | AST for supported languages; traditional fallback |
| Mixed Python/Markdown or code plus prose | Include both extensions and add `--use-ast-chunking` | AST for recognized code, traditional for prose |
| One or more explicit files | Pass each after `--docs` | Same type-driven split; hidden explicit files remain excluded unless opted in |

The public CLI accepts multiple files and directories. A directory scan is
recursive, omits hidden paths by default, applies its `.gitignore`, and skips a
directory that is itself a Git submodule. An explicitly supplied file is not
filtered by `.gitignore`, so list such files deliberately.

## End-to-end pattern

1. **Load** only the intended roots. Use `--file-types` as one comma-separated
   extension list, for example `.pdf,.txt,.md` or `.py,.java,.md`.
2. **Chunk** with separate prose and code budgets. Traditional document and code
   CLI sizes are token-oriented; AST size and overlap are non-whitespace
   characters. Overlap must be smaller than its corresponding size.
3. **Attach metadata** before `add_text` in a custom API flow. At minimum retain
   `file_path`, `file_name`, and `source`; add stable project-relative identity,
   language, dates, or section only when available.
4. **Validate** that at least one source loaded, all passage text is non-empty,
   source paths match their chunks, and sampled code chunks preserve meaningful
   functions/classes or use the documented fallback.
5. **Build** into a named index. The ordinary build command updates an existing
   index rather than forcing a full rebuild; do not add `--force` casually.
6. **Search** before chat. Use `--show-metadata` and a query with a known answer:

   ```bash
   leann search project-docs "Where is request validation implemented?" \
     --top-k 8 --show-metadata
   ```

7. **Chat** only after the retrieved passages are relevant:

   ```bash
   leann ask project-docs "Summarize the request validation flow"
   ```

   Model/provider configuration is intentionally outside this sub-skill.

## Safe command recipes

Plan a command without executing it:

```bash
python scripts/build_rag_command.py document ./documents \
  --index project-docs --file-types .pdf .txt .md
```

A pure code index with the implementation-supported AST languages:

```bash
python scripts/build_rag_command.py code ./src \
  --index project-code --file-types .py .java .cs .ts .tsx .js .jsx
```

A mixed Python/Markdown corpus:

```bash
python scripts/build_rag_command.py code ./project \
  --index project-mixed --file-types .py .md \
  --doc-chunk-size 256 --doc-chunk-overlap 64 \
  --ast-chunk-size 300 --ast-chunk-overlap 64
```

The planner checks paths and numeric relationships but does not enumerate,
open, build, or search the corpus. Its output uses the public `leann` CLI.

## Chunking contracts

### Traditional document chunks

Use traditional chunks for prose and unsupported source types. The app-derived
baseline was 256 with 128 overlap; the public CLI describes document size and
overlap in tokens. For short structured records, reduce overlap. For long prose,
choose a size below the embedding model limit after including overlap.

### AST-aware code chunks

The AST utility recognizes these mappings:

| Extension | Parser language |
|---|---|
| `.py` | Python |
| `.java` | Java |
| `.cs` | C# |
| `.ts`, `.tsx`, `.js`, `.jsx` | TypeScript parser |

AST output is normalized to `{"text": ..., "metadata": ...}`. Metadata can
include source identity plus `start_line_no`, `end_line_no`, `line_count`, and
`node_count` when the parser supplies them. Code chunks with a start line are
rendered with line-number prefixes for navigation.

If `astchunk` cannot import, a language is unsupported, parsing fails, or a
code document lacks language metadata, LEANN falls back to traditional
chunking. This is the deterministic safe path: do not disable or emulate AST
parsing. Verify fallback by checking that chunks still exist and retain
`file_path`/`file_name`; do not require AST-only line metadata after fallback.

### Code scanning constraints

The app-derived code workflow excluded `.git`, `__pycache__`, `node_modules`,
virtual environments, `build`, `dist`, and `target`, and skipped files above
1,000,000 bytes. The public build command uses hidden-path and `.gitignore`
rules rather than the app's explicit `--exclude-dirs` and `--max-file-size`
flags. Put generated/vendor/oversized paths in `.gitignore`, narrow `--docs`, or
supply only approved files. Never enable hidden inputs just to make a count
nonzero.

## Custom composition with the Python API

Use a custom loader only when the public build command cannot preserve required
metadata or source semantics. Normalize each passage before adding it:

```python
from leann.api import LeannBuilder

builder = LeannBuilder(backend_name="hnsw")
for chunk in chunks:
    text = chunk["text"].strip()
    metadata = dict(chunk.get("metadata") or {})
    if not text:
        continue
    if not (metadata.get("file_path") or metadata.get("source")):
        raise ValueError("chunk lacks source identity")
    builder.add_text(text, metadata=metadata)
builder.build_index("project-docs")
```

Keep loading and chunking deterministic. A loader failure must not be converted
into a successful zero-document build.

## Acceptance checks

- Every requested root exists and is a file or directory.
- Extensions are normalized and match actual intended inputs.
- Hidden, ignored, generated, vendored, oversized, and empty files have an
  explicit policy.
- Traditional overlap is less than traditional size; AST overlap is less than
  AST size.
- Every passage is non-empty and has source identity.
- Code/prose dispatch and AST fallback are observable in a bounded sample.
- At least one known-answer query retrieves the expected source with metadata.
- Chat is not used to conceal poor retrieval.
