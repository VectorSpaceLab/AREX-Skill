---
name: flash-indexing
description: "Guides PageIndex Flash PDF extraction, embedded bookmark handling,
  and no-LLM or merge-only optimization."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Flash PDF Indexing

Use this sub-skill when the user mentions `--flash`, `page_index_flash`, fast PDF structure extraction, no-LLM outlines, embedded bookmarks, merge-only optimization, or tree-cost planning.

Do not use it for:

- classic TOC-recovery PDF extraction -> use `../pdf-indexing/`
- Markdown files -> use `../markdown-indexing/`
- workspace retrieval or agent tools -> use `../retrieval-client/`

## Required context

Read these shared references as needed:

- `../../references/workflows.md#flash-pdf-extraction` for end-to-end recipes.
- `../../references/api-reference.md#pageindex-flash` for the verified signature.
- `../../references/cli-reference.md#bundled-pageindex-cli-wrapper` and `../../references/cli-reference.md#standalone-tree-optimization-module` for flags.
- `../../references/data-formats.md#pdf--flash-tree-nodes` for output fields.
- `../../references/troubleshooting.md#flash-pdf-extraction` for PDF/TOC/optimization failures.

## Operating flow

1. For no-LLM structure extraction, run:

   ```bash
   python ../../scripts/pageindex_cli.py --pdf_path document.pdf --flash --no-summary --no-embedded-toc
   ```

2. Leave embedded bookmark handling on when PDF bookmarks are likely useful:

   ```bash
   python ../../scripts/pageindex_cli.py --pdf_path document.pdf --flash --no-summary
   ```

3. Add deterministic merge-only optimization without model calls:

   ```bash
   python ../../scripts/pageindex_cli.py --pdf_path document.pdf --flash --optimize merge --no-summary
   ```

4. Use full optimization only when an LLM key and budget are available:

   ```bash
   python ../../scripts/pageindex_cli.py --pdf_path document.pdf --flash --optimize full --model gpt-4o-2024-11-20
   ```

5. For a local PDF smoke check, run `python scripts/flash_smoke.py document.pdf` from this sub-skill directory.

## API notes

`page_index_flash` is imported from `pageindex.flash`, not from the top-level package:

```python
from pageindex.flash import page_index_flash

tree = page_index_flash("document.pdf", summary=False, use_embedded_toc=False)
```

Useful settings:

- `summary=False` avoids summary model calls.
- `use_embedded_toc=False` disables bookmark consumption.
- `optimize=True, optimize_expand=False` runs merge-only optimization.
- `optimize=True, optimize_expand=True` may call an LLM to propose subsection expansions.

## Important behavior

- Flash validates that input paths are real PDF files and rejects encrypted/password-protected PDFs.
- Embedded bookmarks are classified as ignored, skeleton, or full. Skeleton/full modes can repair or re-hang detected structure.
- Merge-only optimization can reduce redundant same-page frontier nodes and preserves dropped titles in `key_items`.
- Full optimization's expansion pass requires page text and model access.
