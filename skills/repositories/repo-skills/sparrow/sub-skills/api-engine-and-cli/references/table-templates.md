# Table templates and table-mode routing

This reference covers the request-level behavior of `--table` / `table=true`, `--table-template`, and backend option ordering. Backend-specific document and OCR extraction internals belong to `../document-extraction/SKILL.md` and `../ocr-service/SKILL.md`.

## When table mode is selected

The engine routes to the table wrapper when CLI `--table` or API `table=true` is set. The wrapper:

1. Splits the user query into form fields and table fields.
2. Runs an OCR/table pass with `query="*"` to obtain structured text/table blocks.
3. Separates table blocks from non-table blocks per page.
4. Optionally splits multi-page PDFs into page-specific files for form extraction.
5. Loads the requested table template by module basename.
6. Extracts table data from each table block.
7. Extracts form data from non-table blocks when the template implements form extraction.
8. Merges form data with table data and returns raw data for one page or page-wrapped data for multiple pages.

If the wrapper returns one page, the response shape is the page data itself. If it returns multiple pages, the response is a list such as:

```json
[
  {"data": {"items": [...]}, "page": 1},
  {"data": {"items": [...]}, "page": 2}
]
```

## Option ordering in table mode

Normal document extraction expects the first two `options` entries to be backend method and model/space:

```text
[backend, model, optional_flag, ...]
```

Table mode reuses the same list differently:

- `options[:2]` is the backend/model pair available for form extraction.
- `options[2:]` is passed as the backend/model list for the table/OCR pass.

Therefore a practical table-template request usually needs **two backend/model pairs**:

CLI:

```bash
./sparrow.sh '{"items":[{"description":"str", "price":"float or null"}]}' \
  --pipeline sparrow-parse \
  --table \
  --table-template sparrow_generic_table \
  --options mlx \
  --options form-model-name \
  --options mlx \
  --options table-ocr-model-name \
  --file-path statement.pdf
```

API:

```text
options=mlx,form-model-name,mlx,table-ocr-model-name
```

If table mode is enabled but only one backend/model pair is supplied, the table/OCR pass receives too few options and backend configuration fails.

## Query splitting

The table wrapper parses the JSON query and splits it into:

- `form_query`: keys that are not arrays with `items` in their name;
- `table_queries`: array-valued keys whose key name contains `items`.

Example input:

```json
{
  "account_number": "int",
  "items": [
    {"date": "str", "description": "str", "deposit": "float or null"}
  ]
}
```

`account_number` becomes form data; `items` becomes the table query.

Important generic-template nuance: the generic template's parser expects the table key to be exactly `items`. A key such as `statement_items` can be selected by the wrapper because it contains `items`, but the generic template parser does not consume that key as its field schema. Prefer `items` for generic-template queries unless a different template explicitly supports another key.

With `query="*"`, the wrapper skips form/query splitting and passes an empty table query list to the template. The generic template then auto-detects all table columns and returns string values.

## Template factory

The table-template factory dynamically imports a template by basename and expects these functions:

| Function | Required for | Behavior |
| --- | --- | --- |
| `fetch_table_data(table_query, table_markdown)` | table extraction | Converts one table block into a dict. Missing function raises an attribute error. |
| `fetch_form_data(...)` | form/table merge | Converts non-table OCR blocks into form fields. Missing function raises an attribute error when form fields need extraction. |

If a template name does not resolve, the factory raises `Table template '<name>' not found: ...`.

## Implemented template behavior

### `sparrow_generic_table`

The generic template is the usable table-template implementation. It:

- parses an HTML `<table>` block;
- flattens multi-row headers, including `rowspan` / `colspan` combinations;
- generates fallback column names `col1`, `col2`, ... when no headers exist;
- deduplicates duplicate headers with suffixes;
- fuzzy-matches query field names against column headers;
- converts values for `int`, `float`, nullable numeric types, and strings;
- returns `{"items": [...]}`;
- with no table query list, returns all columns as strings;
- extracts form fields from non-table text entries by fuzzy key/value matching.

The generic template is best for HTML table blocks produced by OCR/table extraction when the requested output can be expressed as `{"items": [{...}]}`.

### `sparrow_invoice_table`

The invoice template exists but is a placeholder: its form and table functions return empty dictionaries. Do not choose it when a populated extraction result is required unless the generated skill has been refreshed against a newer implementation.

## Table hints and markdown interaction

- `hints_file_path` / `hints_file` is passed through to form extraction paths and to normal query preparation. Table-template parsing itself uses the OCR/table markdown and query fields; it does not apply hints inside the generic template.
- `--markdown` and `--table` are separate engine branches. If both are set, the engine's branch order selects markdown first and table mode is not reached. Use one wrapper mode per request.

## Minimal table-mode checklist

1. Use `--table` / `table=true` only when the output needs table-template post-processing.
2. Use `--table-template sparrow_generic_table` unless a known implemented template is available.
3. Use query key `items` for generic table schemas, or `*` to auto-detect all columns.
4. Supply two backend/model pairs in table mode: first for form extraction, second for table/OCR pass.
5. If the response is empty, check whether the template is a placeholder, the table block was missing, or the query key was not exactly `items`.
