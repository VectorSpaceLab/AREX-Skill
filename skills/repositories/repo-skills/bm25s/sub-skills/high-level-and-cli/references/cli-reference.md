# `bm25` CLI reference

The package metadata installs the console script `bm25`, which calls
`bm25s.cli:main`. The top-level parser has `mcp`, `index`, and `search`
subcommands. This route documents `index` and `search`; MCP launch is owned by
[hub-mcp-and-evaluation](../../hub-mcp-and-evaluation/SKILL.md).

## Live command shapes

```text
bm25 index [-h] [-o OUTPUT] [-c COLUMN] [-u] FILE
bm25 search [-h] [-i INDEX] [-k TOP_K] [-s SAVE] [-u] QUERY
```

The long and short forms below are the exact parser flags in this revision.

### `index`

```text
bm25 index FILE [-o OUTPUT] [-c COLUMN] [-u]
```

| Flag | Meaning |
|---|---|
| `FILE` | Input path with `.csv`, `.txt`, `.json`, or `.jsonl` suffix |
| `-o OUTPUT`, `--output OUTPUT` | Output directory/name; default is `<filename>_index` |
| `-c COLUMN`, `--column COLUMN` | Document column/key for CSV, JSON, or JSONL |
| `-u`, `--user` | Save below `~/.bm25s/indices/` |

Indexing checks that `FILE` exists before loading. It then calls the high-level
loader and indexer, creates the output directory, saves the underlying BM25
index with its corpus, and saves tokenizer vocabulary and stopwords. Existing
output files can be replaced because the save path is reused; choose a fresh
output name when preserving an older index matters.

Without `-u`, `OUTPUT` is interpreted as a normal path relative to the current
working directory (or as an absolute path). With `-u`, `OUTPUT` is a name under
the user index directory, not an arbitrary path. When `-u` is present without
`-o`, the name is the input filename stem plus `_index`.

Successful indexing prints the loaded document count, output path, and unique
token count. Empty input is rejected with `Error: No documents found in the
input file.` and exit status 1. Loader exceptions are summarized as
`Error loading documents: ...` and exit status 1.

Examples:

```bash
bm25 index notes.txt -o ./notes-index
bm25 index records.csv -c text -o ./records-index
bm25 index records.jsonl --column content -u --output records
```

## `search`

```text
bm25 search [-i INDEX] [-k TOP_K] [-s SAVE] [-u] QUERY
```

| Flag | Meaning |
|---|---|
| `QUERY` | Required query string |
| `-i INDEX`, `--index INDEX` | Index path, or user-index name with `-u` |
| `-k TOP_K`, `--top-k TOP_K` | Requested result count; default `10` |
| `-s SAVE`, `--save SAVE` | Write result object to this JSON path |
| `-u`, `--user` | Resolve an index in `~/.bm25s/indices/`; pick one if `-i` is omitted |

Without `-u`, `-i` is required. With `-u -i NAME`, the command resolves
`~/.bm25s/indices/NAME`; `NAME` is not treated as a current-directory path.
With `-u` and no `-i`, `list_user_indices()` scans only immediate child
directories containing `params.index.json`, sorts names, and invokes an
interactive picker. Rich is used when importable; otherwise a plain text
number/name prompt is used. If no indices exist, the command reports that fact
and exits 1.

The command verifies the resolved directory exists, loads the saved corpus,
converts dictionary corpus entries to their `text` field when present (or the
first dictionary value otherwise), rebuilds a default high-level searcher, and
runs the query. This is a convenience workflow, not a promise that every
custom low-level tokenizer configuration will be reconstructed. Use the
persistence route for controlled reloads.

`actual_k = min(requested_k, number_of_documents)` is applied before the
high-level search, which applies the same upper clamp again. Thus a corpus of
three documents searched with `-k 20` produces at most three hits and prints
`Showing top 3 of 3 documents`. A negative top-k is unsupported and can result
in an underlying negative-dimensions error; use `0` for an intentionally empty
request or, preferably, a positive value.

Terminal output displays a heading, each rank, score formatted to four decimal
places, and a document preview. Previews longer than 200 characters are
truncated with `...` for display only.

## Saved result JSON

With `-s results.json`, the parent directory is created and the file contains:

```json
{
  "query": "machine learning",
  "num_results": 2,
  "total_documents": 3,
  "results": [
    {"id": 0, "score": 0.42, "document": "machine learning is ..."}
  ]
}
```

`num_results` is the length actually returned after top-k clamping. The JSON
contains the full document string; display truncation does not alter it. Scores
are JSON numbers and IDs are positional integers.

## User-directory lifecycle

`-u` creates `~/.bm25s/indices/` and the selected index directory during
indexing. It changes the location of all generated index, corpus, and tokenizer
files, and it makes the index discoverable by the picker. It does not configure
a global service or copy the source input. Keep the input file separately if it
will be needed for a rebuild.

To inspect the route without indexing, use the parser help commands:

```bash
bm25 --help
bm25 index --help
bm25 search --help
```

For a no-network Python fixture check, use
[scripts/simple_file_search.py](../scripts/simple_file_search.py).
