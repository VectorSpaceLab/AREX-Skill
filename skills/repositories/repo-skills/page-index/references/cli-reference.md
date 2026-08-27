# CLI Reference

Use the bundled wrapper `scripts/pageindex_cli.py` instead of depending on a source checkout script path.

## Bundled PageIndex CLI wrapper

```bash
python scripts/pageindex_cli.py --help
```

### Classic PDF tree extraction

```bash
python scripts/pageindex_cli.py --pdf_path document.pdf
python scripts/pageindex_cli.py --pdf_path document.pdf --model gpt-4o-2024-11-20
python scripts/pageindex_cli.py --pdf_path document.pdf --if-add-node-summary no --if-add-doc-description no
```

### Flash PDF extraction

```bash
python scripts/pageindex_cli.py --pdf_path document.pdf --flash --no-summary
python scripts/pageindex_cli.py --pdf_path document.pdf --flash --optimize merge --no-summary
python scripts/pageindex_cli.py --pdf_path document.pdf --flash --optimize full --model gpt-4o-2024-11-20
```

### Markdown tree extraction

```bash
python scripts/pageindex_cli.py --md_path notes.md --if-add-node-summary no
python scripts/pageindex_cli.py --md_path notes.md --if-thinning yes --thinning-threshold 5000
```

The wrapper writes output JSON to `./results/`:

- PDF classic: `<pdf-name>_structure.json`
- PDF Flash: `<pdf-name>_structure_flash.json`
- Markdown: `<md-name>_structure.json`

## Common wrapper flags

| Flag | Applies to | Meaning |
| --- | --- | --- |
| `--pdf_path` | PDF modes | Input PDF path. Must end in `.pdf`. |
| `--md_path` | Markdown mode | Input Markdown path. Must end in `.md` or `.markdown`. |
| `--flash` | PDF only | Use PageIndex Flash. |
| `--embedded-toc` / `--no-embedded-toc` | Flash only | Consume PDF bookmarks when trustworthy. Default is on with Flash. |
| `--summary` / `--no-summary` | Flash only | Generate node summaries. Default is on with Flash; use `--no-summary` for offline structure extraction. |
| `--optimize [{full,merge}]` | Flash PDF only | `merge` is deterministic and no-LLM; `full` also runs LLM expansion. |
| `--model` | All model-backed modes | Override the configured model. |
| `--summary-model` | Flash summaries | Use a separate model for node summaries. |
| `--toc-check-pages` | Classic PDF | Number of early pages to inspect for a TOC. |
| `--max-pages-per-node` | Classic PDF | Maximum page span before recursive splitting. |
| `--max-tokens-per-node` | Classic PDF | Maximum token span before recursive splitting. |
| `--if-add-node-id` | Classic PDF / Markdown | `yes` or `no`; controls `node_id`. |
| `--if-add-node-summary` | Classic PDF / Markdown | `yes` or `no`; summaries need an LLM. |
| `--if-add-doc-description` | Classic PDF / Markdown | `yes` or `no`; doc descriptions need summaries/model access. |
| `--if-add-node-text` | Classic PDF / Markdown | `yes` or `no`; controls whether node text remains in output. |
| `--if-thinning` | Markdown only | `yes` applies tree thinning before tree construction. |
| `--thinning-threshold` | Markdown only | Minimum token threshold for thinning. |
| `--summary-token-threshold` | Markdown only | Token threshold for summary generation. |

## Standalone tree optimization module

The installed/source package also exposes a module CLI:

```bash
python -m pageindex.tree_optimize --pdf document.pdf --structure tree.json --plan
python -m pageindex.tree_optimize --pdf document.pdf --structure tree.json --no-expand --out optimized.json
python -m pageindex.tree_optimize --pdf document.pdf --structure tree.json --log optimize-log.json
```

Important flags:

- `--plan` prints metrics and candidate decisions without API calls.
- `--no-expand` runs merge-only optimization and avoids LLM expansion.
- `--no-merge` disables deterministic merge.
- `--trigger-pages` changes the page-span threshold for considering expansion.
- `--routing` changes the cost of visiting a node in the search-cost model.
- `--headings` passes an optional cached per-page heading-detection file.
- `--model` controls the expansion model when expansion is enabled.

Use `--plan` or `--no-expand` when no API key is available.
