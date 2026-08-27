---
name: reporting
description: "Create and troubleshoot paperai 2.6.0 YAML reports in Markdown,
  CSV, or optional PDF annotation format, including generated columns and safe
  configuration validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Reporting

Use this route to turn an existing paperai corpus/index into a bounded report.
Start with [configuration](references/configuration.md) for YAML and column
semantics, [workflows](references/workflows.md) for staged runs,
[api-reference](references/api-reference.md) for Python calls, and
[cli-reference](references/cli-reference.md) for the positional module CLI.
Use [troubleshooting](references/troubleshooting.md) before changing a model,
corpus, or report definition.

## Scope and routing

- **Owns:** `Task.load`, `Task.queries`, one-level `Task.flatten`, report YAML,
  standard/constant/generated columns, `Execute.options`/`create`/`run`,
  Markdown (`md`), CSV (`csv`), optional PDF annotation (`ant`), output naming,
  `topn`, `threshold`, `indir`, `allsections`, `section`, `surround`,
  `matches`, `snippet`, and column conversion helpers.
- **Requires:** a model directory containing `articles.sqlite` and a compatible
  saved txtai embeddings index. Use [indexing](../indexing/SKILL.md) for corpus
  schema, index construction, vector configuration, and compatibility.
- **Delegates:** search syntax, score filtering, grouping, and highlight
  internals to [querying](../querying/SKILL.md). Do not use this route to repair
  SQLite, build embeddings, or ingest source PDFs.

## Safe route

1. Copy the minimal, standard-column YAML in [configuration](references/configuration.md)
   and replace every placeholder. Run the bundled
   [the safe validator](scripts/validate_report_config.py) before loading a
   model; it parses YAML and checks shape only, without importing paperai,
   opening SQLite, or touching models.
2. Confirm the model directory and database/index prerequisites. For `ant`,
   also confirm a readable source directory and exact source basenames.
3. Run one narrow query with explicit `topn` and `md`. Add one generated field,
   then `dtype`/context controls, then switch to CSV or annotation.
4. Inspect output files with a Markdown/CSV parser and plan a fresh output
   directory or unique names: paperai opens outputs in write mode and does not
   prompt before replacement.

## Fast facts

- Renderer values are exactly `md`, `csv`, and `ant`; missing render resolves
  to Markdown, while another value raises `ValueError`.
- A task path writes beside the YAML. Its root `name` is the Markdown/master
  output stem. Markdown is `<name>.md`; CSV creates one `<query-name>.csv` per
  top-level query and removes its temporary `<name>.csv`; annotation writes
  `annotations/<Source>` and removes its temporary `<name>.ant`.
- Standard columns are `Id`, `Date`, `Study`, `Study Link`, `Journal`, `Source`,
  `Entry`, and `Matches`. A `constant` column performs no model call. A
  generated column has `query` and optional `question`/controls.
- `query: "*"` enumerates all articles and can make `topn` ineffective. The
  query layer uses a default threshold of 0.25 when threshold is absent.
  Pass `topn` explicitly: in 2.6.0 `Execute.options` stores a missing value as
  `None`, which can defeat the nominal `Report.build` fallback of 50.
- `section: true` expands a match to the full same-named subsection; positive
  `surround: N` expands to nearby stored section rows. `section` wins if both
  are set. `matches` controls context snippets per generated field, not article
  count.
- `qa` is an `Execute`/CLI parameter but verified 2.6.0 filters it before RAG
  construction; set YAML `options.llm` for the effective RAG model selector.
  `ant` additionally requires `txtmarker`, PDFs, and matching `Source` names.

Keep long schemas, renderer details, workflows, and failure matrices in the
linked references rather than expanding this router.
