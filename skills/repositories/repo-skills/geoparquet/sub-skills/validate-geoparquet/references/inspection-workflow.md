# Footer-to-conformance workflow

Use this sequence for a concrete `.parquet` file. Preserve raw command output as
review evidence and distinguish **conformant candidate**, **non-conformant**,
and **not verified**.

## 1. Identify the target

Record the claimed GeoParquet version, all geometry column names, whether the
file is a partition, the writer and exact versions, and whether old 1.1 readers
are a hard requirement. Do not infer support from an extension or a generic
Parquet read.

## 2. Inspect the footer

```bash
python /path/to/inspect_geoparquet.py data.parquet
python /path/to/inspect_geoparquet.py data.parquet --require-conformant --require-statistics
```

Review the exact `geo` key, UTF-8 JSON, schema paths, physical types,
max-definition and max-repetition levels, native logical type, row-group count,
and every row-group's geospatial statistics. A conforming geometry leaf is
root-level `BYTE_ARRAY`, repetition level 0, with native `Geometry` or
`Geography`. A plain binary WKB column is not native 2.0, even when its `geo`
JSON is convincing.

## 3. Validate metadata locally

For a bare object or `{"geo": {...}}` wrapper:

```bash
python /path/to/validate_geo_metadata.py metadata.json
python /path/to/validate_geo_metadata.py metadata.json --parquet data.parquet
```

Or pass `data.parquet` directly to extract and validate its footer metadata.
The default is offline. A non-zero result is a failed metadata or requested
footer gate. `--allow-missing-statistics` reports the missing observation as
unverified instead of passing it as verified.

## 4. Reconcile fields and statistics

Confirm that:

- `primary_column` names a `columns` entry and a native geometry field;
- every metadata column exists at the root and is WKB `BYTE_ARRAY`;
- no geometry field is repeated or nested;
- known `geometry_types` are unique, dimension-correct, complete, and agree
  with native `geospatial_types`; `[]` explicitly means unknown;
- `bbox` uses the correct 4/6/8 layout and contains every row-group extent;
- the optional CRS, edges, orientation, and epoch fields follow the normative
  values; and
- native CRS and metadata CRS describe one CRS, even when encoded differently.

PyArrow commonly exposes statistics as `is_geo_stats_set` and
`geo_statistics` fields `geospatial_types`, `xmin`, `xmax`, `ymin`, `ymax`,
`zmin`, `zmax`, `mmin`, and `mmax`. If the installed API does not expose an
observation, record it as missing instead of guessing.

## 5. Classify

- **Conformant candidate:** metadata, native schema, WKB physical layout, and
  required statistics checks pass.
- **Non-conformant:** a required rule fails, including absent native logical
  type, `PointZ`, duplicate types, a five-element bbox, metadata CRS as a
  string, nested/repeated geometry, or mismatched statistics.
- **Not verified:** a full PROJJSON check, native/metadata CRS equivalence, or a
  required statistics observation could not run. Do not call this a pass.

## 6. Version boundary

GeoParquet 1.1 commonly uses WKB `BYTE_ARRAY`, legacy `geo` metadata, and a
bbox covering. It may be the right compatibility target for an old reader, but
it lacks the native 2.0 logical type and must not be labelled GeoParquet 2.0.
A native-type-only file without `geo` metadata is likewise not a complete 2.0
GeoParquet file, even if a native reader can open it.
