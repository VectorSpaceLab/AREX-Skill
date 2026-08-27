# PageIndex Workflows

## Route selection

| User task | Start with |
| --- | --- |
| Build a tree from a PDF with TOC recovery or summaries | `sub-skills/pdf-indexing/` |
| Build a fast PDF tree without an LLM | `sub-skills/flash-indexing/` |
| Convert Markdown headings to a tree | `sub-skills/markdown-indexing/` |
| Retrieve document metadata, structure, or page content from a workspace | `sub-skills/retrieval-client/` |
| Optimize a tree or inspect search cost | `sub-skills/flash-indexing/` plus the tree optimization section below |

## Classic PDF tree extraction

Use this path when the user wants the original LLM-assisted PageIndex pipeline: TOC detection, TOC transformation, page-number reconciliation, recursive splitting, summaries, and document descriptions.

1. Ensure `pageindex` imports and model credentials are available.
2. Run the bundled CLI wrapper:

   ```bash
   python scripts/pageindex_cli.py --pdf_path document.pdf
   ```

3. Override models and size thresholds when needed:

   ```bash
   python scripts/pageindex_cli.py \
     --pdf_path document.pdf \
     --model gpt-4o-2024-11-20 \
     --toc-check-pages 20 \
     --max-pages-per-node 10 \
     --max-tokens-per-node 20000
   ```

4. Control output density:

   ```bash
   python scripts/pageindex_cli.py \
     --pdf_path document.pdf \
     --if-add-node-summary yes \
     --if-add-doc-description yes \
     --if-add-node-text no
   ```

Output is written as `./results/<pdf-name>_structure.json`.

Notes:

- Classic PDF extraction uses LLM calls even when node summaries are disabled, because TOC detection/transformation and verification are model-backed.
- Use Flash with `--no-summary` when the user explicitly needs an offline no-LLM tree.
- Page indexes in output are physical PDF pages, 1-based and inclusive.

## Flash PDF extraction

Use this path when speed, no-LLM structure extraction, embedded bookmarks, or deterministic merge-only optimization matter.

Structure-only extraction:

```bash
python scripts/pageindex_cli.py --pdf_path document.pdf --flash --no-summary --no-embedded-toc
```

Embedded bookmarks enabled (default with Flash):

```bash
python scripts/pageindex_cli.py --pdf_path document.pdf --flash --no-summary
```

Merge-only optimization, still no LLM:

```bash
python scripts/pageindex_cli.py --pdf_path document.pdf --flash --optimize merge --no-summary
```

Full optimization with expansion and summaries, model-backed:

```bash
python scripts/pageindex_cli.py --pdf_path document.pdf --flash --optimize full --model gpt-4o-2024-11-20
```

API use:

```python
from pageindex.flash import page_index_flash

tree = page_index_flash("document.pdf", summary=False, use_embedded_toc=False)
optimized = page_index_flash(
    "document.pdf",
    summary=False,
    optimize=True,
    optimize_expand=False,
)
```

Output is written as `./results/<pdf-name>_structure_flash.json` when using the bundled CLI.

## Markdown tree extraction

Use this path for `.md` or `.markdown` files with explicit headings.

Offline structure-only CLI:

```bash
python scripts/pageindex_cli.py --md_path notes.md --if-add-node-summary no --if-add-doc-description no
```

Markdown thinning:

```bash
python scripts/pageindex_cli.py \
  --md_path notes.md \
  --if-thinning yes \
  --thinning-threshold 5000 \
  --if-add-node-summary no
```

Async API use:

```python
import asyncio
from pageindex import md_to_tree

result = asyncio.run(md_to_tree(
    md_path="notes.md",
    if_thinning=False,
    if_add_node_summary="no",
    if_add_doc_description="no",
    if_add_node_text="no",
))
```

Markdown tree nodes use `line_num`, not PDF page ranges. See `data-formats.md`.

## Workspace retrieval and agentic Q&A

Use this path when the user wants document metadata, structure, page content, or an agent tool pattern.

```python
from pageindex import PageIndexClient

client = PageIndexClient(workspace="workspace")
doc_id = client.index("document.pdf")
print(client.get_document(doc_id))
print(client.get_document_structure(doc_id))
print(client.get_page_content(doc_id, "5-7"))
```

Important boundaries:

- `PageIndexClient.index()` calls the PDF or Markdown tree builders and may need model credentials.
- Loading an existing workspace and retrieving cached structure/page content can be offline.
- For agentic Q&A, expose three tools: `get_document`, `get_document_structure`, and `get_page_content`. Fetch tight page ranges; do not request the entire document text.
- The OpenAI Agents SDK demo pattern requires the optional `openai-agents` dependency and a model key.

## Standalone tree optimization

Use the module CLI for an existing tree JSON:

```bash
python -m pageindex.tree_optimize --pdf document.pdf --structure tree.json --plan
python -m pageindex.tree_optimize --pdf document.pdf --structure tree.json --no-expand --out optimized.json
```

Use `--plan` to inspect complexity and candidates without mutating outputs. Use `--no-expand` to avoid LLM calls. Expansion needs page text and a configured model.

## Bundled smoke helpers

- `python scripts/check_env.py` — import/signature smoke.
- `python sub-skills/flash-indexing/scripts/flash_smoke.py document.pdf` — no-LLM Flash plus merge-only optimization on a local PDF.
- `python sub-skills/markdown-indexing/scripts/markdown_smoke.py` — no-LLM Markdown conversion on a synthetic fixture.
- `python sub-skills/retrieval-client/scripts/workspace_smoke.py` — offline `PageIndexClient` retrieval over a synthetic workspace.
