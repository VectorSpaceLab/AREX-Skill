# Troubleshooting structured export

Use this guide when the bundled exporter fails, emits warnings, or produces JSON that is valid but missing expected data. Unless noted otherwise, run the commands from this sub-skill directory.

## CLI problems

### `the following arguments are required: paths`

Cause: no input file or directory was provided.

Recovery:

```sh
python3 scripts/export_nlp_progress.py english --output structured.json
```

### `input path does not exist`

Cause: the command is running from a directory where the relative input path is wrong, or the target language/task file is absent.

Recovery:

1. Run `pwd` and `ls` to confirm the current working directory.
2. Use paths relative to that directory.
3. For a single file, verify it is a Markdown file you intended to parse.
4. For a directory, verify it contains top-level `*.md` files; nested directories are not scanned.

### `output parent directory does not exist`

Cause: `--output` points inside a directory that has not been created.

Recovery:

```sh
mkdir -p exports
python3 scripts/export_nlp_progress.py english --output exports/structured.english.json
```

### `output path is a directory`

Cause: `--output` names a directory instead of a file.

Recovery: choose a file path such as `structured.json` or `exports/structured.json`.

## Path and traversal problems

### A directory export is missing files from nested folders

Cause: directory inputs are intentionally non-recursive.

Recovery: pass each desired directory explicitly, or pass individual Markdown files explicitly.

### The JSON order changes from a hand-picked command

Cause: top-level CLI argument order is preserved. Directory contents are sorted, but the order of separate positional paths is exactly the order you typed.

Recovery: choose and record a stable input order for reproducible downstream diffs.

### A directory contributes no output

Cause: the directory has no top-level `*.md` files.

Recovery: pass the correct language directory or specific Markdown files.

## Output problems

### JSON validation fails

Cause: output may be mixed with diagnostics only if stdout/stderr were manually redirected together, or the file may be partial from an interrupted run.

Recovery:

1. Re-run with `--output structured.json` to a regular file.
2. Keep stderr separate from stdout.
3. Validate again:

```sh
python -m json.tool structured.json >/dev/null
```

### Output file was overwritten

Cause: the exporter overwrites the selected `--output` file.

Recovery: choose a new file name for experiments, or copy the previous JSON before rerunning.

### Output is an empty list

Causes:

- Input files had no column-0 H1 headings.
- Input directory had no top-level Markdown files.
- The wrong path was supplied.

Recovery: inspect only the path list and heading levels, then rerun with a known representative Markdown file.

## Schema problems

### A task has no `datasets`

Cause: datasets are created only from H3 headings. A task may instead contain `subtasks`, whose datasets are nested under those subtask objects.

Recovery: consumers should traverse both direct `task.datasets` and every `subtask.datasets`.

### A dataset has no `sota`

Causes:

- The H3 section has prose only.
- The table header does not start in column 0 with `|`.
- The table header does not contain `Model`.
- The table lacks `Paper` or `Paper / Source`.
- The table is under an unsupported heading level.

Recovery: check parser assumptions before changing Markdown. If the user wants preservation export, do not invent SOTA data; either normalize the Markdown heading/table shape or accept that the dataset is prose-only in JSON.

### Rows have no `paper_title` or `paper_url`

Cause: the paper/source cell has no Markdown link.

Recovery: this is valid output. Keep the row and treat missing paper fields as unknown link metadata.

### Rows have no `code_links`

Cause: the table has no `Code` column. If the table has `Code` but a row cell has no Markdown links, `code_links` is present as an empty list.

Recovery: consumers should treat `code_links` as optional.

### Metric values are strings instead of numbers

Cause: the exporter preserves raw Markdown table cell values.

Recovery: perform numeric cleanup downstream only after deciding metric-specific rules for missing values, asterisks, parentheticals, and text notes.

## Table parsing problems

### `Model name not found in this SOTA table, skipping`

Cause: a detected table header contains `model` somewhere but the sanitized header cells do not include exactly `model`.

Recovery:

- Use `Model` as a column header when normalizing Markdown.
- Avoid empty leading header cells unless row layout is known to align correctly.
- Do not rename the model column to `System`, `Method`, or `Approach` if the table must be exported.

### `Paper reference not found in this SOTA table, skipping`

Cause: the header does not include `Paper` or `Paper / Source` after sanitization.

Recovery:

- Use `Paper` or `Paper / Source` as the paper column header.
- If the table is not a SOTA table, accept that it remains in dataset prose instead of JSON `sota`.

### `This row does not have enough columns, skipping`

Cause: a Markdown row has fewer pipe-delimited cells than the header.

Recovery:

- Check for a missing trailing cell separator or an unescaped `|` that shifted columns.
- Normalize malformed rows before exporting if exact row coverage matters.

### Expected table is absent with no warning

Likely causes:

- The table line has leading spaces before `|`.
- The table is under H5 or deeper.
- The table header does not contain `model`.
- The table is in an H4 section without a parent H3 dataset.

Recovery: normalize the Markdown shape or run a custom one-off parser if the user asks for broader Markdown support.

## Link extraction problems

### `Found multiple paper references ... using only the first`

Cause: a paper/source cell contains multiple Markdown links.

Recovery: accept the warning when preserving the repository contract. If downstream use needs all paper links, add a separate post-processing pass from the original Markdown cells; do not reinterpret the exported `paper_url` as exhaustive.

### Dataset or code links look incomplete

Cause: the link extractor is lightweight and expects ordinary `[title](url)` links. URLs containing literal parentheses or malformed Markdown can parse poorly.

Recovery: verify the source cell or description text. Normalize malformed Markdown before export if those links are required.

## Subdataset problems

### `Parsing the subdataset SOTA tables ... inferred N labels for M tables`

Cause: a section has multiple SOTA tables, but the parser could not find exactly one preceding non-empty label per table.

Recovery:

1. Inspect the section's text around each table.
2. Add or normalize a non-empty label immediately before each table when content editing is allowed.
3. If content editing is not allowed, document the skipped subdatasets and keep the rest of the JSON.

### H4 subdataset tables are skipped

Cause: an H4 table must be under an active H3 dataset. H4 under H2, H1, or another unsupported level is reported and skipped.

Recovery: normalize the page to include an H3 dataset container above the H4 sections, or accept that those tables are outside the bundled parser contract.
