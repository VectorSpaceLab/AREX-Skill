# Troubleshooting content-maintenance issues

Use this guide when a Markdown edit, checker run, or optional site preview fails.

## Contribution and scope issues

**Problem: The requested update is only a benchmark lookup.**
Route benchmark discovery and SOTA research to `benchmark-catalog`. This sub-skill applies accepted evidence to Markdown content; it does not decide the domain benchmark from scratch.

**Problem: The user asks for machine-readable JSON export.**
Route automated export and structured parsing to `structured-export`.

**Problem: A dataset has only the introducing paper.**
Do not present it as an accepted dataset addition unless the user supplies evidence that at least one other published paper evaluated on it, or explicitly accepts documenting an exception.

**Problem: The page already points to a public leaderboard.**
Prefer updating the pointer or adding a caveat over copying many rows that may become stale. If adding rows anyway, state the date/evidence basis in the handoff.

## Editor and navigation issues

**Problem: A new task page is not discoverable.**
Add it to the top-level task list using the language directory's existing link style. Check relative links from the page back to the repository root or neighboring pages.

**Problem: Heading levels become inconsistent.**
Mirror the page's local hierarchy. Task pages often use a top `#` title, dataset sections with `###`, and subdataset variants with `####`, but language aggregation pages may use `##` task sections.

**Problem: A new dataset section is too thin.**
Add the required elements: dataset/task description, references, evaluation metric/setting, annotated example, download/access link when available, and at least two results including SOTA.

## Table validation issues

Run:

From the generated `nlp-progress` skill root:

```bash
python3 sub-skills/content-maintenance/scripts/check_nlp_progress_markdown.py <changed-file-or-directory>
```

From this sub-skill directory, use `python3 scripts/check_nlp_progress_markdown.py <changed-file-or-directory>`.

Use `--strict` before final handoff when feasible.

**Error: result table missing `Model`.**
Add a `Model` column or confirm that the table is not a result/SOTA table. Example/data-stat tables do not need `Model`.

**Error: result table missing `Paper` or `Paper / Source`.**
Add a citation/source column. For legacy pages, `Paper` is acceptable; `Paper / Source` is the common style.

**Warning: result table missing `Code`.**
Add a `Code` column when the edit includes implementations or when creating a new table. For legacy tables, this warning can be left unresolved unless the user requests strict cleanup.

**Error: malformed or empty Markdown link.**
Fix links with empty labels or URLs. Use `[Official](https://example.org/code)` or `[Paper title](https://example.org/paper)`, not `[](...)`, `[Title]()`, or an unclosed `[Title](...)` link.

**Warning: duplicate row.**
Compare model, paper/source, split, and metric values. Update the existing row if the new evidence refers to the same result.

**Warning or render issue: row has the wrong number of cells.**
Check for missing trailing pipes, unescaped pipes inside text, or a code/paper title containing `|`. Escape literal pipes as `\|` or rewrite the text.

**Problem: sorting is disputed.**
Check metric direction. Higher is normally better for F1, accuracy, BLEU, ROUGE, EM, LAS, UAS, MAP, MRR, precision, and recall. Lower is normally better for error rate, WER, CER, perplexity, loss, latency, or cost. For multi-metric tables, preserve the page's existing primary sort convention.

## Optional Jekyll preview issues

**Problem: Ruby is missing or too old.**
Skip preview for Markdown-only changes, or ask the user for permission to install/activate a suitable Ruby runtime if preview is required.

**Problem: `bundle install` fails.**
Common causes are no network access, RubyGems TLS problems, unavailable native headers, or incompatible local Ruby. Report it as an optional preview blocker unless the user required a rendered preview.

**Problem: `bundle exec jekyll serve` fails with a busy port.**
Retry with another port, for example `--port 4001`, or stop the old server process.

**Problem: Liquid include rendering fails.**
Check whether the edit changed include syntax, score names, or data passed to a table/chart include. Most content updates should remain plain Markdown and should not touch include templates.

## Handoff when issues remain

Report unresolved issues explicitly:

- Which file and line are affected.
- Whether the issue is a fatal Markdown/content problem or only an optional preview problem.
- What evidence or user decision is missing.
- Whether `--strict` failed only because of legacy warnings such as missing `Code` columns.
