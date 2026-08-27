# Reporting workflows

## 1. Validate and bound the first run

1. Define one top-level query and explicit `topn: 1`–`5`.
2. Start with standard columns only. This separates model/database/index
   wiring from RAG extraction.
3. Run the bundled validator and fix all errors:

   ```bash
   python scripts/validate_report_config.py TASK_FILE
   ```

4. Confirm `MODEL_DIRECTORY/articles.sqlite` exists and that the directory has
   a compatible saved embeddings configuration/index. The report layer does
   not build or repair an index; use [indexing](../../indexing/SKILL.md).
5. Run Markdown first and inspect headings, dates, links, output size, and row
   shape. Add exactly one generated field next.

A model-free YAML check cannot prove query execution: `Execute.run` loads the
model/database and `Report` constructs RAG. Use a small real model/index for
runtime smoke checks.

## 2. Markdown diagnostic report

```bash
python -m paperai.report TASK_FILE 3 md MODEL_DIRECTORY
```

For every top-level query, Markdown emits a query heading, `Highlights`, and
`Articles`. It keeps a human-readable linked Study value, escapes `|` in cell
values, and encodes parentheses in URLs. A no-match query can validly produce
an empty article section; compare with the querying route before changing the
YAML.

Specify `options.llm` for reproducible generated fields. In verified 2.6.0 the
CLI/API `qa` value is stored but removed before RAG construction. If `llm` is
absent, txtai may resolve the default `NeuML/bert-small-cord19qa` model and
need cache/network access.

## 3. CSV export

```bash
python -m paperai.report TASK_FILE 5 csv MODEL_DIRECTORY
```

CSV is intended for downstream tools. There is one `<query-name>.csv` per
query, with a header and data rows. The root `<name>.csv` is a temporary master
handle and is removed during cleanup. Parse per-query output with a CSV reader:
multiline matches/answers are quoted and line counts are misleading.

Keep query names filesystem-safe and unique. The implementation opens existing
per-query files with write mode and has no collision prompt.

## 4. Generated fields and conversions

Start with one field:

```yaml
- name: Intervention
  query: "intervention used"
  question: "What intervention was used?"
```

For a source excerpt instead of a QA answer, use `matches`:

```yaml
- name: Evidence
  query: "primary outcome"
  matches: 2
```

For controlled numeric output, use `dtype` only when the answer format is
predictable:

```yaml
- name: Count
  query: "number of subjects"
  question: "Number of subjects"
  dtype: int
```

Retrieval/RAG cost grows with selected articles × generated fields × context.
Keep a raw generated field beside a converted field when a failed conversion
would hide important evidence. `question` defaults to `query`; `$NAME` and
`$QUERY` are substituted per top-level query.

## 5. Section, surround, snippet, and allsections

```yaml
- name: Local Context
  query: "adverse events"
  question: "Quote the relevant evidence"
  surround: 1
```

- `section: true` replaces a matched value with all stored rows having the
  matching section name.
- `surround: N` includes stored section rows from matching ID `N` rows before
  and after, within the same section name. It is not a character/word count.
- If both are set, `section` takes precedence.
- The extracted value must occur verbatim in a stored section for expansion.
- `section` or `surround` force snippet behavior in the report's parameter
  handling.
- Weighted indexes filter section names using the index policy unless
  `options.allsections: true`; this changes context size and cost.

Use a tiny report to check boundary behavior: the first/last section naturally
has fewer neighbors, and section names may be absent.

## 6. Full-corpus audit (`query: "*"`)

`*` is special: it bypasses embeddings search and enumerates all article IDs.
The implementation then processes every article, so `topn` may not bound this
case. It is appropriate for a deliberate full export, not a first run. Test
with a narrow query, one generated field, and a copied/small corpus before
scaling. Full-corpus generated reports can be slow, large, and model-cache
intensive.

## 7. Optional PDF annotation

```bash
python -m paperai.report TASK_FILE 3 ant MODEL_DIRECTORY OPTIONAL_RUNNER_VALUE SOURCE_PDF_DIRECTORY
```

Run Markdown/CSV first. For `ant`:

- install/import `txtmarker` and its PDF support;
- ensure `SOURCE_PDF_DIRECTORY` exists and is readable;
- ensure each database `Source` basename equals a PDF basename exactly;
- use text-bearing, readable/unlocked PDFs; scanned image-only PDFs may not
  contain highlightable text; and
- use a fresh output directory if previous annotations must be preserved.

The annotator recursively scans the input directory, writes matching files to
`annotations/`, and annotates the first blank-line-delimited value from each
nonempty generated field. Standard metadata fields are excluded and `Source`
is retained for lookup. A valid query can therefore produce no annotation when
basenames do not match.

## 8. Programmatic orchestration and performance

Use the API when fractional threshold values or application-level preflight are
needed:

```python
from paperai.report.execute import Execute

Execute.run(
    task=task_file,
    topn=3,
    render="csv",
    path=model_directory,
    qa=None,
    indir=None,
    threshold=0.35,
)
```

Put the effective RAG model in YAML `options.llm`, not the `qa` argument, for
paperai 2.6.0. Reduce one dimension at a time when budgeting: article count,
top-level query count, generated-column count, `context`, `matches`, then
renderer. Progress messages occur around every 100 processed documents; model
startup may be quiet and should be diagnosed separately from report building.
