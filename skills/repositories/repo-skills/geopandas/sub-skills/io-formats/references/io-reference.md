# GeoPandas I/O Reference

Read this for verified signatures and operational notes for data movement APIs.

## File I/O

| API | Verified signature / shape | Notes |
|---|---|---|
| `geopandas.read_file` | `read_file(filename, bbox=None, mask=None, columns=None, rows=None, engine=None, **kwargs)` | Reads vector data from paths, URLs, file-like objects, and supported drivers. Base install includes pyogrio; Fiona is optional. |
| `geopandas.list_layers` | top-level helper | Lists layers in multi-layer sources when the selected engine supports it. |
| `GeoDataFrame.to_file` | `to_file(self, filename, driver=None, schema=None, index=None, **kwargs)` | Writes vector files. Set `driver` when the extension is ambiguous or the destination has strict requirements. |
| `GeoDataFrame.from_file` | class method | Constructor-style read equivalent for many file workflows. |

Common filters:

- `bbox`: bounding box tuple or geometry-like object for spatial filtering.
- `mask`: geometry mask for filtering; ensure CRS is compatible with the data source.
- `columns`: select only needed fields; include geometry unless the task deliberately wants attributes only.
- `rows`: integer or slice to limit rows for smoke tests or previews.

Engine notes:

- `pyogrio` is part of this snapshot's base dependency set and is the default practical path for lightweight checks.
- `fiona` is an optional alternative engine. Do not claim Fiona-specific features unless Fiona is installed and verified.

## GeoJSON-like Records

| API | Use |
|---|---|
| `GeoDataFrame.iterfeatures()` | Iterate feature mappings for streaming or custom serialization. |
| `GeoDataFrame.to_geo_dict()` | Produce a GeoJSON-like dictionary. |
| `GeoDataFrame.to_json()` | Serialize to a GeoJSON string. |
| `GeoDataFrame.from_features()` | Build a GeoDataFrame from feature mappings or objects exposing `__geo_interface__`. |

Validate CRS separately when moving through plain dictionaries or JSON strings; a downstream consumer may not preserve all metadata.

## WKB/WKT

| API | Verified signature / behavior |
|---|---|
| `GeoSeries.from_wkt(data, index=None, crs=None, on_invalid='raise', **kwargs)` | Parse WKT strings into geometries. |
| `GeoSeries.to_wkt(**kwargs)` | Produce WKT strings. |
| `GeoSeries.from_wkb(...)` / `to_wkb(...)` | Parse or produce WKB bytes. |
| `GeoDataFrame.to_wkt()` / `to_wkb()` | Convert geometry columns for tabular interchange. |

Use WKT for readable fixtures and WKB for compact binary exchange. Always carry CRS metadata in a separate column/field if the target format does not store it.

## Arrow, Parquet, Feather, and GeoArrow

| API | Verified signature / behavior | Required optional dependency |
|---|---|---|
| `geopandas.read_parquet` | `read_parquet(path, columns=None, storage_options=None, bbox=None, to_pandas_kwargs=None, **kwargs)` | `pyarrow` |
| `GeoDataFrame.to_parquet` | `to_parquet(path, index=None, compression='snappy', geometry_encoding='WKB', write_covering_bbox=False, schema_version=None, **kwargs)` | `pyarrow` |
| `geopandas.read_feather` | `read_feather(path, columns=None, to_pandas_kwargs=None, **kwargs)` | `pyarrow` |
| `GeoDataFrame.to_feather` | `to_feather(path, index=None, compression=None, schema_version=None, **kwargs)` | `pyarrow` |
| `GeoDataFrame.to_arrow` / `from_arrow` | Arrow/GeoArrow conversion | `pyarrow` or compatible Arrow objects |

Practical choices:

- Use Parquet/GeoParquet for columnar storage and analytics workflows.
- Use `write_covering_bbox=True` when downstream readers benefit from spatial pruning and the data/metadata path supports it.
- Use `geometry_encoding='WKB'` for broad compatibility unless GeoArrow-native encoding is explicitly desired and supported.

## PostGIS and SQL

| API | Verified signature | Service requirements |
|---|---|---|
| `geopandas.read_postgis` | `read_postgis(sql, con, geom_col='geom', crs=None, index_col=None, coerce_float=True, parse_dates=None, params=None, chunksize=None)` | SQLAlchemy-compatible connection, database driver, geometry column, query privileges. |
| `GeoDataFrame.to_postgis` | `to_postgis(name, con, schema=None, if_exists='fail', index=False, index_label=None, chunksize=None, dtype=None) -> None` | SQLAlchemy, GeoAlchemy2/driver support, table privileges, PostGIS extension. |

Use `chunksize` for large reads/writes. Set `if_exists` deliberately (`fail`, `replace`, `append`) and treat `replace` as destructive.

## Optional Dependency Probe

Run:

```bash
python scripts/check_optional_io_dependencies.py --json
```

Use `--require pyarrow sqlalchemy psycopg` only when the task needs those modules to be installed now.
