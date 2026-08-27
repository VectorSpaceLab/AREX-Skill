# Table semantics

NLP-progress pages mix benchmark result tables, examples, dataset statistics, and prose-only leaderboards. This reference explains how to distinguish and interpret them.

## Result-like/SOTA table pattern

A result-like table usually has:

- A model/system column, commonly named `Model`, `System`, `Annotator`, or similar.
- One or more metric columns, such as `Accuracy`, `F1`, `F1-score`, `EM`, `BLEU`, `ROUGE-1`, `ROUGE-L`, `METEOR`, `Perplexity`, `BPC`, `LAS`, `UAS`, `Smatch`, `Error`, or dataset-specific split columns.
- A paper/source column, commonly `Paper / Source`, `Paper`, `Source`, or `Reference`.
- Optional `Code`, `Github`, `Implementation`, or `Note` columns.

A result-like table is interpreted only within its enclosing heading trail. The row at the top is often intended to be the best or most recent known result, but this is not guaranteed. Some pages explicitly say results are chronological, and older pages may be unsorted.

## Tables that are not SOTA results

Do not treat these as model-result tables unless the user explicitly asks for examples or dataset structure:

- Dataset examples: tables such as `Passage | Question | Answer` or `Question | SQL query`.
- Dataset-size summaries: tables with rows such as `# Train`, `# Dev`, `# Test`.
- Local table-of-contents or checklist tables.
- Bullet lists of systems without numeric result columns.
- Tables that contain only data fields and no model/system or paper/source context.

When uncertain, call a table “example/statistics” rather than “SOTA”. The bundled script reports both total table count and result-like table count so ambiguous pages can be reviewed manually.

## Metric direction and comparability

Always infer metric direction from nearby prose or conventional metric meaning before declaring a winner.

Usually higher is better:

- Accuracy, sentence accuracy, Exact Match, F1, macro/micro F1, BLEU, ROUGE, METEOR, LAS, UAS, Smatch, labeled F1, precision, and recall.

Usually lower is better:

- Perplexity, bits per character (BPC), error, error rate, RMSE, runtime, and parameter count when used as an efficiency measure.

If a table has multiple metrics, do not collapse it to one SOTA claim unless the requested metric is specified. For example:

- Question answering pages may use F1 and EM together.
- RACE has `RACE-m`, `RACE-h`, and overall `RACE` columns.
- SearchQA has unigram accuracy, n-gram F1, EM, and F1 in one table.
- Semantic dependency parsing has multiple formalisms and domains (`DM ID`, `DM OOD`, `PAS ID`, `PAS OOD`, `PSD ID`, `PSD OOD`).
- Summarization tables often list ROUGE and METEOR; warning sections caution that automatic metrics are limited.

Treat missing cells (`-`, `--`, empty cells, `?`) as not reported, not as zero. Preserve units and annotations such as `uncased`, `ensemble`, `preprint`, `under review`, dynamic evaluation markers, or footnotes.

## Multi-dataset and multi-subdataset tables

Some result tables encode multiple datasets or partitions in columns rather than headings. Examples include CNN/Daily Mail, RACE, Penn Treebank validation/test, IWSLT test sets, and Chinese word segmentation datasets.

For these tables:

1. Record the enclosing heading trail.
2. Identify which columns are metrics versus subdatasets/splits.
3. Cite the exact column used for a claim.
4. Avoid comparing rows across columns with different splits unless the user asks for a multi-column summary.
5. Include any prose immediately above the table that defines test sets, split names, or evaluation setup.

## Dataset descriptions and official resources

Dataset descriptions usually appear between a dataset heading and its first table. Extract:

- Task definition and domain.
- Dataset size, split sizes, or number of examples.
- Evaluation metric and whether higher/lower is better.
- Data/download links, project pages, public leaderboard links, and baseline repositories.
- Special conditions, such as automatically word-segmented Vietnamese text, gold versus predicted POS, dataset release versions, or known evaluation issues.

A page may have a public leaderboard in prose but no local results table. In that case, report that NLP-progress points to a public leaderboard and do not invent local SOTA rows.

## Paper/source and code columns

Paper/source columns may be named `Paper / Source`, `Paper`, or `Paper (including links to webservices/source code)`. Code columns may be named `Code`, `Github`, or be folded into notes.

Interpret code labels cautiously:

- `Official` usually means the table contributor believed the linked implementation was official.
- `Link`, raw URLs, or unlabeled GitHub links may be unofficial or merely related.
- Empty code cells mean no code link is listed in NLP-progress, not that code is unavailable elsewhere.
- Some cells contain multiple links, mirrors, or both official and unofficial implementations.

## Recommended citation shape

When answering a catalog query, include enough information for a user to audit the claim:

- Page and heading trail: `english/language_modeling.md > Language modeling > Word Level Models > Penn Treebank`.
- Dataset/task and metric: `Penn Treebank word-level language modeling, Test perplexity`.
- Model/system and score: preserve table text exactly where possible.
- Paper/source link text and URL, if extracted.
- Code link label and URL, if extracted.
- Caveat: “as listed in NLP-progress”; add staleness, split, metric, or warning notes when applicable.

Example prose pattern:

> As listed in NLP-progress at `<relative page> > <heading trail>`, `<model>` reports `<metric>=<score>` on `<dataset/split>`, with paper/source `<paper title or URL>` and code `<Official/Link/URL if present>`. The page defines the evaluation as `<metric description>`.
