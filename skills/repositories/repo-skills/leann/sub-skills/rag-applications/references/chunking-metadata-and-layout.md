# Chunking, metadata, and layout

## Canonical passage contract

Normalize every loader to:

```python
{
    "text": "non-empty passage text",
    "metadata": {
        "source": "stable source identifier",
        "file_path": "path when applicable",
        "file_name": "display name when applicable"
    }
}
```

Metadata should be a small flat mapping of JSON-compatible values. Keep one
field name and one type per concept across the whole index. Do not put secrets,
raw credentials, binary payloads, or large message bodies in metadata.

Recommended optional fields:

| Family | Useful fields | Type guidance |
|---|---|---|
| Documents | `document_type`, `section`, `page`, `creation_date`, `last_modified_date` | Page integer; dates ISO-8601 strings |
| Code | `language`, `file_extension`, `start_line_no`, `end_line_no`, `line_count`, `node_count` | Numeric line fields; extension starts with `.` |
| Browser | `title`, `url`, `domain`, `last_visited`, `visit_count`, `typed_count` | Counts integers |
| Calendar | `event`, `start`, optional `end`/`location` in a custom loader | Dates use one timezone policy |
| Conversations | `source`, conversation/channel/contact identity, first/last timestamp, count | Counts integers; avoid unstable display names as sole IDs |
| Images | `image_path`, `image_name`, `image_dir` | One record per image |
| Visual PDF | `pdf_path`, `pdf_name`, `page_number`, `image_path` | Page number one-based integer |

## Chunk size and overlap

A useful chunk is small enough for the embedding model and large enough to
retain one semantic unit. Size units differ by surface:

- Public `leann build` document and non-AST code sizes are described in tokens.
- The packaged chunking utility and app-derived examples historically pass
  character-like values to LlamaIndex's `SentenceSplitter`; do not transfer a
  numeric setting between surfaces without checking its unit.
- AST size and overlap are non-whitespace characters. Source guidance estimates
  code conservatively at roughly 1.2 tokens per character.

Always enforce:

```text
size > 0
0 <= overlap < size
estimated(size + overlap) <= embedding input budget
```

Start with these evidence-backed baselines, then verify against the chosen
embedding limit:

| Content | Size | Overlap | Notes |
|---|---:|---:|---|
| Public CLI documents | 256 tokens | 128 tokens | Default |
| Public CLI traditional code | 512 tokens | 50 tokens | Default when not using AST |
| Public CLI AST | 300 characters | 64 characters | Default; final chunks can expand |
| Email app-derived chunks | 256 | 25 | Shorter overlap |
| WeChat app-derived chunks | 192 | 64 | Conversation-oriented |
| iMessage app-derived chunks | 1000 | 200 | Concatenated conversations |

An overlap equal to or larger than size is invalid even if a lower layer would
silently adjust it. Validate explicitly so the build manifest matches reality.

## AST dispatch and fallback

AST-aware chunking recognizes `.py`, `.java`, `.cs`, `.ts`, `.tsx`, `.js`, and
`.jsx`. It separates recognized code documents from text documents, annotates
code language, uses AST chunks for code, and uses traditional chunks for text.

Fallback conditions include:

- `astchunk` import failure;
- missing language metadata;
- unsupported extension;
- parser failure for one file;
- empty code content.

The safe behavior is deterministic traditional chunking, preserving document
metadata. AST-specific fields such as `start_line_no` may then be absent. Record
`chunking_strategy` yourself in a custom pipeline if downstream validation must
distinguish `ast` from `traditional`; the built-in metadata does not guarantee
that field.

## Extension and ignore policy

The default public build allowlist covers text/Markdown/Office documents and a
broad set of code/config extensions, but PDF handling is special and may also
be enabled when no custom list is provided. Prefer an explicit list for a
bounded RAG corpus. Common defaults include:

```text
.txt .md .docx .pptx
.py .js .ts .jsx .tsx .java .cpp .c .h .hpp .cs .go .rs .rb
.php .swift .kt .scala .r .sql .sh .json .yaml .yml .xml .toml
.ini .cfg .conf .html .css .scss .vue .svelte .ipynb .jl
```

Policy:

1. Normalize extensions to lowercase with a leading dot.
2. Exclude hidden paths by default.
3. Honor `.gitignore` on directory scans.
4. Remember that explicitly named files bypass `.gitignore` filtering.
5. Exclude generated outputs, environments, caches, vendored dependencies,
   indexes, rendered pages, and the destination directory.
