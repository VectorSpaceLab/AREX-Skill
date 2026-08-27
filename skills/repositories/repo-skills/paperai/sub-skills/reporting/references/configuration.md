# Report configuration

`Task.load` uses `yaml.safe_load`. A task root is a mapping with a non-empty
`name`; `options` is optional. Every other top-level mapping except reserved
`id`, `name`, `options`, and `fields` is treated as a report query. Each query
needs a `query` string and `columns` list. Paperai does not perform friendly
schema validation itself, so run `../scripts/validate_report_config.py` first.

## Minimal safe YAML

This standard-only template isolates model/database/output plumbing. Replace
placeholders before running; no placeholder is a real model or data path.

```yaml
name: ExampleReport
options:
  render: md
  topn: 3
  threshold: 0.25
  path: MODEL_DIRECTORY

ExampleQuery:
  query: "SEARCH TERMS"
  columns:
    - name: Date
    - name: Study
    - name: Study Link
    - name: Journal
    - name: Source
    - name: Entry
    - name: Id
    - name: Matches
```

A task supplied as a file writes beside that file. A YAML string supplied to
`Task.load` uses `.` as its output directory. Use a filesystem-safe `name` and
query key. A non-`*` query needs a saved compatible index as well as the
SQLite database.

## Generated-column example

Add generated fields only after the standard-only run works. In the verified
2.6.0 code, `options.llm` is the effective RAG model selector. The `qa` runner
argument is accepted and stored by `Execute.options`, but is removed before
`Report` constructs RAG; do not rely on it as the model selector.

```yaml
name: ExampleExtraction
options:
  render: csv
  topn: 3
  path: MODEL_DIRECTORY
  llm: LLM_MODEL_DIRECTORY_OR_ID
  context: 5
  system: "Extract only the requested value from the supplied context."
  template: |
    Question: {question}
    Context: {context}
  params:
    maxlength: 2048
    stripthink: true

Research:
  query: "SEARCH TERMS"
  columns:
    - name: Study
    - name: Sample Size
      query: "number of participants"
      question: "Sample size"
      dtype: int
    - name: Follow-up
      query: "follow-up duration"
      question: "Follow-up duration"
      dtype: months
    - name: Evidence Snippet
      query: "primary outcome"
      question: "Quote the primary outcome"
      surround: 1
    - name: Constant Label
      constant: screened
```

Replace `MODEL_DIRECTORY`, `LLM_MODEL_DIRECTORY_OR_ID`, and `SEARCH TERMS`.
The model/default RAG may resolve or download weights; validation never does.

## Root and query keys

| Key | Shape | Meaning |
|---|---|---|
| `name` | string | Report/output stem. Required. |
| `options` | mapping | RAG options plus runner overrides. |
| `<query-name>` | mapping | One query/output unit. |
| `query` | string | Search text; `*` enumerates all articles. |
| `columns` | list | Column mappings or one-level nested lists. |
| `id`, `fields` | reserved | Not treated as report queries. |

`Task.flatten` flattens exactly one list level. Deeper nesting remains nested
and is unsafe for normal column processing. A column should be a mapping with a
non-empty `name`; standard fields need no `constant` or `query` marker.

## Options and precedence

`Execute.options(options, topn, render, path, qa, indir, threshold)` mutates the
mapping and gives supplied command/API values precedence. It stores these
runner keys:

- `topn`: article count for ordinary queries;
- `render`: `md`, `csv`, or `ant`;
- `path`: model/index directory passed to `Models.load`;
- `qa`: stored runner value, but filtered before RAG in verified 2.6.0;
- `indir`: source directory used by `ant`;
- `threshold`: query score cutoff, defaulting to 0.25 inside query search when
  it remains unset.

Pass `topn` explicitly. Although `Report.build` comments say the default is 50,
`Execute.options` inserts `topn: None` when neither YAML nor CLI supplies it,
so the `None` can reach arithmetic/search code. `render` is explicitly resolved
to `md` by `Execute.run` when falsey.

Other options are forwarded to txtai RAG after runner keys are removed. Common
keys are `llm`, `system`, `template`, `context`, and `params`; accepted values
are txtai-version/model dependent. `similarity` creates a similarity/labels
pipeline for categorical fields. `allsections: true` disables weighted-index
section-name filtering.

## Column kinds

### Standard columns

Use exact names from this set:

- `Id`: article identifier;
- `Date`: publication date, normalized by query formatting;
- `Study`: title (Markdown renders it as a link; CSV keeps plain text);
- `Study Link`: article reference/link;
- `Journal`: publication, falling back to `Source` when absent;
- `Source`: source filename/name;
- `Entry`: article entry date;
- `Matches`: matching section text.

Unknown names are not arbitrary SQLite columns. They can cause a row lookup
failure; use a generated or constant field for other data.

### Constant and generated columns

```yaml
- name: Cohort
  constant: validation
```

A `constant` field is copied without retrieval or QA. A generated field has
`query`, and `question` defaults to that query if omitted. The query ranks
article-section context; the question is passed to RAG. A query beginning with
`$` is handled as a question-style field. `$NAME` becomes the lowercase query
name with underscores removed; `$QUERY` becomes lowercase query text.

| Key | Meaning |
|---|---|
| `name` | Required output field name. |
| `query` | Retrieval/question input. |
| `question` | RAG question; defaults to `query`. |
| `constant` | Fixed value; mutually exclusive in intent with `query`. |
| `matches` | Nonzero number of matched context values to join with blank lines. |
| `section` | `true` replaces the matched value with the full same-named subsection. |
| `surround` | Number of nearby stored section rows on each side. |
| `snippet` | Requests snippet context; `section`/`surround` force it true. |
| `dtype` | `int`, duration unit, or a list of categorical labels. |

`topn` chooses articles; `matches` chooses context values inside one generated
field. Empty retrieval/extraction becomes an empty generated field.

## Renderer behavior

- **Markdown (`md`)** writes query headings, `Highlights`, and `Articles`.
  It removes `Journal`, `Study Link`, and `Sample Text` from the table,
  percent-encodes parentheses in links, and escapes `|` as `&#124;`.
- **CSV (`csv`)** uses Python CSV quoting and writes one `<query-name>.csv` per
  query. The temporary root `<name>.csv` is deleted in renderer cleanup.
  Multi-line matches/answers must be read with a CSV parser, not line counts.
- **Annotation (`ant`)** removes `Date`, `Study`, `Study Link`, `Journal`,
  `Matches`, `Entry`, and `Id` from annotation fields, always retains `Source`,
  and writes matching PDFs under `annotations/`. It annotates the first
  blank-line-delimited value from each nonempty generated field.

## Conversion assumptions

Conversions apply to nonempty generated values, not constants or standard
metadata:

- `dtype: int` strips commas and converts number words such as `Twenty Three`
  to a digit string. `30 days`, decimals, and unparseable text return `None`.
- Duration `days|weeks|months|years` parses date ranges or simple relative
  durations. It uses fixed approximations: 7 days/week, 30 days/month, and 365
  days/year (with 4 weeks/month and 52 weeks/year in direct unit conversion).
  Invalid/unsupported text returns `None`.
- `dtype: [labels]` uses the labels pipeline when a similarity model exists;
  with no model, `Column.categorical` returns original text. Labels must match
  the classifier's selected indices.

These are presentation conversions, not scientific calendar calculations. Keep
a raw answer alongside a converted field when precision matters.
