---
name: data-preparation
description: "Load, inspect, clean, reshape, validate, and save Orange data."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Data Preparation

Use this sub-skill for Orange data loading, schema inspection, column/domain edits, preprocessing, reshaping, validation, and saving.

## Start here

1. Identify the input shape: local file, URL, sample dataset, in-memory `Table`, or SQL source.
2. Decide whether the task is only inspection or also cleaning, reshaping, validation, or export.
3. Read [`references/data-formats.md`](references/data-formats.md) for the `Table`/`Domain`/`Variable` model and file-format rules.
4. Read [`references/file-and-sql-workflows.md`](references/file-and-sql-workflows.md) for file, widget, reshape, save, and optional SQL flows.
5. Read [`references/troubleshooting.md`](references/troubleshooting.md) when parsing, encoding, duplicate-name, empty-table, or save/load problems appear.
6. Optionally run [`scripts/data_smoke.py`](scripts/data_smoke.py) for a non-mutating sanity check.

## Use this for

- Loading tables from `.tab`, `.csv`, `.tsv`, `.xlsx`, `.pkl`, sample datasets, or URLs.
- Understanding domains, attributes, class variables, metas, and variable reuse.
- Cleaning and reshaping data with `OWFile`, `OWCSVImport`, `OWDataSets`, `OWDataInfo`, `OWFeatureStatistics`, `OWSelectColumns`, `OWEditDomain`, `OWSelectRows`, `OWImpute`, `OWContinuize`, `OWDiscretize`, `OWPurgeDomain`, `OWConcatenate`, `OWMelt`, `OWTranspose`, `OWGroupBy`, `OWRandomize`, `OWUnique`, `OWTransform`, `OWDataSampler`, `OWCreateClass`, `OWCreateInstance`, and `OWPreprocess`.
- Exporting with `OWSave` or `Table.save`.
- Using `OWSql` and `Orange.data.sql` only when a backend is already available and configured.

## Route away

- Supervised learners, predictors, scoring, and evaluation: use the supervised-modeling sibling.
- Plots, projections, clustering, and other exploratory visualization: use the exploration-visualization sibling.
- Widget framework mechanics, canvas behavior, or widget-catalog tooling: use the widget-development sibling.

## Operating notes

- `Table` stores rows in `X`, `Y`, `metas`, and `W`; `Domain` controls which variables live in each part.
- `Variable.make(...)` is preferred when you want Orange to reuse an existing descriptor by name and type.
- Prefer `Table.from_file(...)` / `Table.save(...)` for file round trips, and `Table.from_numpy(...)` / `Table.from_table(...)` for programmatic construction or domain conversion.
- `Table.transpose(...)` is the main reshape helper for turning columns into rows.
- Direct in-place edits in scripts usually need `with table.unlocked():`.
- `OWFile` can rename duplicate columns and switch readers; `OWCSVImport` is the escape hatch for delimiter and encoding problems.
- `OWSave` refuses unsupported sparse formats; pickle is the safe fallback for sparse tables.
- `OWSql` is optional and service-bound; do not make it a minimum requirement.

## Boundaries

- Do not cover supervised modeling, model evaluation, plotting, projection, or clustering here.
- Do not assume a live SQL backend in the inspection environment.
- Keep SQL guidance documented but optional.
