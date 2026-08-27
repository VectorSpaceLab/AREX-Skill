# Orange data-preparation troubleshooting

Use this when file loading, schema repair, preprocessing, saving, or SQL setup goes wrong.

## Fast triage

Before changing anything, check:

- `len(table)` — is the table empty?
- `table.domain` — do the roles and variable names look right?
- `table.has_missing()` and `table.is_sparse()` — are you dealing with missing or sparse data?
- the exact widget message — `OWFile`, `OWSave`, and `OWSql` usually expose the failure mode directly.
- whether the task can be recovered by reloading with a different reader/writer or by editing the domain.

## Unknown file type

**Typical signs**

- `OWFile` shows `Select file type.` or `Missing reader.`
- `Table.from_file(...)` raises `IOError("Unknown file name extension.")`

**What usually happened**

- the extension is not registered
- the file was renamed without changing its real format
- the current widget state points to a stale reader

**Fix**

- pick an explicit reader in `OWFile`
- rename the file so the extension matches the content
- for raw delimited text, use `OWCSVImport` instead of guessing
- for saving, choose a supported writer extension before calling `Table.save(...)`

## Invalid encodings

**Typical signs**

- `Table(filename)` or `CSVReader(...).read()` raises `ValueError`
- `OWFile` shows a read error or a warning about skipped bytes
- a UTF-8 file with a BOM is misread as plain UTF-8 text

**What usually happened**

- the source file is not really UTF-8
- the delimiter sniffer hit a byte sequence it could not decode
- the file is binary or mixed-format content disguised as text

**Fix**

- reopen the file with `OWCSVImport` and select the encoding manually
- try `utf-8-sig` for UTF-8 files with a BOM
- save the source text as plain UTF-8 before importing
- if the file is actually binary, stop using a text reader and switch to the correct format

## Duplicate names

**Typical signs**

- `OWFile` shows `Some variables have been renamed to avoid duplicates.`
- headers appear as `name (1)`, `name (2)`, and so on
- a transpose or merge step creates repeated output names

**What usually happened**

- the source file has repeated column names
- two source tables were combined without a unique schema
- a rename created a collision with an existing variable

**Fix**

- rename the columns in the source file or in `OWEditDomain`
- check whether the renamed names still match downstream widget expectations
- if duplicate values were intentional, keep the warning in mind because later joins and edits may still collide

## Missing values

**Typical signs**

- rows disappear after `OWSelectRows` or `IsDefined`
- `OWImpute` becomes necessary before later cleaning or export
- a statistic or reshape widget reports no usable rows

**What usually happened**

- blank cells, `?`, or NaNs were imported from the file
- a preprocessing step removed rows or columns with missing data
- a sparse/dense conversion exposed previously hidden missing values

**Fix**

- inspect `table.has_missing()` before and after each step
- use `OWImpute` when you need to preserve rows
- use `RemoveNaNRows`, `RemoveNaNColumns`, or `OWPurgeDomain` when dropping is acceptable
- if a widget outputs nothing, check whether the filter removed every row

## Type coercion surprises

**Typical signs**

- a numeric column loads as discrete or text
- a text column becomes categorical with unexpected values
- a date column is treated as plain text
- `OWEditDomain` or `OWFile` shows a type that does not match the source file

**What usually happened**

- the reader inferred types from a short sample
- a header annotation was missing or ambiguous
- a column looked discrete because it had a small value set
- a time column was not ISO-8601-shaped enough for automatic parsing

**Fix**

- add explicit header annotations in the file
- use `OWEditDomain` to change the variable type after loading
- prefer `Variable.make(...)` when building descriptors in scripts
- if the conversion itself should persist, attach a `compute_value` transform instead of hand-editing the data matrix

## SQL credential or backend problems

**Typical signs**

- `OWSql` shows `Please install a backend to use this widget.`
- connection errors mention host, role/user, or database
- the table list never appears
- custom SQL fails when the backend cannot execute or materialize the query

**What usually happened**

- no SQL backend package is installed
- the database service is down or unreachable
- credentials, schema, or table permissions are wrong
- the backend is read-only for the requested operation

**Fix**

- confirm that a backend appears in `Backend.available_backends()`
- verify host, port, database, username, password, and schema
- start with a simple table query before trying custom SQL
- treat SQL as optional if the environment is not service-ready

## Empty tables

**Typical signs**

- the widget says `No data.`
- a preprocessing step appears to succeed but downstream widgets receive nothing
- row counts drop to zero after filtering or selection

**What usually happened**

- `Table.from_domain(...)` or a filter produced a zero-row table
- `OWSelectRows` removed every row
- a domain edit or projection-style reshape removed all usable columns

**Fix**

- check `len(table)` after each stage
- inspect the selected conditions, column filters, and row samplers
- remember that some preprocessors accept empty input but later widgets may not

## Save/load mistakes

**Typical signs**

- `OWSave` shows `Use Pickle format for sparse data.`
- `OWSave` shows `unsupported_format` or `no_file_name`
- `Table.save(...)` fails with an unknown extension
- a reload loses annotations or variable metadata

**What usually happened**

- the writer does not support sparse data
- the stored filter is stale after an upgrade
- the filename extension does not match the selected writer
- the metadata sidecar was separated from the main file

**Fix**

- use pickle for sparse tables
- choose the writer before saving, not after
- keep the `.metadata` sidecar with the main tabular file
- re-open the output with the same reader to confirm the round trip
- if the widget state looks stale, reselect the format and save again

## Provenance note

This troubleshooting guide is distilled from Orange3's data readers, SQL/table code, data widgets, and native tests. See the repo-level provenance file for the relative evidence-path list and refresh baseline.
