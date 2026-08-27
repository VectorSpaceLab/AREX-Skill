---
name: document-indexing
description: "Guides Semantra text and PDF preprocessing, window configuration,
  cache artifact inspection, and no-server indexing workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Semantra Document Indexing

Use this sub-skill when the task is to prepare local text or PDF files for
Semantra, choose chunk windows, control the Semantra cache directory, inspect
cached artifacts, or troubleshoot preprocessing before the interactive web UI is
used.

## Read first

- [workflows.md](references/workflows.md) for practical indexing command
  patterns, cache-directory decisions, validation steps, and safe no-server
  workflows.
- [cache-and-data-formats.md](references/cache-and-data-formats.md) for the
  Semantra artifact filenames, JSON fields, embedding binaries, Annoy indexes,
  PDF conversion artifacts, and window tuple semantics.
- [troubleshooting.md](references/troubleshooting.md) for filename, encoding,
  PDF extraction, stale-cache, corrupt-artifact, and window-format failures.
- Run [create_tiny_corpus.py](scripts/create_tiny_corpus.py) when you need a
  tiny local text fixture to construct or smoke-test Semantra commands.
- Run [inspect_semantra_cache.py](scripts/inspect_semantra_cache.py) when you
  need a read-only summary of an existing Semantra cache directory.

## Route here when

- The user asks how to run `semantra` over one file, many files, `*.txt`, or a
  PDF collection.
- The user wants to preprocess documents without starting the browser UI; use
  `--no-server`.
- The user asks what `--windows`, `--encoding`, `--force`, `--semantra-dir`, or
  `--show-semantra-dir` means.
- The user needs to understand why Semantra reprocessed a document or which
  files appeared in the cache directory.
- The user has PDF text extraction or PDF viewer-position problems.

Route model/backend questions to
[models-and-embeddings](../models-and-embeddings/SKILL.md). Route query syntax,
result interpretation, preference tags, web API, or local server behavior to
[interactive-search](../interactive-search/SKILL.md).

## Core indexing workflow

1. Confirm that Semantra is installed and the CLI is visible. From a normal
   user environment, prefer:

   ```sh
   semantra --help
   semantra --list-models
   semantra --show-semantra-dir
   ```

2. Decide where processed artifacts should live. If the user does not care,
   let Semantra use its application cache directory. For reproducible tasks,
   pass an explicit cache directory:

   ```sh
   semantra --semantra-dir ./semantra-cache --no-server documents/*.txt
   ```

3. Choose documents. Semantra accepts one or more existing filenames. It reads
   `.pdf` files through its PDF path and treats other filenames as text using
   the selected encoding.

4. Choose a model with the sibling
   [models-and-embeddings](../models-and-embeddings/SKILL.md) sub-skill before
   launching a large job. Local transformer models may download model files the
   first time; OpenAI mode requires credentials and sends text to an external
   API.

5. Use `--no-server` for preprocessing-only jobs. Omit it when the next step is
   interactive search in the local browser UI.

6. Validate the result without relying on the source checkout:

   ```sh
   python path/to/inspect_semantra_cache.py --cache-dir ./semantra-cache
   ```

   Expect at least a config JSON, token JSON, embedding binary, and usually an
   Annoy index for each processed document/config/window combination.

## Window decisions

Semantra's default `--windows 128_0_16` means windows of 128 tokens, initial
offset 0, and a rewind/overlap of 16 tokens. The CLI accepts comma-separated
window specs:

- `128` -> `(size=128, offset=0, rewind=0)`.
- `128_0_16` -> `(size=128, offset=0, rewind=16)`.
- `64_8` -> `(size=64, offset=8, rewind=0)`.

Only the first configured window is used by the query routes in this Semantra
version; extra windows can still be processed and cached. Use smaller windows
for short, precise excerpts and larger windows for more context. Increase
rewind when important passages are often split across window boundaries.

## Cache and force rules

Semantra hashes both document content and model/window configuration. A document
can have multiple cache groups if you change model, tokens, windows, Annoy tree
count, encoding, or Semantra version. Use `--force` when the cache exists but
must be rebuilt. Before deleting artifacts, inspect the cache and identify the
matching document/config group in [cache-and-data-formats.md](references/cache-and-data-formats.md).

## PDF-specific notes

For PDFs, Semantra extracts text and stores page-position metadata used by the
web viewer. If the PDF opens but navigation/highlighting is wrong, distinguish
between:

- text extraction problems in the converted text artifact;
- page-position JSON problems;
- web API or browser rendering problems, which route to
  [interactive-search](../interactive-search/SKILL.md).

## Do not

- Do not tell future agents to open or run original repository docs, examples,
  or tests. Use the bundled references and scripts here instead.
- Do not run default local transformer indexing on sensitive or huge document
  sets until the user accepts model download/cache/runtime costs.
- Do not use OpenAI mode for private documents unless the user explicitly
  accepts the privacy and cost tradeoff.
