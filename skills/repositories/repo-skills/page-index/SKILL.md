---
name: page-index
description: "Routes PageIndex PDF, flash, Markdown, and workspace retrieval workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PageIndex

PageIndex turns PDFs and Markdown into hierarchical trees and exposes retrieval helpers for workspace-backed document Q&A.

Use this skill when the request mentions:
- generating a tree, outline, TOC, or section hierarchy from a PDF
- the fast no-LLM Flash path or embedded bookmarks
- converting Markdown headings into a tree
- optimizing an existing tree for search cost
- `PageIndexClient`, workspace storage, or document retrieval by page range
- the agentic vectorless RAG demo or tool-call based document QA

## Start here

- Install the runtime dependency set listed in `references/configuration.md`.
- Make `pageindex` importable in the current Python environment before using the bundled scripts.
- Quick import smoke: `python scripts/check_env.py`
- Main CLI help: `python scripts/pageindex_cli.py --help`

## Route map

- `sub-skills/pdf-indexing/` — classic PDF tree extraction with the LLM-assisted pipeline.
- `sub-skills/flash-indexing/` — fast PDF extraction with PageIndex Flash, embedded bookmarks, and merge-only optimization.
- `sub-skills/markdown-indexing/` — Markdown heading trees, thinning, and optional summaries.
- `sub-skills/retrieval-client/` — `PageIndexClient`, workspace persistence, page retrieval, and agentic Q&A patterns.

## Shared references

Read these when you need the full details behind a route:

- `references/workflows.md` — end-to-end workflows and the right route for each task family.
- `references/api-reference.md` — verified public APIs and signatures.
- `references/cli-reference.md` — bundled CLI wrapper and `pageindex.tree_optimize` flags.
- `references/data-formats.md` — tree JSON, workspace JSON, and Markdown semantics.
- `references/configuration.md` — model defaults, environment variables, and optional extras.
- `references/troubleshooting.md` — common failures and recovery steps.
- `references/repo-provenance.md` — staleness and source snapshot information.

## Selection hints

- PDF with TOC recovery, page-number reconciliation, summaries, or document descriptions -> `pdf-indexing`.
- Fast PDF structure from layout statistics, embedded bookmarks, or merge-only optimization -> `flash-indexing`.
- Markdown files with headings -> `markdown-indexing`.
- Workspace-backed retrieval, `get_document`, `get_document_structure`, `get_page_content`, or the agentic RAG demo -> `retrieval-client`.
- If a task mentions `--optimize`, start from `flash-indexing`; its reference material covers the merge-only and expand paths.

## Operating notes

- The package is source-first in this repository. Do not assume a pip-installable distribution exists; install the runtime dependency set from `references/configuration.md` and use the bundled scripts in a path-aware environment.
- Live LLM or agentic runs still need the user's API key and network access.
- Prefer the smallest safe workflow that matches the request.
- If the repository has changed, read `references/repo-provenance.md` before updating or refreshing the skill.
