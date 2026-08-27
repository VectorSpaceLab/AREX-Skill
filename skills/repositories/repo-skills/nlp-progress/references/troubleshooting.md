# Cross-cutting troubleshooting

## Wrong route

- If the user asks “where is this benchmark/result/task?”, route to `benchmark-catalog`.
- If the user asks for `structured.json`, JSON schema, parser behavior, or export warnings, route to `structured-export`.
- If the user asks to edit Markdown, add a result, validate a table, or preview the site, route to `content-maintenance`.

## Content root is missing or partial

Symptoms:

- Inventory helper reports no `README.md`.
- No language directories are found.
- Export output is an empty list.
- A path such as `english/` is not found.

Recovery:

1. Ask for the NLP-progress content root or verify the current working directory.
2. Check for `README.md` and at least one language directory.
3. If the user supplied a subdirectory, run catalog/export helpers on that subdirectory only when that narrow scope is intentional.
4. Use content-root-relative paths in answers so the user can reproduce them.

## Static SOTA may be stale

NLP-progress is a static curated snapshot. Some pages link to external leaderboards that may be more current. When recency matters and no live external check was performed, answer with language such as “NLP-progress lists...” and include the page/heading trail.

Do not infer current global SOTA from a local row without checking the benchmark's official leaderboard or current literature when the user requires recency.

## No Python package import exists

There is no `import nlp_progress` package and no editable package install. Python use in this skill is limited to bundled standard-library helper scripts. If a user asks for installation, explain:

- For lookup/edit/export: Python 3 is enough for helper scripts.
- For optional local site preview: Ruby, Bundler, and GitHub Pages gems may be needed.
- ML frameworks, model weights, CUDA, ROCm, MPS, and dataset downloads are unrelated to this repository.

## Optional Jekyll preview fails

Ruby/Bundler/GitHub Pages preview is optional and network-sensitive. Treat failures as preview blockers, not as benchmark lookup/export/edit blockers, unless the user explicitly required rendered-site validation. Use the content-maintenance site-preview reference for concrete commands and recovery.

## Bundled script path confusion

When running helpers from the generated `nlp-progress` skill root, use paths such as:

```bash
python3 sub-skills/benchmark-catalog/scripts/index_nlp_progress.py <content-root> --pretty
python3 sub-skills/structured-export/scripts/export_nlp_progress.py <paths> --output structured.json
python3 sub-skills/content-maintenance/scripts/check_nlp_progress_markdown.py <changed-file-or-directory>
```

When running from a sub-skill directory, use that sub-skill's local `scripts/...` path. Do not call original source repository scripts as runtime dependencies.

## JSON export and Markdown validation disagree

The maintenance checker and structured exporter have different purposes:

- The checker warns about Markdown table/link hygiene and can run recursively.
- The exporter preserves the repository's simple parser assumptions and scans directory inputs only one level deep.

If the checker passes but JSON is missing a table, read `structured-export/references/parser-assumptions.md`: the table may lack `Model`, lack `Paper`/`Paper / Source`, be under an unsupported heading level, or have leading spaces before `|`.

If JSON export succeeds but the checker warns, decide whether the warning is legacy style, missing optional `Code`, duplicate rows, or a real content-quality problem.
