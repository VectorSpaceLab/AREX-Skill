# Reporting CLI reference

The module entry point is positional rather than a full argparse interface:

```bash
python -m paperai.report TASK [TOPN] [RENDER] [MODEL_PATH] [QA_VALUE] [SOURCE_DIR] [THRESHOLD]
```

| Position | `Execute.run` argument | Meaning |
|---|---|---|
| `TASK` | `task` | Required YAML path. A path writes beside the task. |
| `TOPN` | `topn` | Integer article count; pass it explicitly for bounded runs. |
| `RENDER` | `render` | `md` (default), `csv`, or `ant`. |
| `MODEL_PATH` | `path` | Required model/index directory containing `articles.sqlite`; non-`*` queries need a saved embeddings index. |
| `QA_VALUE` | `qa` | Runner value accepted by the CLI, but filtered before RAG in verified 2.6.0; use YAML `options.llm` for the effective model. |
| `SOURCE_DIR` | `indir` | Required for `ant`; recursively searched for source basenames. |
| `THRESHOLD` | `threshold` | Match cutoff. The module entry point currently parses this position with `int`; use the Python API or YAML for fractional values. |

The entry point converts `TOPN` and `THRESHOLD` with `int` and does not provide a
robust help/argument-count screen. Keep the order exact and prefer the validator
for task shape. Generic placeholder paths below are examples only.

## Commands

Standard-column Markdown smoke run:

```bash
python -m paperai.report TASK_FILE 3 md MODEL_DIRECTORY
```

CSV with an optional runner value (the effective RAG model belongs in YAML
`options.llm`):

```bash
python -m paperai.report TASK_FILE 5 csv MODEL_DIRECTORY OPTIONAL_RUNNER_VALUE
```

PDF annotation:

```bash
python -m paperai.report TASK_FILE 3 ant MODEL_DIRECTORY OPTIONAL_RUNNER_VALUE SOURCE_PDF_DIRECTORY
```

## Output naming and collisions

For a task file whose root contains `name: ExampleReport`:

- `md` writes `ExampleReport.md` beside the task. It includes every top-level
  query, each with a heading, highlights, and articles table.
- `csv` opens a temporary `ExampleReport.csv` master handle, then writes one
  `<query-name>.csv` beside the task for each top-level query. Cleanup removes
  the master; the per-query CSVs are the success artifacts.
- `ant` opens a temporary `ExampleReport.ant` handle, writes matching files to
  `annotations/<Source>` beside the task, and removes the master. Existing
  annotation basenames can be replaced.

Outputs use write mode without prompting. Use a fresh output directory or
unique, filesystem-safe root/query names when preserving prior results. Query
names become filenames for CSV, so avoid separators, `..`, and duplicate names.

## Model-free validation

```bash
python scripts/validate_report_config.py TASK_FILE
# or: cat TASK_FILE | python scripts/validate_report_config.py -
```

The helper emits JSON and returns nonzero for YAML parse errors, missing root
`name`, malformed `options`, missing query `query`/`columns`, or malformed
columns. It reports standard/generated/constant counts and warning-level
unknown fields, but does not prove model availability, SQLite schema, query
relevance, RAG quality, renderer import, or PDF readability.
