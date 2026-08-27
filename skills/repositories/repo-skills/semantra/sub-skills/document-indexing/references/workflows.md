# Document Indexing Workflows

## Purpose

Read this when constructing Semantra commands that preprocess local text or PDF
files, choose a cache directory, adjust windows, or validate that indexing
finished before interactive search.

## Minimal installed-package checks

Run these before indexing a large corpus:

```sh
semantra --help
semantra --list-models
semantra --show-semantra-dir
```

If `semantra --help` fails because the package cannot import, read the root
[troubleshooting](../../../references/troubleshooting.md) reference first.

## Create a tiny command fixture

When you need a safe local corpus to test command construction, run:

```sh
python scripts/create_tiny_corpus.py --output-dir ./tiny-semantra-corpus
```

From this sub-skill directory, the script writes three UTF-8 `.txt` files and
prints a sample Semantra command. Running the sample command may download the
selected embedding model; the script itself never downloads anything.

## Preprocess without starting the browser UI

Use `--no-server` when the goal is to build or refresh cache artifacts only:

```sh
semantra --no-server --semantra-dir ./semantra-cache report.pdf notes/*.txt
```

This reads every filename, extracts text or PDF content, computes tokens,
embeddings, and Annoy indexes, writes cache artifacts, and exits without
starting Flask.

## Index and launch the local UI

Omit `--no-server` when the user wants to search immediately after processing:

```sh
semantra --semantra-dir ./semantra-cache report.pdf notes/*.txt
```

After processing, Semantra starts a local server on `127.0.0.1:8080` by default.
For query syntax and UI behavior, continue with
[interactive-search](../../interactive-search/SKILL.md).

## Choose a cache directory

Semantra uses an application directory by default. Prefer an explicit
`--semantra-dir` when:

- the task must be reproducible across shells;
- the user wants to inspect or archive processed artifacts;
- multiple experiments use different models or windows;
- you need a temporary cache for a bounded smoke test.

Use the CLI to discover the default directory instead of guessing:

```sh
semantra --show-semantra-dir
```

Then inspect either the default directory or your explicit cache directory with:

```sh
python scripts/inspect_semantra_cache.py --cache-dir ./semantra-cache
```

## Text files and encodings

Semantra treats non-`.pdf` inputs as text. It opens them with the configured
encoding and `errors="ignore"`. The default is UTF-8. If important characters are
missing or garbled, rerun with an explicit encoding:

```sh
semantra --encoding latin-1 --semantra-dir ./latin-cache --no-server legacy.txt
```

Changing encoding changes the generated text chunks and therefore should be
kept separate from previous cache experiments.

## PDF files

Files whose names end in `.pdf` use Semantra's PDF extraction path. Semantra
writes converted text and a page-position index, then computes tokens and
embeddings from the extracted text. If a PDF is scanned image-only, protected,
corrupt, or has unusual text ordering, extraction quality may be poor even when
rendering succeeds.

Validate PDF cache groups by looking for:

- a converted PDF text artifact;
- a PDF positions JSON artifact;
- the normal token/config/embedding/Annoy artifacts for the same document hash.

## Window command patterns

Default:

```sh
semantra --windows 128_0_16 <files>
```

Smaller, more precise windows:

```sh
semantra --windows 64_0_8 <files>
```

Larger context windows:

```sh
semantra --windows 256_0_32 <files>
```

Multiple windows can be processed:

```sh
semantra --windows 128_0_16,256_0_32 <files>
```

Only the first configured window is used for search in Semantra 0.1.12 query
routes. Additional windows still produce cache artifacts and may be useful for
experimentation or future code changes.

## Reprocessing and `--force`

Semantra reuses artifacts when it finds a complete matching cache group for the
document hash and model/window configuration. Use `--force` when:

- a previous run was interrupted;
- cache files are incomplete or corrupted;
- the user wants to rebuild after changing source documents but the cache did
  not appear to refresh;
- you intentionally changed dependency versions or model behavior without
  changing the serialized configuration.

Prefer inspecting the cache before deleting anything. If only one document group
is corrupt, delete or rebuild that group rather than the entire cache directory.

## Safe validation checklist

- `semantra --help` exits successfully.
- `semantra --list-models` prints the preset registry.
- The target filenames exist and are local files.
- The user accepts any model download/API/privacy constraints.
- A custom `--semantra-dir` exists or can be created.
- `inspect_semantra_cache.py` shows config/token/embedding artifacts after a
  no-server preprocessing run.
