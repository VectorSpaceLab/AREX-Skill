# High-level and CLI troubleshooting

Diagnose the input, dependency, and path first. Keep a failing local fixture
small and preserve the original exception/message when reporting a problem.

## Install and import failures

- The base distribution installs NumPy, but the default high-level wrapper
  imports `Stemmer` and constructs a Numba-backed retriever. Install the
  package's stemmer/Numba core extras (or the equivalent `PyStemmer` and
  `numba` packages) before using `bm25s.high_level`.
- If `import bm25s.high_level` fails with `ModuleNotFoundError: Stemmer`, the
  problem is the optional PyStemmer dependency, not the input file.
- If construction fails while selecting or compiling the Numba backend, check
  that Numba is installed and compatible with the installed NumPy. Do not
  claim that high-level mode automatically falls back to NumPy; its defaults
  request Numba explicitly.
- Rich is optional for `-u` interactive search. Without it, the picker falls
  back to a plain input prompt. Install the CLI extra only when colored tables
  are wanted.
- The CLI's `mcp launch` path is outside this branch. Follow
  [hub-mcp-and-evaluation](../../hub-mcp-and-evaluation/SKILL.md), including its
  verified version-sensitive `mcp<2` compatibility finding; do not assume the
  latest `mcp` release works.

## Optional dependency and runtime symptoms

- A first high-level indexing run may compile Numba and show progress bars. It
  can be slower than later runs; this is expected compilation overhead.
- CPU is the required backend for this workflow. No CUDA-only setup or GPU
  claim is needed. Keep optional acceleration choices explicit and route deeper
  backend diagnosis to the appropriate sibling skill.
- Progress output is normal. Suppress it only at the surrounding process level
  if a log consumer requires clean output; the high-level wrapper does not
  expose a `show_progress` argument.

## Data and configuration failures

- `FileNotFoundError` from Python load or `Error: File '...' not found.` from
  the CLI means the input path is absent. Check the path and current working
  directory; do not substitute a repository fixture.
- `ValueError: Unsupported file extension: ...` means the suffix is not one of
  lowercase `.txt`, `.csv`, `.json`, or `.jsonl`. Rename or preprocess the file.
- A CSV with the wrong `-c/--column` reports
  `Column '<name>' not found in CSV.`. Without `-c`, the first header is used,
  which may be an ID or metadata column rather than document text.
- A JSON list of dictionaries with an explicit or inferred missing key raises a
  `KeyError` in `.json` loading. A JSONL record missing the chosen key raises a
  `ValueError` identifying the key and a short line prefix. Fix the schema or
  choose the correct `document_column`; do not skip malformed records.
- A top-level JSON object is rejected with
  `JSON file must contain a list of strings or dicts.`. Convert it to a list or
  select the intended list before loading.
- Empty TXT, JSON, or JSONL inputs load to an empty list and CLI indexing exits
  with `Error: No documents found in the input file.`. An empty/headerless CSV
  follows an implementation quirk and can return a `BM25Search` object from
  `load`; treat that as invalid input and add a header plus at least one row.
- Document values should already be strings. The loader does not serialize
  arbitrary numbers, nulls, or nested JSON objects into searchable text.

## API failures and surprising results

- Pass `queries` as a list of strings, such as `search(["cat"] , k=3)`. A bare
  string is iterable and is interpreted as multiple one-character queries.
- `language` currently accepts only `"english"`; another value raises
  `NotImplementedError`.
- `bm25_kwargs` and `tokenizer_kwargs` must be dictionaries or `None`. Passing
  `corpus` inside `bm25_kwargs` is reserved and raises `ValueError`.
- Empty strings, whitespace-only queries, and queries whose terms are all
  unknown return empty hit lists. This is intentional high-level behavior.
- A requested `k` larger than the corpus is clamped to the document count. A
  negative `k` is not a supported shorthand for empty output and can raise
  `ValueError: negative dimensions are not allowed`; use `k=0` or validate
  earlier.
- Result IDs are zero-based positions, not values from an `id` field in an
  input record. The high-level loader extracts only the selected text value.

## CLI path and index failures

- `Error: Must specify --index or use --user flag.` means search had neither
  `-i/--index` nor `-u/--user`.
- `Error: Index directory '...' not found.` means the resolved local or user
  index path does not exist. With `-u -i NAME`, pass the directory name, not a
  path that should be interpreted relative to the current directory.
- `Error loading index: ...` indicates missing/corrupt low-level index files or
  an incompatible saved index. Use the persistence route to inspect required
  files rather than creating empty placeholders.
- `Error: Corpus not found in index.` means the saved index lacks a corpus; the
  high-level CLI search path requires one because it returns document text.
- If `-u` reports no indices, index at least one file with `bm25 index FILE -u`
  first. The picker recognizes only directories containing
  `params.index.json`.
- If the search output says fewer results than requested, compare `-k` with the
  saved document count. Oversized top-k is intentionally clamped. A negative
  top-k is a caller error, not a recoverable missing-result condition.
- Search re-tokenizes the loaded corpus with the default high-level English
  configuration. If an index was built with unusual tokenizer settings, use
  controlled low-level persistence/retrieval instead of assuming the CLI will
  restore those settings.

## Workflow-specific recovery checklist

1. Reproduce with a temporary or user-supplied local file and `bm25 --help`;
   avoid network data.
2. Verify the suffix, encoding, header/key, and whether every JSONL record has
   the selected field.
3. Load the file in Python and print `len(corpus)` before indexing.
4. Index to a fresh path, then search with a small positive `-k` and compare
   terminal output with the saved JSON's `total_documents` and `num_results`.
5. For user-directory issues, print the resolved home directory and index name
   in the calling environment; do not silently change `HOME` in a production
   workflow.
