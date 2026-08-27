# Reporting troubleshooting

## Install/import

- **`ModuleNotFoundError: paperai` or `paperai.report`:** install paperai
  2.6.0 into the active Python environment and verify
  `python -c "import paperai; import paperai.report.execute"`. A YAML helper
  passing proves only YAML support; it does not prove report imports.
- **Missing `yaml`, `txtai`, `regex`, `dateutil`, `text2digits`, or `txtmarker`:**
  install the declared runtime dependencies. `txtmarker` is specifically
  needed by `ant`; `txtai` is needed for index/query/RAG construction.
- **Version mismatch:** confirm paperai 2.6.0 and inspect the installed txtai
  API before changing RAG options. Unknown RAG options are forwarded to txtai
  and may fail or change behavior across versions.

## YAML and column shape

- **YAML scanner/parser error:** quote values containing `:`, `#`, braces, or
  special prompt text. Use a block scalar (`|`) for a template. Validate before
  model loading.
- **`KeyError: name`:** the root needs a non-empty `name`; each column mapping
  needs `name`.
- **`KeyError: query` or `columns`:** a top-level non-reserved mapping is
  treated as a report query and therefore needs both keys. Check indentation so
  query content was not accidentally nested under `options`.
- **`TypeError` in `Task.queries`/`flatten`:** a query is not a mapping,
  `columns` is not a list, or an item is a scalar. Flattening is only one level.
- **Unknown/empty field:** exact standard names are `Id`, `Date`, `Study`,
  `Study Link`, `Journal`, `Source`, `Entry`, and `Matches`. Arbitrary names are
  not automatically read from SQLite and can fail row lookup. Use `constant`
  or generated `query` fields for other values.
- **Validator says valid but run fails:** the helper intentionally does not
  validate txtai options, model files, SQLite schema, relevance, or PDF text.

## Model/database/query prerequisites

- **Missing model path:** `Models.load(path)` joins `path` with
  `articles.sqlite`; a missing `path` can fail before YAML is read. Pass a real
  model directory explicitly.
- **`no such table: articles/sections`:** the database is not a compatible
  paperai/paperetl-style corpus. Follow [indexing](../../indexing/SKILL.md) for
  schema and export prerequisites instead of patching report SQL.
- **Database opens but search has `NoneType`/`isweighted` errors:** a database
  alone is insufficient. `Models.load` loads embeddings only when the model
  directory contains saved `config` or `config.json`; non-`*` reports need a
  compatible saved index.
- **No articles:** the query may not match, the default score cutoff (0.25) may
  be too high, or weighted/vector configuration may be incompatible. Test a
  narrow query and consult [querying](../../querying/SKILL.md) for syntax.
- **Report is unexpectedly huge:** `query: "*"` enumerates all articles and can
  ignore the intended article bound. Replace it with a narrow query and lower
  `topn` while diagnosing.
- **`topn` arithmetic/type failure:** pass an explicit integer. In 2.6.0,
  `Execute.options` can store `None` when neither YAML nor CLI supplies it,
  despite the nominal `Report.build` fallback comment of 50.

## Renderer/output failures

- **`ValueError: Invalid report format`:** use exactly `md`, `csv`, or `ant`,
  not `markdown` or `pdf`.
- **Markdown table is malformed:** generated text containing `|` is normally
  escaped; inspect custom output and duplicate/unknown column names. Markdown
  intentionally removes `Journal`, `Study Link`, and `Sample Text` from its
  table list.
- **CSV appears to have the wrong line count:** parse each `<query-name>.csv`
  with a CSV reader; multiline values are quoted. The root `<name>.csv` master
  is temporary and is deleted.
- **Stale/overwritten output:** Markdown and temporary/per-query CSV files open
  in write mode. Annotation outputs use `annotations/<Source>` and can replace
  same-basename files. Use a unique root/query name or fresh output directory.
- **Partial files after an exception:** loading, task parsing, renderer
  construction, and writing are separate stages. Capture the exception, remove
  only known partial artifacts, and retry with one query/one article.

## Generated columns and QA

- **Model download/authentication failure:** with no `options.llm`, RAG may
  resolve the default QA model. In verified 2.6.0 the `qa` Execute/CLI value is
  filtered before RAG construction, so set YAML `options.llm` to a local model
  or known model ID. Check cache/network/authentication and reduce `context` or
  `params.maxlength`.
- **Generated field blank:** no relevant section may have been retrieved, the
  question may be unsuitable, or RAG may have returned no value. Add a
  temporary `matches` excerpt field to distinguish retrieval from extraction.
- **Generated field slow:** cost grows with selected articles, generated fields,
  context, and matches. Reduce each one, avoid `*`, and keep annotation as a
  separate final stage.
- **Conversion returns `None`:** `int` does not accept values with units or
  decimals; durations need recognized ranges/units; unsupported duration text
  is not scientific inference. Preserve raw text beside converted output.
- **Unexpected categorical result:** no classifier means original text is
  returned. With a similarity/labels model, ensure labels are compatible with
  returned label indices.
- **`$NAME`/`$QUERY` surprise:** substitutions lowercase values and remove
  underscores from query names. Avoid placeholders when exact case is needed.

## Section/context controls

- **`section`/`surround` did not expand:** the extracted value must occur
  verbatim in an indexed section. `section` returns all same-name subsection
  rows; `surround` uses neighboring stored section IDs, not characters. At
  document boundaries fewer neighbors are expected.
- **Context is missing in weighted indexes:** weighted section filtering can
  exclude section names. Try `options.allsections: true` deliberately; it can
  increase context and runtime. Consult [indexing](../../indexing/SKILL.md) for
  the index's section policy.

## Optional PDF annotation

- **`ant` fails on `indir`:** `indir` is required for annotation. Check that it
  exists and is readable before running; a missing/`None` value can fail during
  recursive directory walking.
- **No annotations produced:** this may be valid report generation. Annotation
  matches `basename(Source)` exactly, not title, URL, or article ID. Compare the
  CSV `Source` column with PDF basenames and confirm recursive contents.
- **PDF cannot be highlighted:** verify `txtmarker` import, readable/unlocked
  PDFs, and text extraction. Image-only scans have no searchable text. The
  formatter strips punctuation and non-alphanumeric characters, making short or
  heavily transformed excerpts difficult.
- **Annotation dependency is unavailable:** use Markdown/CSV as the supported
  fallback; do not treat annotation as a required CPU report path.

## Size/runtime diagnosis

Start with one query, explicit `topn: 1`, one standard field, and Markdown.
Record wall time/output size. Then add one generated field, raise `topn`, raise
context/matches, and change renderer one dimension at a time. If standard-only
is slow, separate model startup/database/index issues from RAG generation. If
memory grows on `*`, stop and bound the task.
