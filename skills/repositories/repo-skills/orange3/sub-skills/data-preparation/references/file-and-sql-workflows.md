# Orange file, widget, and SQL workflows

This reference turns the Orange data model into practical load, clean, reshape, validate, and save flows.

## Typical local-file workflow

1. Load the data.
   - GUI: `OWFile` for local files and URLs, `OWDataSets` for bundled samples, `OWCSVImport` when text parsing needs manual control.
   - API: `Table.from_file(...)` or `Table("iris")` for sample data.
2. Inspect the schema and data quality.
   - GUI: `OWDataInfo`, `OWFeatureStatistics`.
   - API: inspect `len(table)`, `table.domain`, `table.has_missing()`, `table.is_sparse()`.
3. Clean the table.
   - `OWSelectColumns`, `OWEditDomain`, `OWSelectRows`, `OWImpute`, `OWContinuize`, `OWDiscretize`, `OWPurgeDomain`.
4. Reshape or combine.
   - `OWConcatenate`, `OWMelt`, `OWTranspose`, `OWGroupBy`, `OWUnique`, `OWRandomize`, `OWDataSampler`, `OWTransform`, `OWCreateClass`, `OWCreateInstance`.
5. Save the result.
   - `OWSave` or `Table.save(...)`.

Programmatic equivalent:

```python
from Orange.data import Table
from Orange.preprocess import Impute, Continuize

data = Table.from_file("input.tab")
data = Impute()(data)
data = Continuize()(data)
data.save("cleaned.tab")
```

## Data-widget sequencing

`OWPreprocess` is the reusable pipeline builder when the same cleaning chain should be kept as a single widget state.

Good use cases:

- combine `Impute` + `Continuize` + `Discretize` + `Normalize` in a repeatable order
- keep the pipeline editable for future runs
- hand a preprocessor object to a later workflow instead of hard-coding the whole chain

Keep the workflow in `Orange.widgets.data` when the task is about table/domain repair, row/column reshaping, or export.

## Reshape and validation patterns

- Use `OWSelectRows` for conditional filtering on attributes, classes, and metas.
- Use `OWDataSampler` and `OWRandomize` to make validation splits reproducible.
- Use `Table.transpose(...)` or `OWTranspose` for wide-to-long style reshaping.
- Use `OWGroupBy` for grouped aggregation and `OWMelt` for pivot-style conversion.
- Use `OWConcatenate` when several cleaned tables need to share a common schema.

If you are scripting, prefer explicit round-trip checks after a major reshape:

```python
round_tripped = Table.from_file("cleaned.tab")
assert round_tripped.domain == data.domain
```

## Save workflow

`OWSave` and `Table.save(...)` are the main export paths.

Practical notes:

- Use type annotations for `.tab` or `.csv` when the target reader should preserve explicit variable types.
- Pickle is the safest fallback for sparse tables.
- If a saved table loses name or type metadata, confirm that the sidecar metadata file stayed with the main file.
- If a stored filter or writer became invalid after an upgrade, reset the widget state and re-pick the format.

## SQL workflow, optional and service-bound

`OWSql` and `Orange.data.sql.table.SqlTable` are the SQL entry points.

Use them only when all of the following are true:

- a backend package is installed and visible to `Backend.available_backends()`
- the live database service is reachable
- credentials, schema, and table permissions are already known

`OWSql` supports both table selection and custom SQL. It can also discover categorical values from the database when `guess_values` is enabled, but that can be slow on large tables.

For custom SQL, the widget can materialize a query result only when the backend can write a table and a materialization table name is provided.

If no backend is available, stop at the local-file workflow and document the SQL path as optional instead of required.

## Provenance note

This reference is distilled from Orange3's file/SQL/preprocess documentation, widget implementations, and widget/API tests. See the repo-level provenance file for the relative evidence-path list and refresh baseline.
