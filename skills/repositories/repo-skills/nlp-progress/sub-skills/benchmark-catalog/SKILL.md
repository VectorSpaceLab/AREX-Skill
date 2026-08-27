---
name: benchmark-catalog
description: "Helps agents find, interpret, and cite NLP-progress benchmark,
  dataset, leaderboard, model-result, SOTA, and multilingual task catalog
  material."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# benchmark-catalog

Use this sub-skill when a user asks where NLP-progress records an NLP task, dataset, benchmark, leaderboard, metric, paper/source link, code link, model result, SOTA row, or multilingual benchmark page.

NLP-progress is a static Markdown/GitHub Pages catalog, not an installable ML package. Operate on a caller-supplied content root that contains the NLP-progress Markdown pages. No accelerator, package install, or network access is required for catalog inspection.

## Fast workflow

1. Confirm the content root has `README.md` and language directories such as `english/`, `vietnamese/`, or `chinese/`.
2. Inventory pages and result-like tables with the bundled helper:
   ```bash
   python3 scripts/index_nlp_progress.py <content-root> --pretty
   python3 scripts/index_nlp_progress.py <content-root> --language english --pretty
   ```
3. Route from the README table of contents or a language directory to the relevant Markdown page, then use the heading trail to identify the task, subtask, dataset, and partition.
4. Interpret only the table under the relevant heading trail. Capture the model/system name, metric columns, paper/source link, optional code link, and any caveat text immediately around the table.
5. When answering, cite the content-root-relative page path plus heading trail, and say “as listed in NLP-progress” when you have not independently checked whether a leaderboard is current.

## References

- `references/catalog-navigation.md` — how to locate languages, task pages, headings, anchors, and citable page context.
- `references/table-semantics.md` — how to distinguish result tables from examples/statistics and interpret metrics, paper/source, code, and multi-metric layouts.
- `references/multilingual-coverage.md` — known language-directory coverage patterns, thin pages, and missing-page handling.
- `references/troubleshooting.md` — stale SOTA, missing leaderboards, malformed tables, inconsistent headings, and link/code caveats.

## Boundaries

- For machine-readable export behavior, JSON schema assumptions, or structured data extraction workflows, route to the sibling `structured-export` sub-skill.
- For contribution editing, table linting, Markdown maintenance, Jekyll preview, or site build/debug workflows, route to the sibling `content-maintenance` sub-skill.
