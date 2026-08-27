---
name: semantic-layer
description: "Guides PandasAI semantic dataset creation, schema validation,
  CSV/Excel/parquet/SQL loading, views, transformations, and query-builder
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Semantic Layer

Use this sub-skill when a task involves PandasAI `pai.create`, `pai.load`,
`read_csv`, `read_excel`, `schema.yaml`, semantic-layer columns, transformations,
SQL connector schemas, or views across datasets.

The semantic layer is the PandasAI v3 surface that turns raw data into named,
described, loadable datasets. Created datasets are stored under a project
`datasets/` directory and then loaded into `DataFrame` or `VirtualDataFrame`
objects for chat and SQL-backed analysis.

## Fast route

1. Validate the user's goal: local CSV/Excel/parquet, SQL-backed virtual table,
   or view over existing datasets.
2. Use `organization/dataset` path names with lowercase hyphenated segments.
   PandasAI converts the dataset name to an underscore schema/table name.
3. For local data, prefer `pai.read_csv` or `pai.read_excel`, then `pai.create`.
4. For SQL, define a `source` with `type`, `connection`, and `table`; install
   only the needed `pandasai-sql[...]` extension.
5. For views, ensure every column and relation uses `table.column` format and
   that source datasets exist first.
6. After loading a dataset, route natural-language `.chat()` behavior to
   [`../conversational-analysis/SKILL.md`](../conversational-analysis/SKILL.md).

## Read next

- [`references/api-reference.md`](references/api-reference.md) for verified API
  signatures and class fields.
- [`references/schema-and-data-formats.md`](references/schema-and-data-formats.md)
  for schema YAML, valid source/column/transformation types, path naming, and
  view rules.
- [`references/workflows.md`](references/workflows.md) for local, SQL, view,
  transformation, Excel, and FakeLLM recipes.
- [`references/troubleshooting.md`](references/troubleshooting.md) for schema,
  loader, query-builder, path, connector, and SQL-safety failures.
- [`scripts/validate_semantic_schema.py`](scripts/validate_semantic_schema.py)
  to validate a schema YAML without creating datasets.
- [`scripts/create_local_dataset_smoke.py`](scripts/create_local_dataset_smoke.py)
  for a deterministic local create/load/chat smoke.

## Boundary decisions

| User asks for | Do |
| --- | --- |
| Loading CSV or Excel directly into a DataFrame for chat | Use this sub-skill for `read_csv`/`read_excel`, then route chat to conversational analysis |
| Persistent dataset with metadata/schema | Use `pai.create` and this sub-skill end-to-end |
| SQL table represented without local data load | Use SQL `source` schema; note optional connector dependency |
| Combining multiple datasets | Use a semantic view with relations and compatible sources |
| `pai dataset create` prompts | Route to CLI/project ops; the CLI writes a source schema interactively |

## Safe validation

Run the schema validator on a YAML file:

```bash
python sub-skills/semantic-layer/scripts/validate_semantic_schema.py --schema-yaml schema.yaml
```

Run the end-to-end local smoke:

```bash
python sub-skills/semantic-layer/scripts/create_local_dataset_smoke.py
```

Both helpers avoid external databases, provider credentials, network, and Docker.

## Key gotchas

- `pai.create` requires either a PandasAI `DataFrame`, a valid source, or
  `view=True` with relations/columns.
- Dataset path format is `organization/dataset`; both segments must be
  lowercase and hyphenated.
- Schema names use underscores, not hyphens. Generated SQL must use the schema
  name, not the original path slug.
- For views, columns and relation endpoints must be `table.column` with letters,
  numbers, and underscores.
- `group_by` is strict: every non-aggregated column must be in `group_by`, and
  expression columns must not be in `group_by`.
- SQL and cloud connector sources are optional-extension workflows; do not assume
  their packages, services, credentials, or enterprise license are present.
