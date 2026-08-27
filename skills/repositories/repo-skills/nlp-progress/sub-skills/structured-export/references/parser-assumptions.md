# Parser assumptions and edge cases

The bundled exporter is intentionally simple. It models the Markdown style used by NLP-progress benchmark pages rather than implementing a full Markdown parser.

## Input traversal

- Positional CLI inputs may be files or directories.
- Files are parsed exactly in CLI argument order.
- A directory is scanned only for top-level filenames ending in `.md`; nested directories are not traversed.
- Directory Markdown files are sorted by filename before parsing so repeated exports are deterministic.
- Files are read as UTF-8.

## Heading state machine

The parser splits a document into sections whenever a line begins with `#` in column 0.

- H1 (`# ...`) starts a task object.
- H2 (`## ...`) starts a subtask object under the current task.
- H3 (`### ...`) starts a dataset object under the current subtask, or directly under the task if no subtask is active.
- H3 headings containing `Table of content` are ignored as datasets.
- H4 (`#### ...`) is treated as a subdataset label only when a current H3 dataset already exists and the H4 section contains a valid SOTA table.
- H5 and deeper headings are not assigned schema objects.

Important consequences:

- Headings indented with spaces are not headings to this parser.
- A document with an H2/H3/H4 before any H1 produces an error diagnostic and may yield partial output.
- H4 sections without an active H3 dataset are reported as unexpected subdatasets and skipped.
- Dataset prose in H4 sections is not emitted separately; only the H4 label and its SOTA table are represented.

## Description extraction

- A task description is all text after the H1 until the next heading.
- A subtask description is all text after the H2 until the next heading.
- A dataset description is all text after the H3 except lines that belong to detected SOTA tables.
- Non-SOTA Markdown tables remain in the dataset description.
- Dataset links are all Markdown links in the dataset description, emitted as `{title, url}` objects.

## SOTA table detection

A SOTA table begins when all of these are true:

1. The line starts with `|` in column 0.
2. The line contains `model` case-insensitively.
3. The parser is not already inside a table.

Once a table starts, every following line that starts with `|` is part of that table. The table ends at the first line that does not start with `|`.

Consequences:

- Tables with leading spaces before `|` are not detected.
- Tables whose header uses `System`, `Method`, `Approach`, or another synonym instead of `Model` are skipped.
- Non-SOTA tables are not parsed unless their header contains `model`.
- Pipes inside cell text are not escaped or interpreted; rows are split with a simple `|` split.

## Header requirements

After splitting the header on `|`, empty header cells are discarded. Each remaining header cell is stripped, lowercased, has spaces removed, and has `**` removed before matching special columns.

Required columns:

- `Model` -> sanitized as `model`.
- `Paper / Source` -> sanitized as `paper/source`, or `Paper` -> sanitized as `paper`.

Optional special column:

- `Code` -> sanitized as `code`.

Every other header column becomes a metric name in `sota.metrics`. The metric names preserve their original header spelling after outer whitespace stripping.

If `Model` is missing, the table is skipped with an error diagnostic. If `Paper / Source` or `Paper` is missing, the table is skipped with an error diagnostic.

## Row parsing

- The first table line is the header.
- The second table line is assumed to be the Markdown separator row and is skipped.
- Remaining table lines are data rows.
- A row with fewer cells than the header is skipped with a warning.
- Metric values are raw strings from table cells.
- A row's `metrics` keys exactly match `sota.metrics`.
- The model cell is split by a simple parenthesis heuristic: `Model Name (Authors, Year)` emits `model_name: "Model Name"`; author text is not emitted.
- If a paper/source cell has multiple Markdown links, the first link becomes `paper_title` and `paper_url`; a warning is emitted.
- If a paper/source cell has no Markdown link, the row is kept but `paper_title` and `paper_url` are omitted.
- If a `Code` column exists, all Markdown links in that code cell become `code_links`. If the cell has no links, `code_links` is an empty list.

## Subdataset inference

Subdatasets can be produced in two ways.

### H4 subdataset sections

When an H4 section occurs under a current H3 dataset and contains one valid SOTA table, the H4 heading becomes the `subdataset` label and the table becomes that subdataset's `sota` object.

If the H4 section contains multiple SOTA tables, the parser falls back to the multi-table inference rule below for that H4 section.

### Multiple SOTA tables in one H3 section

When an H3 dataset section contains more than one SOTA table, the parser infers one subdataset label per table from the nearest preceding non-empty line before each table. It sanitizes each inferred label by removing `**`, trimming whitespace, and removing a trailing colon.

If the section text contains `hypernym discovery evaluation benchmark`, the first inferred label is dropped because that page has a non-SOTA partition table before the actual SOTA tables.

If the number of inferred labels does not match the number of SOTA tables, the parser emits an error diagnostic and skips those subdatasets. It does not invent labels.

## Known edge cases

- Empty leading header cells can shift row interpretation because empty header cells are discarded but row cells are still position-based.
- H4 tables under an H2 without an H3 container are skipped; normalize such Markdown to include an H3 dataset if the table must be exported.
- H5 and deeper SOTA tables are ignored unless the Markdown is flattened to H4/H3 levels accepted above.
- A table with a `Model` header but no `Paper`/`Paper / Source` is treated as non-exportable SOTA evidence, even if it has useful metrics.
- Markdown links with parentheses inside URLs may not parse as intended because the link extractor is intentionally lightweight.
- Raw metric values may contain footnote markers, asterisks, explanatory text, or missing-value markers. Normalize them only in a downstream transform, not in this preservation export.
