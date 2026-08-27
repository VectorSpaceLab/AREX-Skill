# Vector I/O API reference

## `fiona.open`

The verified public signature is:

```python
fiona.open(
    fp, mode="r", driver=None, schema=None, crs=None, encoding=None,
    layer=None, vfs=None, enabled_drivers=None, crs_wkt=None,
    ignore_fields=None, ignore_geometry=False, include_fields=None,
    wkt_version=None, allow_unsupported_drivers=False, opener=None, **kwargs
)
```

- `fp` may be a path-like value or a file-like object in supported modes.
- `mode` is `"r"`, `"w"`, or `"a"`. Reading is the default.
- In `"w"`, supply a supported driver and schema; supply `crs` or `crs_wkt`
  when the output needs spatial reference metadata.
- `layer` selects a named or indexed layer. In write mode, layer names are
  strings.
- `encoding` handles datasets whose driver cannot infer the correct encoding.
- `include_fields` and `ignore_fields` are mutually exclusive. Use
  `ignore_geometry=True` when only attributes are needed.
- `enabled_drivers` restricts driver probing. `allow_unsupported_drivers=True`
  is an escape hatch, not a default: it bypasses Fiona's known-safe mode table.
- Driver-specific `kwargs` become OGR open or layer-creation options.

## `Collection`

`Collection(path, mode="r", driver=None, schema=None, crs=None, encoding=None,
layer=None, ...)` exposes file-like behavior over features. Important
properties are `driver`, `schema`, `crs`, `crs_wkt`, `name`, `mode`, `closed`,
`bounds`, `profile`, `meta`, and `enabled_drivers`. Common methods include
iteration, `items(bbox=..., where=...)`, `filter(bbox=...)`, `write(feature)`,
`writerecords(iterable)`, `flush()`, and `close()`.

Use `len(src)` only when the driver supports counting. Dataset feature IDs are
GDAL-controlled and may begin at 0 or 1 and need not be contiguous; do not
assume Python list indexing semantics for negative IDs.

## Model objects

`Feature`, `Geometry`, and `Properties` are GeoJSON-like mapping objects. Their
usual fields are `id`, `geometry`, and `properties`; a geometry has `type` and
`coordinates` (or `geometries` for a collection). Use `Geometry.from_dict(...)`
and `Feature.from_dict(...)` when converting ordinary mappings into Fiona model
objects, and `to_dict`/`ObjectEncoder` when serializing in a version where the
mapping-compatible model is available.

## `MemoryFile`

The verified constructor is `MemoryFile(file_or_bytes=None, filename=None,
ext="")`. Constructing it with initial bytes makes a read-only byte-backed file;
constructing it without bytes creates a writable temporary virtual file. A
`MemoryFile` contains one dataset and its `.open(...)` method has no `path`
argument. Close both the collection and the memory file with context managers.

## Safe minimal read

```python
import fiona

with fiona.open("input.geojson") as src:
    print(src.driver, src.schema, src.crs)
    first = next(iter(src), None)
    if first is not None:
        print(first.id, first.geometry, first.properties)
```

This assumes the file exists and that its installed GDAL build includes its
format driver. Validate with `fio info` or a small `fiona.open` probe first.
