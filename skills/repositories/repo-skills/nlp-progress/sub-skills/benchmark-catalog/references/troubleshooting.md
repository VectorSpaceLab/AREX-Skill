# Troubleshooting benchmark-catalog tasks

## The task or language is not in the README

- Inventory the content root with `python3 scripts/index_nlp_progress.py <content-root> --pretty` from this sub-skill directory.
- Search language directories directly; some files may be present even if the README table of contents is sparse or stale.
- If no page exists, report that the requested task/language is not covered in this NLP-progress snapshot rather than inventing a benchmark.

## A README anchor does not resolve

Older anchors can drift when headings are renamed. Search for the visible heading text in the target page. If the heading has punctuation or slash characters, try a normalized GitHub-style anchor by lowercasing, removing punctuation, and replacing spaces with hyphens.

## A heading looks like a dataset but is not one

Headings such as `Table of contents`, `Warning: Evaluation Metrics`, `Task`, `Evaluation`, `Metrics`, `Systems`, `Datasets`, and `References` are often structural. Check nearby prose and table headers before treating them as a benchmark.

## A result table seems malformed

Symptoms:

- Header lacks `Model`.
- Header lacks `Paper` or `Paper / Source`.
- Row has fewer cells than the header.
- Markdown link labels or URLs are empty.

Use the `content-maintenance` checker if the user is editing the page. For read-only catalog answers, preserve the ambiguity and cite the exact row/context rather than silently normalizing it.

## A page has several metrics or splits

Do not compare rows across splits or metrics unless the user asked for that comparison and the metric direction is clear. Keep separate score columns visible in the answer. For lower-is-better metrics such as WER, CER, perplexity, loss, latency, or cost, the top row may not follow a higher-is-better convention.

## The table may be stale

NLP-progress is a curated static repository. If a page points to a public leaderboard, prefer the leaderboard for current standings. When network access is not available, phrase the answer as “NLP-progress lists…” and include a stale-data caveat.

## Code links are missing or ambiguous

An empty `Code` cell means no implementation is listed in the page, not that no implementation exists. `[Official]` indicates an author/project-maintained implementation when used consistently; `[Link]` is usually unofficial or related. If code provenance matters, verify it outside NLP-progress before relying on it.

## The content root is incomplete

If the index helper reports no `README.md` or no language Markdown files, the user may have supplied a subdirectory or a partial copy. Ask for the repository/content root or run the helper on the parent directory. The sub-skill itself does not need the original production checkout, only the user's content root.
