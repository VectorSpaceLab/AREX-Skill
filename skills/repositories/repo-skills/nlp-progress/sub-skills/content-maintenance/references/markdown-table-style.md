# Markdown table style for NLP-progress result pages

NLP-progress task pages are plain Markdown. Tables should remain readable in GitHub's Markdown preview and in the GitHub Pages site.

## Result table anatomy

A result table normally has:

- `Model`: model/system name, often with author and year.
- One or more metric columns: examples include `F1`, `Accuracy`, `BLEU`, `ROUGE-1`, `EM`, `LAS`, `UAS`, `Perplexity`, `RACE-m`, or language-direction metrics such as `EN-VI (BLEU)`.
- `Paper` or `Paper / Source`: citation/source cell, preferably an inline Markdown link.
- `Code`: optional but recommended implementation link column.

Common header examples:

```markdown
| Model | F1 | Paper / Source | Code |
| --- | :---: | --- | --- |
```

```markdown
| Model | ROUGE-1 | ROUGE-2 | ROUGE-L | METEOR | Paper / Source | Code |
| --- | :---: | :---: | :---: | :---: | --- | --- |
```

```markdown
| Model | RACE-m | RACE-h | RACE | Paper | Code |
| --- | :---: | :---: | :---: | --- | --- |
```

Older pages may use `Paper` and `Source` as separate columns. Preserve the existing page style unless the user explicitly asks for normalization.

## Alignment and spacing

- Use one header row, one separator row, then result rows.
- Center-align numeric metric columns with `:---:` or the page's existing `:-----:` style.
- Left-align text-heavy cells such as `Model`, `Paper / Source`, and `Code` with `---`.
- Keep a leading and trailing pipe on new rows even though some legacy rows omit the final pipe.
- Preserve local spacing style when editing an existing table; consistency inside one table matters more than global uniformity.

## Model cells

Use the shortest unambiguous model label:

```markdown
| BERT Large (Devlin et al., 2018) | 92.8 | [BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding](https://example.org/bert) | |
```

If a score uses a special split, training setup, or caveat, include it in the model cell or a nearby note:

```markdown
| CrossWeigh + Flair (Wang et al., 2019)♦ | 94.28 | [Paper title](https://example.org/paper) | [Official](https://example.org/code) |
```

Define symbols such as `♦` near the table if they are not already explained.

## Metric columns

- Keep metric names exactly comparable to the dataset's evaluation setting.
- Do not mix development and test scores in one column unless the table already does so and the row label makes the split clear.
- For multi-metric tables, preserve the existing metric order and sort by the primary metric used by the page.
- If metric direction is ambiguous, add a short note rather than guessing.

Typical direction defaults:

| Metric family | Direction |
| --- | --- |
| Accuracy, F1, EM, BLEU, ROUGE, METEOR, LAS, UAS, MAP, MRR, Precision, Recall | Higher is better |
| Error, WER, CER, perplexity, loss, cost, latency | Lower is better |

## Paper/source cells

Use an inline Markdown link when possible:

```markdown
[Paper title](https://example.org/paper)
```

Acceptable variants include:

- `Paper / Source`: the most common style for citation/source evidence.
- `Paper`: common on several task pages.
- `Paper` plus `Source`: legacy style where source may act like an implementation or supporting source column.

Avoid empty paper/source cells for benchmark results. If the score is from a secondary paper, make that clear in surrounding prose or in the cell.

## Code cells

Use these labels:

```markdown
[Official](https://example.org/official-code)
[Link](https://example.org/unofficial-code)
```

Rules:

- `[Official]` means the implementation is from the paper authors, dataset owners, or recognized project maintainers.
- `[Link]` means a non-official implementation or related framework link.
- Multiple code links may appear in one cell if the table already uses that style.
- Empty code cells are allowed when no implementation is available.
- Prefer adding a `Code` column to new result tables. For old tables without one, add it only if the edit scope includes code maintenance and the row count is manageable.

## Duplicate and stale-row cautions

A duplicate is usually the same model, paper/source, dataset split, and metric values. Update the existing row instead of appending a new one.

A stale row is a local entry that may no longer match an external public leaderboard. When maintaining such a table:

- Do not claim the table is complete unless the user supplied up-to-date evidence.
- Add a pointer or caveat to the leaderboard if the page already uses that pattern.
- Preserve historical rows that document published results unless the user asks for cleanup.

## Validation commands

Run the checker on changed files:

From the generated `nlp-progress` skill root:

```bash
python3 sub-skills/content-maintenance/scripts/check_nlp_progress_markdown.py path/to/changed_page.md
```

Run strict validation before final handoff when feasible:

```bash
python3 sub-skills/content-maintenance/scripts/check_nlp_progress_markdown.py --strict path/to/changed_page.md
```

Warnings are non-fatal by default so legacy pages can be maintained incrementally. `--strict` turns warnings into failures.
