---
name: markdown-indexing
description: "Guides PageIndex Markdown-to-tree conversion, heading parsing,
  thinning, and optional summaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Markdown Indexing

Use this sub-skill when the user wants to convert `.md` or `.markdown` files into PageIndex trees, reason about heading parsing, use `md_to_tree`, enable tree thinning, or troubleshoot line-number based retrieval.

Do not use it for:

- PDF files -> use `../pdf-indexing/` or `../flash-indexing/`
- workspace retrieval after indexing -> use `../retrieval-client/`

## Required context

Read these shared references as needed:

- `../../references/workflows.md#markdown-tree-extraction` for CLI and API recipes.
- `../../references/api-reference.md#markdown-tree-extraction` for the verified `md_to_tree` signature.
- `../../references/data-formats.md#markdown-tree-output` for line-number output shape.
- `../../references/troubleshooting.md#markdown-extraction` for heading and summary failures.
- `../../references/configuration.md#offline-friendly-modes` for no-LLM settings.

## Operating flow

1. Prefer explicit no-summary flags when the user only needs structure:

   ```bash
   python ../../scripts/pageindex_cli.py --md_path notes.md --if-add-node-summary no --if-add-doc-description no
   ```

2. Enable thinning only when the user has many small sections:

   ```bash
   python ../../scripts/pageindex_cli.py --md_path notes.md --if-thinning yes --thinning-threshold 5000 --if-add-node-summary no
   ```

3. Use the async API from synchronous code with `asyncio.run`:

   ```python
   import asyncio
   from pageindex import md_to_tree

   result = asyncio.run(md_to_tree("notes.md", if_add_node_summary="no"))
   ```

4. For an offline smoke check, run `python scripts/markdown_smoke.py` from this sub-skill directory.

## Heading rules

- ATX headings (`#`, `##`, ... `######`) become nodes at their matching levels.
- Non-empty bold-only lines (`**Heading**`) become level-1 nodes.
- Empty bold-only headings are ignored.
- Fenced code blocks suppress heading detection until the closing fence.
- Markdown output uses `line_num`, not PDF page indexes.

## Common decisions

- If the user asks for retrieval after conversion, route to `../retrieval-client/` after generating or loading the workspace.
- If model keys are unavailable, turn off `if_add_node_summary` and `if_add_doc_description`.
- If the tree is too granular, use thinning; if content disappears, lower the thinning threshold or disable thinning.
