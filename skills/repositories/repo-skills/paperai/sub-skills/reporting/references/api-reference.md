# Reporting API reference

Live inspection confirmed the public package is paperai 2.6.0 with PyYAML,
txtai, txtmarker, staticvectors, rich, regex, python-dateutil, and text2digits
available in the prepared Python 3.11 inspection environment. Do not copy that
private environment's executable or filesystem path into runtime instructions.

## Task API

```python
from paperai.report.task import Task

name, options, queries, outdir = Task.load("report.yml")
# queries == [(query_name, {"query": ..., "columns": [...] }), ...]
Task.queries(config)
Task.flatten(columns)
```

`Task.load(task)` accepts a path or YAML string. Existing paths are opened as
UTF-8 and set `outdir` to the parent directory. YAML strings use `.`. It calls
`yaml.safe_load`, requires `config["name"]`, and invokes `Task.queries`.
`Task.queries` skips root keys `id`, `name`, `options`, and `fields`, then
mutates each query's `columns` to a one-level flattened list. It is not a
friendly validator: malformed values can raise `TypeError`, `KeyError`, or a
YAML exception. Use the bundled validator first.

## Execute API

```python
from paperai.report.execute import Execute

Execute.run(
    task="report.yml",
    topn=3,
    render="md",          # md, csv, or ant
    path="MODEL_DIRECTORY",
    qa="OPTIONAL_RUNNER_VALUE",
    indir="SOURCE_PDF_DIRECTORY",
    threshold=0.25,
)
```

Signature:

```text
Execute.run(task, topn=None, render=None, path=None, qa=None,
           indir=None, threshold=None)
```

`run` first loads the model/database, loads the task, merges options, chooses a
renderer, opens the root output, builds reports, calls renderer cleanup, and
closes the database. Model/path failures therefore occur before task errors.
A failed run can leave a partial output; inspect the exception and remove only
known partial files before retrying.

```python
merged = Execute.options(
    {"render": "csv", "topn": 2},
    topn=5, render=None, path=None, qa=None, indir=None, threshold=0.4,
)
report = Execute.create("md", embeddings, db, merged)
```

`Execute.options` mutates and returns the supplied mapping. Non-`None` values
from the call win; otherwise existing YAML values remain. `Execute.create`
returns `Markdown`, `CSV`, or `Annotate`; any other renderer raises
`ValueError("Invalid report format: ...")`.

Important 2.6.0 detail: `Execute.options` stores `qa`, but `Report.__init__`
filters `qa` out of the RAG keyword/selector mapping. `options["llm"]` is the
effective RAG model selector. Also pass `topn` explicitly: absent values can be
stored as `None` rather than triggering the nominal `Report.build` fallback of
50.

## Report and renderer contracts

`Report(embeddings, db, options)` expects an embeddings object with
`isweighted()` and a paperai article/section SQLite connection. Its useful
methods are:

```text
Report.build(queries, options, output)
Report.params((query_name, query, columns))
Report.variables(value, (query_name, query, columns))
Report.sections(article_id)
Report.resolve(params, sections, article_id, field_name, value)
Report.subsection(article_id, section_id)
Report.surround(article_id, section_id, size)
```

`Report.build` searches each query, emits highlights, groups article rows,
computes fields, sorts by normalized `Date` descending, and calls the concrete
writer. `query: "*"` uses all article IDs instead of grouped search results.
The query layer caps highlights at five; the report asks for `int(topn / 10)`.

```python
from paperai.report.column import Column

Column.integer("Twenty Three")                 # "23"
Column.integer("4,000,234")                    # "4000234"
Column.integer("30 days")                      # None
Column.duration("2021-01-01 to 2021-01-31", "days")  # 30
Column.duration("1 week", "months")            # 0.25
Column.convert(30, "days", "months")           # 1.0
Column.categorical(None, "raw", ["x"])         # "raw"
```

`Column.duration` returns `None` for invalid/unsupported formats. `convert`
returns an unchanged value for an unknown input unit.

## Row and annotation details

Markdown rows contain normalized `Date`, linked `Study`, `Source`, `Matches`,
`Entry`, `Id`, and generated fields. CSV rows contain `Date`, plain `Study`,
`Study Link`, `Journal`, `Source`, `Matches`, `Entry`, `Id`, and generated
fields. Markdown escapes pipes and URL parentheses; CSV uses comma-delimited
minimal quoting, including for multiline values.

Annotation recursively scans `indir`, matches the basename of `Source`, and
uses `txtmarker.Factory.create("pdf", formatter, 4)`. The formatter removes
common URLs/emails/citation patterns and non-alphanumeric characters before
matching. A basename mismatch can produce no annotation without meaning that
query/report generation failed.
