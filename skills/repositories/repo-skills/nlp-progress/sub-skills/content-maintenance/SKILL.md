---
name: content-maintenance
description: "Helps maintain NLP-progress Markdown task pages by adding or
  updating datasets, benchmark results, SOTA rows, code links, table
  conventions, validation checks, and optional Jekyll previews."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# content-maintenance

Use this sub-skill when a user asks to add or update NLP-progress task pages, dataset sections, benchmark result rows, SOTA ordering, paper/source citations, code implementation links, or a local site preview for Markdown content.

NLP-progress is a static Markdown and GitHub Pages corpus. Core content maintenance is CPU/any only and does not require an ML runtime, package install, accelerator, or network access.

## Route elsewhere

- Automated JSON export, structured parsing, or `structured.json` generation belongs to `structured-export`.
- Domain benchmark discovery, benchmark lookup, or deciding what the current SOTA should be from external sources belongs to `benchmark-catalog`.

## Operating procedure

1. Identify the target language/task Markdown page and whether the change is a result row, dataset section, or new task page.
2. Apply the bundled contribution policy in [references/contribution-guidelines.md](references/contribution-guidelines.md).
3. Preserve table conventions from [references/markdown-table-style.md](references/markdown-table-style.md), including `Model`, metric columns, `Paper` or `Paper / Source`, and optional `Code` cells.
4. For new datasets, include description, evaluation setting/metric, annotated example, download link when available, and at least two results including the SOTA result.
5. Keep result tables sorted with the best result on top, while checking metric direction before moving rows.
6. Validate changed Markdown with the bundled checker before handoff. From the generated `nlp-progress` skill root, run:

   ```bash
   python3 sub-skills/content-maintenance/scripts/check_nlp_progress_markdown.py <changed-file-or-directory>
   python3 sub-skills/content-maintenance/scripts/check_nlp_progress_markdown.py --strict <changed-file-or-directory>
   ```

   From this sub-skill directory, the equivalent path is `python3 scripts/check_nlp_progress_markdown.py ...`.

7. If the user explicitly asks for a rendered preview, use the optional Jekyll notes in [references/site-preview.md](references/site-preview.md). Do not make Ruby/Bundler setup part of normal content validation.
8. If validation or rendering fails, use [references/troubleshooting.md](references/troubleshooting.md) to triage contribution, editor, build, and table issues.

## Handoff checklist

- State which Markdown pages changed and what task/dataset/result each change affects.
- State the source basis for each new result: paper/preprint, benchmark split, metric name, and code link status.
- State how sorting was decided, including whether higher or lower metric values are better.
- Report checker command(s), warnings, and whether `--strict` passed.
- Mention any stale leaderboard caveat, missing download link, missing code link, or unavailable optional Jekyll preview.
