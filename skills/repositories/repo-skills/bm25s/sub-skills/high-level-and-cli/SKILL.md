---
name: high-level-and-cli
description: "Load local text files, build a beginner-friendly bm25s searcher,
  and operate the bm25 index/search CLI with explicit file, index, and result
  contracts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---
# High-level and CLI workflows

Use this route when a task needs a one-line local-file search workflow or the
`bm25` console command. It owns `bm25s.high_level.load`, `index`, and
`BM25Search`, plus the `bm25s.terminal` implementation behind the `bm25`
entry point. It does not own low-level BM25 scoring, tokenizer design,
long-lived index file format details, Hub/evaluation operations, or MCP server
behavior.

- For low-level index save/load and corpus-file invariants, use
  [persistence-and-corpus-io](../persistence-and-corpus-io/SKILL.md).
- For tokenization, custom stemmers, or shared vocabularies, use
  [tokenization-and-stopwords](../tokenization-and-stopwords/SKILL.md).
- Route `bm25 mcp launch` and its version-sensitive MCP dependency handling to
  [hub-mcp-and-evaluation](../hub-mcp-and-evaluation/SKILL.md); do not improvise
  MCP setup in this route.

## Python quick path

```python
import bm25s.high_level as bm25

corpus = bm25.load("documents.csv", document_column="text")
searcher = bm25.index(corpus)
results = searcher.search(["machine learning"], k=5)
for hit in results[0]:
    print(hit["id"], hit["score"], hit["document"])
```

Keep `queries` as a list of strings. `search()` returns one result list per
query, preserving query order. Every hit is a dictionary with the integer
positional `id`, a Python `float` `score`, and the original corpus value under
`document`. The high-level object keeps the corpus separately, so IDs are
positions in the list supplied to `index()` rather than application IDs.

The high-level defaults are intentionally opinionated: English only,
PyStemmer English stemming, English stopword removal, lowercasing, Numba
retrieval, NumPy CSC construction, and `auto_compile=False` followed by a
safe compile without warmup. These defaults require the optional PyStemmer and
Numba packages in addition to NumPy. Pass explicit `bm25_kwargs` or
`tokenizer_kwargs` only when the required dependencies and behavior are known.
The only accepted `language` value in this revision is `"english"`.

## Load local documents

`load(path, document_column=None)` accepts lowercase `.txt`, `.csv`, `.json`,
and `.jsonl` suffixes. Use [references/api-reference.md](references/api-reference.md)
for the exact selection rules. In short:

- TXT treats each nonblank, stripped line as one document.
- CSV uses `csv.DictReader`; `document_column` selects a named column, or the
  first header column is selected by default.
- JSON requires a top-level list. It accepts a list of strings or a list of
  dictionaries; for dictionaries, `document_column` selects a key or the
  first key in the first item is inferred.
- JSONL skips blank lines, reads one object per nonblank line, and selects the
  explicit key or the first key in the first record. Every later record must
  contain that key.

Use strings as document values. The loader does not normalize arbitrary JSON
values into text. Missing files raise `FileNotFoundError`; unsupported suffixes
raise `ValueError`. Missing JSON/CSV fields are data errors, not invitations to
silently skip records.

## Search semantics

- `search(queries, k=10, n_jobs=1)` clamps a positive `k` to the corpus size.
  Asking for more hits than documents therefore returns all documents, not an
  error. `k=0` returns empty hit lists; do not pass a negative `k`.
- A query that tokenizes to no terms returns `[]`, and mixed batches retain an
  empty list in the corresponding position. Unknown terms can likewise produce
  no hits.
- Results are sorted by the underlying retriever. Ties and zero-score hits are
  still returned when `k` allows them. An empty corpus can be constructed but
  cannot produce hits.
- `BM25Search` is an in-memory convenience wrapper. The CLI's index command
  writes a reusable index plus corpus/tokenizer files; use the persistence
  route for direct low-level control.

## CLI recipe

The installed entry point is `bm25` (`bm25s.cli:main`). The normal local
workflow is:

```bash
bm25 index documents.txt -o my_index
bm25 search -i my_index "machine learning" -k 5 -s results.json
```

The exact short/long flags are documented in
[references/cli-reference.md](references/cli-reference.md). Indexing supports
`-o/--output`, `-c/--column`, and `-u/--user`; searching supports
`-i/--index`, `-k/--top-k`, `-s/--save`, and `-u/--user`.

`-u` is a filesystem side effect, not merely a lookup toggle. Indexing writes
to `~/.bm25s/indices/<name>` and creates parent directories; `-o NAME` is a
custom name and without `-o` the name is `<input-stem>_index`. Searching with
`-u -i NAME` resolves that name under the same directory. Searching with `-u`
without `-i` opens a picker (Rich when installed, otherwise a text fallback).
Only directories containing `params.index.json` are offered. No user index is
created by a search.

The CLI clamps an oversized `-k` to the number of saved documents before
searching, and the high-level searcher clamps again. Consequently, terminal
output and saved JSON report the actual number returned. Use a nonnegative,
reasonably sized integer; negative values are not a supported way to request
zero results.

## Result files and errors

`-s PATH` writes an object containing `query`, `num_results`,
`total_documents`, and `results`. The result dictionaries retain `id`, `score`,
and `document`; JSON output is not shortened, even though terminal display
truncates a document preview after 200 characters.

Treat these messages as actionable diagnostics: missing input or index paths,
load failures such as a missing column/key, empty input (`No documents found`),
and a missing `--index` unless `--user` is selected. Do not conceal a malformed
fixture by changing columns or skipping bad JSONL records. See
[references/troubleshooting.md](references/troubleshooting.md) and run the
self-contained local recipe at
[scripts/simple_file_search.py](scripts/simple_file_search.py) before asking
for external data.

## Handoff checklist

Record the input format, selected column/key, document count, high-level
English/PyStemmer/Numba defaults or overrides, query batch and `k`, and whether
an index was written to a user directory. For CLI use, record the resolved
index path, exact flags, result JSON path, and whether `k` was clamped. Keep
MCP launch work with the linked sibling route. The bundled script accepts an
explicit local path or creates a temporary fixture and is safe to run from an
arbitrary working directory.
