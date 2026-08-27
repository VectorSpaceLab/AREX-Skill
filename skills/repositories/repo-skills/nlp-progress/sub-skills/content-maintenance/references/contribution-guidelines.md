# Contribution guidelines for NLP-progress content maintenance

Use these rules when adding or updating static Markdown task pages, dataset sections, result rows, and code links.

## Source quality rules

- Prefer results reported in published papers.
- Influential preprints may be acceptable, but mark the source clearly and avoid presenting unverifiable claims as settled leaderboard facts.
- A dataset should have been used for evaluation in at least one published paper besides the paper that introduced the dataset.
- If an actively maintained public leaderboard already exists for a task or dataset, prefer pointing readers to that leaderboard or add a caveat that the local table may become stale.

## Updating an existing result table

1. Confirm the table is the correct task, dataset, split, language, and evaluation setting.
2. Record the model name in the `Model` cell. The common style is `Model (Author et al., Year)` or a short system name when the table already uses one.
3. Fill metric columns exactly as named in the header. Do not rename existing metrics unless the whole table is being deliberately normalized.
4. Put the citation in `Paper` or `Paper / Source` as an inline Markdown link when a stable paper/source URL is available.
5. Use a `Code` column when the table has one. If no implementation is available, leave the cell empty.
6. Label an official implementation as `[Official](https://example.org/project)`.
7. Label an unofficial implementation as `[Link](https://example.org/project)` unless the table already uses a more specific non-official label.
8. Keep the best result at the top of the table. Check whether the metric is higher-is-better or lower-is-better before moving rows.
9. Avoid duplicate rows for the same model, paper, split, and metric values. If a new paper reports the same model under a different setting, make the distinction visible in the model name or surrounding note.
10. Validate the changed file with the bundled checker before handoff.

## Adding a new dataset under an existing task

A new dataset section should be self-contained enough for a reader to understand what is being evaluated:

1. Add the dataset under the relevant task section, preserving the page's heading level and local ordering convention.
2. Briefly describe the dataset/task and cite relevant references.
3. Describe the evaluation setting and evaluation metric. Include split names if they affect comparability.
4. Include an annotated example when the dataset format is not obvious.
5. Add a download link when one is available. If access is restricted, state that directly instead of inventing a public link.
6. Add a result table with at least two results, including the state-of-the-art result known from the accepted source set.
7. Include `Model`, one or more metric columns, `Paper` or `Paper / Source`, and preferably `Code`.

Template:

```markdown
### Dataset name

Short dataset description, provenance, scale, evaluation split, and metric direction.

Example:

| Input | Label |
| --- | --- |
| Example text | Example annotation |

Links: dataset page or download URL when available.

| Model | Score | Paper / Source | Code |
| --- | :---: | --- | --- |
| Model A (Author et al., 2024) | 91.2 | [Paper title](https://example.org/paper) | [Official](https://example.org/code) |
| Model B (Author et al., 2023) | 89.7 | [Paper title](https://example.org/previous) | |
```

## Adding a new task page

1. Create a new Markdown page in the appropriate language directory using the repository's existing lowercase, underscore-separated filename style unless the language directory already uses another style.
2. Add the new page to the top-level task list so readers can navigate to it.
3. Start the page with a task heading, a concise task definition, and any necessary examples.
4. Add dataset sections using the new-dataset checklist above.
5. Add a back-navigation link only if neighboring pages in that language directory use one.
6. Validate the new page and the edited navigation file with the bundled checker.

## Result sorting and metric direction

- Accuracy, F1, BLEU, ROUGE, METEOR, EM, LAS, UAS, MAP, MRR, precision, recall, and hit-rate style metrics are normally higher-is-better.
- Error rate, word error rate, character error rate, perplexity, loss, and runtime/cost metrics are normally lower-is-better.
- Some tables mix metrics or splits. Sort by the page's existing primary metric convention and avoid reordering historical rows if the table does not have a clear primary metric.
- If the table delegates to a public leaderboard, do not overstate the local rows as exhaustive or current.

## Validation checklist

Before handoff, verify:

- The target page, heading, dataset, split, and language are correct.
- New datasets include description, metric, example, download/access note, and at least two results including SOTA.
- Result tables include `Model` and `Paper` or `Paper / Source`.
- `Code` cells use `[Official](url)` for official code and `[Link](url)` for unofficial code.
- Empty `Code` cells are acceptable when no implementation is available.
- Markdown links have non-empty labels and URLs.
- No duplicate rows were introduced.
- The table remains sorted with the best result on top for the chosen metric direction.
