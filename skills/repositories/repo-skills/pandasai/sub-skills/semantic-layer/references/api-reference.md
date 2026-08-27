# Semantic Layer API Reference

## Purpose

Use this for verified signatures, model fields, source types, and loader/query
builder behavior. Recipes are in `workflows.md`; validation rules are expanded
in `schema-and-data-formats.md`.

## File readers

```python
import pandasai as pai

df = pai.read_csv("data.csv")
excel_df = pai.read_excel("workbook.xlsx")
all_sheets = pai.read_excel("workbook.xlsx", sheet_name=None)
```

| API | Verified signature | Return behavior |
| --- | --- | --- |
| `pai.read_csv` | `read_csv(filepath: Union[str, BytesIO]) -> DataFrame` | Wraps `pandas.read_csv` and sets a sanitized table name from the file name or `table_from_bytes`. |
| `pai.read_excel` | `read_excel(filepath, sheet_name=0) -> Union[dict[Hashable, DataFrame], DataFrame]` | Returns a single PandasAI DataFrame for a single sheet; returns a dict of PandasAI DataFrames when pandas returns multiple sheets. |

## Dataset creation and loading

Verified signature:

```python
pai.create(
    path: str,
    df: DataFrame | None = None,
    description: str | None = None,
    columns: list[dict] | None = None,
    source: dict | None = None,
    relations: list[dict] | None = None,
    view: bool = False,
    group_by: list[str] | None = None,
    transformations: list[dict] | None = None,
) -> DataFrame | VirtualDataFrame
```

`pai.create`:

- validates `path` as `organization/dataset` using lowercase hyphenated names;
- writes `schema.yaml` under a project `datasets/` directory;
- writes `data.parquet` for local DataFrame-backed datasets;
- converts hyphenated dataset names to underscore schema names;
- returns a loaded `DataFrame` or `VirtualDataFrame`.

Verified loading signature:

```python
pai.load(dataset_path: str) -> DataFrame
```

`pai.load` validates the dataset path, checks the local dataset path, reads the
schema, selects a loader, and returns the loaded dataframe object.

## Schema model fields

| Model | Important fields |
| --- | --- |
| `SemanticLayerSchema` | `name`, `source`, `view`, `description`, `columns`, `relations`, `order_by`, `limit`, `transformations`, `destination`, `update_frequency`, `group_by` |
| `Column` | `name`, `type`, `description`, `expression`, `alias` |
| `Source` | `type`, `path`, `connection`, `table` |
| `SQLConnectionConfig` | `host`, `port`, `database`, `user`, `password` |
| `Relation` | `name`, `description`, `from`, `to` |
| `Transformation` | `type`, `params` |

`SemanticLayerSchema.to_dict()` omits `None` values and uses aliases such as
`from`. `to_yaml()` serializes that dictionary to YAML.

## Loader selection

`DatasetLoader.create_loader_from_schema` chooses:

| Condition | Loader | Result |
| --- | --- | --- |
| `schema.source.type` is `csv` or `parquet` | `LocalDatasetLoader` | Loads data through DuckDB into a PandasAI `DataFrame` |
| `schema.view` is true | `ViewDatasetLoader` | Returns a `VirtualDataFrame` backed by view query builder |
| other supported source types | `SQLDatasetLoader` | Returns a `VirtualDataFrame` backed by optional connector execution |

Every loader validates that its query builder can produce parseable SQL before
returning.

## Query builder behavior

- Local source table expressions use `read_csv(...)` or `read_parquet(...)` over
  files in the project dataset directory.
- SQL source table expressions use the lowercased source table name.
- Views build subqueries over dependency datasets and join them through
  relations.
- Transformations are applied to column expressions when the schema declares
  them.
- `order_by`, `limit`, `group_by`, `distinct` from duplicate-removal
  transformations, and column aliases are included in generated SQL.

## SQL safety

Local and remote query execution paths validate SQL before execution. The
sanitizer accepts SELECT/CTE-style reads and blocks common mutation or metadata
keywords such as INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, GRANT, SHOW,
DESCRIBE, comments, and similar constructs.
