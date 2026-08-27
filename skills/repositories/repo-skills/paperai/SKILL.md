---
name: paperai
description: "Guides paperai workflows for indexing paper corpora, querying
  scientific articles, and generating RAG-backed Markdown, CSV, or
  PDF-annotation reports."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# paperai

`paperai` is a Python application for searching and analyzing scientific and
medical paper corpora. It combines a paperetl-style SQLite database with a
txtai embeddings index and optional LLM/RAG pipelines. Use this skill when a
task asks to build a paperai index, search indexed articles, expose enriched
search results, or generate repeatable reports.

## Install and inspect

Use Python 3.10+ and install the public package:

```bash
python -m pip install "paperai==2.6.0"
python -m pip check
# from the generated paperai skill directory
python scripts/check_install.py
```

The last command is a bundled, no-download import check; it does not load model
weights or validate a corpus. Read [references/install.md](references/install.md)
for dependency and runtime boundaries, and [references/troubleshooting.md](references/troubleshooting.md)
for cross-cutting failures.

## Route by task

- **Build or inspect an index, validate `articles.sqlite`, train static vectors,
  or export section text:** read
  [indexing](sub-skills/indexing/SKILL.md).
- **Run one-shot searches, use `paperai` shell, integrate the enriched API, or
  make a search UI:** read [querying](sub-skills/querying/SKILL.md).
- **Define YAML tasks and produce Markdown/CSV/PDF-annotation reports:** read
  [reporting](sub-skills/reporting/SKILL.md).

A normal end-to-end handoff is `indexing → querying` or
`indexing → reporting`. The generated skill contains the needed API details and
safe helpers; do not reopen the original repository's source, examples, tests,
or checkout-specific paths.

## Shared model-directory contract

Most workflows receive one directory containing `articles.sqlite` and saved
txtai artifacts (`config` or `config.json` plus model/index files). The database
is normally produced by paperetl and is not created by paperai. Validate its
tables and columns before model construction. Model identifiers can trigger
network downloads and optional GPU use; state the cache, device, data, and
runtime constraints before starting a large operation.

## Verification boundary

A successful import proves package plumbing only. Validate actual model loading,
SQLite schema compatibility, retrieval quality, report rendering, and optional
PDF annotation separately. Keep `maxsize`, `toprank`, `topn`, and report context
bounded for smoke runs. Markdown/CSV are the portable default; `ant` annotation
requires original PDFs and additional runtime support.

Read [references/repo-provenance.md](references/repo-provenance.md) before using
this skill with a changed checkout. If the commit, package version, or evidence
paths differ, refresh the repo skill instead of assuming the guidance is current.
