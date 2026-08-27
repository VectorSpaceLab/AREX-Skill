# NLP-progress corpus overview

## Repository identity

NLP-progress tracks progress in Natural Language Processing by collecting benchmark datasets, evaluation metrics, model/result tables, paper/source links, and optional code links in plain Markdown. The public site is served with GitHub Pages/Jekyll, but most operating tasks are Markdown-only.

The repository is not a Python package. Treat it as a versioned content corpus plus a small structured export utility.

## Source corpus shape

Core evidence lives in language directories:

| Language directory | Markdown task pages | Result-like table headers observed | Notes |
| --- | ---: | ---: | --- |
| `english/` | 39 | 416 | Broadest coverage: QA, language modeling, semantic parsing, summarization, NER, dialogue, parsing, sentiment, GEC, and many others. |
| `vietnamese/` | 1 | 35 | One multi-task language page with H2 task sections and H3/H4 datasets or directions. |
| `chinese/` | 3 | 13 | General Chinese NLP page plus word segmentation and QA; README also points to an external Chinese NLP site. |
| `bengali/` | 4 | 3 | POS tagging, emotion detection, QA, and sentiment. |
| `persian/` | 3 | 8 | NER, NLI, and summarization. |
| `spanish/` | 3 | 7 | Entity linking, NER, and summarization. |
| `russian/` | 3 | 2 | QA, sentiment, and summarization. |
| `french/` | 2 | 4 | QA and summarization. |
| `german/` | 2 | 1 | QA and summarization. |
| `hindi/` | 1 | 5 | One multi-task page. |
| `arabic/`, `korean/`, `nepali/`, `portuguese/`, `turkish/` | 1 each | 0-3 each | Thin focused coverage; verify whether a numeric local table exists. |

The generated skill's benchmark helper can recompute exact counts for a caller's current content root:

```bash
python3 sub-skills/benchmark-catalog/scripts/index_nlp_progress.py <content-root> --pretty
```

## Support files

| Source evidence | Role in this skill |
| --- | --- |
| `README.md` | Top-level language/task navigation, project purpose, contribution rules, table template, export/Jekyll pointers, wish list. |
| `structured/README.md` | Official export evidence: Python 3.6+ standard-library utility, path arguments, default `structured.json`, optional `--output`; runtime use is through the bundled exporter in this skill. |
| `structured/export.py` | Source for bundled `sub-skills/structured-export/scripts/export_nlp_progress.py`. |
| `structured/requirements.txt` | Empty; confirms the export path has no third-party Python requirements. |
| `Gemfile`, `jekyll_instructions.md`, `_includes/table.html`, `_includes/chart.html` | Optional site-preview and Liquid rendering evidence for content-maintenance notes. |
| `CITATION.cff`, `LICENSE` | Citation/license/provenance evidence. |

## Evidence exclusions

- `.git/` is VCS metadata and not runtime skill content.
- `img/` contains contribution screenshots; the skill distills the contribution flow in prose instead of bundling images.
- `skills/` contains generated production artifacts and review/test reports; it is excluded from source extraction.
- Ruby/Jekyll dependencies are optional for preview only and are not needed for benchmark lookup, export, or Markdown validation.

## Capability mapping

| Capability | Owner |
| --- | --- |
| Locate language/task/dataset pages and cite benchmark rows | `benchmark-catalog` |
| Interpret headings, table columns, metric direction, paper/source links, and code links | `benchmark-catalog` |
| Export Markdown pages/directories to JSON | `structured-export` |
| Explain export schema and parser edge cases | `structured-export` |
| Add/update result rows, datasets, task pages, and code links | `content-maintenance` |
| Validate Markdown table/link style | `content-maintenance` |
| Optional Jekyll preview and build troubleshooting | `content-maintenance` |
