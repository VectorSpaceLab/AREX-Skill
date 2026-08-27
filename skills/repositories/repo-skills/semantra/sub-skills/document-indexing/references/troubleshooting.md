# Document Indexing Troubleshooting

## Purpose

Use this reference for Semantra failures that happen before or during document
processing: filenames, encodings, PDFs, windows, cache artifacts, and repeated
or incomplete preprocessing.

## `Error: Must provide a filename to process/query`

Likely cause: the CLI was run without positional filenames and without an early
exit flag such as `--help`, `--version`, `--list-models`, or
`--show-semantra-dir`.

Recovery:

1. Pass one or more existing files:
   ```sh
   semantra report.pdf notes/*.txt
   ```
2. If the task only checks installation, use `semantra --help` or
   `semantra --list-models` instead.

## `Invalid value for '[FILENAME]...'` or missing files

Likely cause: the shell glob did not match, the path is wrong, or a directory
was passed where the CLI expects files.

Recovery:

- Expand the glob in the shell first, for example `ls notes/*.txt`.
- Quote paths containing spaces.
- Generate a known-safe fixture with
  [create_tiny_corpus.py](../scripts/create_tiny_corpus.py) before testing the
  Semantra command shape.

## Text looks garbled or important characters are missing

Likely cause: the file is not UTF-8, while Semantra defaults to UTF-8 and ignores
decoding errors.

Recovery:

1. Identify the likely encoding from the document source.
2. Reprocess with an explicit encoding and a separate cache directory:
   ```sh
   semantra --encoding latin-1 --no-server --semantra-dir ./latin-cache legacy.txt
   ```
3. Compare token/config artifacts with
   [inspect_semantra_cache.py](../scripts/inspect_semantra_cache.py).

## PDF extraction is empty, scrambled, or slow

Likely causes:

- the PDF is scanned image-only and has no embedded text;
- the PDF is protected, corrupt, or unusually structured;
- `pypdfium2` cannot render/extract a particular page;
- the file is large and extraction simply takes time.

Recovery:

- Test with a small PDF first.
- Inspect whether the cache contains `<md5>.pdf.txt` and
  `<md5>.pdf.positions.json`.
- If the text artifact is empty or unreadable, Semantra cannot semantically
  search the PDF content without an OCR/preprocessing step outside Semantra.
- If text extraction is fine but browser navigation is wrong, route to
  [interactive-search troubleshooting](../../interactive-search/references/troubleshooting.md).

## Window string crashes or produces surprising chunks

Likely cause: `--windows` must be a comma-separated list of integer specs in the
form `size`, `size_offset`, or `size_offset_rewind`.

Recovery:

- Use known-good values such as `128_0_16`, `64_0_8`, or `256_0_32`.
- Avoid negative or non-integer values.
- Remember that only the first window is used by Semantra 0.1.12 query routes.
- Read [cache-and-data-formats.md](cache-and-data-formats.md) before comparing
  offsets or embedding counts.

## Semantra keeps reprocessing the same file

Likely causes:

- `--force` is set;
- the document content changed, changing the MD5 group;
- model, encoding, windows, tokens, Annoy tree count, or dependency behavior
  changed, creating a new config hash;
- a previous run left incomplete embeddings or Annoy indexes.

Recovery:

1. Run the cache inspector:
   ```sh
   python scripts/inspect_semantra_cache.py --cache-dir ./semantra-cache
   ```
2. Compare config JSON summaries for the same base filename.
3. If a group is incomplete, rebuild with `--force` or remove only that group.
4. Keep a separate `--semantra-dir` for experiments with different models or
   windows.

## Embedding or Annoy artifact counts do not match config JSON

Likely cause: an interrupted run, disk-full event, or incompatible cache files.

Recovery:

- Treat the group as incomplete.
- Rebuild with `--force`.
- If the issue recurs, verify free disk space and whether the model/backend is
  failing mid-run; then route model/backend errors to
  [models-and-embeddings troubleshooting](../../models-and-embeddings/references/troubleshooting.md).

## Browser static files are missing after indexing

Likely cause: Semantra's Python package cannot find the bundled `client_public`
assets. This affects server/UI launch more than indexing, but it often appears
immediately after preprocessing finishes.

Recovery:

- Reinstall Semantra from a distribution that includes package data.
- If working from a source checkout, ensure the frontend assets exist in the
  installed package data before starting the server.
- Continue with [interactive-search troubleshooting](../../interactive-search/references/troubleshooting.md).