6. Set and enforce a maximum file size in a custom loader. The app-derived code
   workflow used 1,000,000 bytes.
7. Count empty, unreadable, malformed, and unsupported files separately.

## Metadata filters

`LeannSearcher.search(..., metadata_filters=...)` and public `leann search
--metadata-filters` apply AND logic across fields and across operators on one
field. Supported operators are:

- comparison: `==`, `!=`, `<`, `<=`, `>`, `>=`;
- membership: `in`, `not_in`;
- string: `contains`, `starts_with`, `ends_with`;
- boolean: `is_true`, `is_false`.

Example:

```bash
leann search project-code "request validation" --show-metadata \
  --metadata-filters '{"file_path":{"ends_with":".py"},"line_count":{"<=":100}}'
```

Missing fields, unsupported operators, type mismatches, and evaluation errors
remove the affected result rather than guaranteeing a raised exception. Filters
are post-retrieval, so a very small candidate set can hide valid filtered
matches. Validate the schema first and choose a candidate count appropriate to
the expected selectivity.

Membership is exact: `{"tags": {"in": ["rag"]}}` asks whether the entire field
value is in the expected collection; it does not mean “does a list-valued field
contain rag.” Use `contains` only when its string-conversion behavior is
acceptable.

## Temporal semantic-file recipe

The source semantic-file utilities are intentionally not bundled as executable
helpers: they hard-code a local index base, macOS Spotlight folders, and
side-effecting output paths. Distill them into this explicit recipe instead.

### Collection

On macOS, an authorized collector may query Spotlight for approved roots and
emit records with:

```text
Path, Name, Size, ContentType, Kind, CreationDate, ContentChangeDate
```

Spotlight access and folder selection are private-data operations. The planner
must not run them. On other platforms, replace Spotlight with an approved file
manifest generator that emits the same schema.

### Build

For each record, form concise embedding text from name, path, size, content type,
and kind. Preserve dates as:

```python
metadata = {
    "creation_date": item.get("CreationDate"),
    "modification_date": item.get("ContentChangeDate"),
}
```

Drop missing values. Require a non-empty list and at least one successfully
added item before building. Choose the index base explicitly; never default to
whatever the current directory resolves to.

### Search with relative time

1. Parse expressions of the form `[around|about|roughly|approximately] N
   hour|day|week|month|year[s] [ago]`.
2. Inject `now` for deterministic tests. Exact phrases cover target-to-now;
   fuzzy phrases use a documented buffer (the source recipe used 20%).
3. Remove the matched phrase from the semantic query and reject a remaining
   query shorter than four characters.
4. Retrieve semantic candidates once.
5. Filter by `modification_date`, falling back to `creation_date`, using parsed
   ISO datetimes rather than raw string comparison.
6. Count missing and malformed dates and report the final range. The fixed
   30-day month and 365-day year approximations must be disclosed.

## Data layout

Keep immutable inputs and generated artifacts separate:

```text
rag-run/
  inputs/             # approved source roots or manifests
  indexes/            # index artifacts only
  manifests/          # schema, counts, chunking settings, source hashes if allowed
  samples/            # optional redacted validation samples
  pages/              # optional rendered PDF pages
```

Never place `indexes/`, `pages/`, or generated manifests under a recursively
indexed input root. The manifest should include source roots, extension/ignore
policy, loader version, chunk units/sizes/overlaps, metadata schema, loaded/
skipped/failed/chunk counts, embedding model identity, and build timestamp. It
must not include credentials or private passage text.

## Validation ledger

Before build:

- input roots and destination are distinct;
- source type, extension, ignore, hidden, size, and empty-file policies are set;
- chunk units and overlap inequalities are valid;
- metadata fields and types are declared.

After load/chunk:

- loaded + skipped + failed counts reconcile with discovered inputs;
- every passage has non-empty text;
- every passage has stable source identity;
- sampled text, path, dates, page/line ranges, and conversation identity agree;
- no generated output has re-entered the corpus.

After build/search:

- index artifacts exist at the intended base;
- stored passage count matches the accepted chunk count;
- one known-answer semantic query retrieves the expected source;
- one metadata/time filter includes and excludes known fixtures correctly;
- zero-result behavior explains whether retrieval, schema, filter, or source
  collection caused the result.
