# Vector I/O workflows

## Read, inspect, and filter

```python
import fiona

with fiona.open("roads.gpkg", layer="roads") as src:
    print(src.profile)
    for feature in src.filter(bbox=(-105.0, 39.0, -104.0, 40.0)):
        if feature.properties.get("class") == "primary":
            print(feature.id)
```

For an attribute predicate that the driver supports, `src.items(where=...)`
can push an SQL-style filter into GDAL. Treat the expression as driver- and
field-name-sensitive; if it fails, first inspect `src.schema["properties"]`.

## Write a compatible output

```python
import copy
import fiona

with fiona.open("source.geojson") as src:
    profile = copy.deepcopy(src.profile)
    profile.update(driver="GPKG", layer="selected")
    with fiona.open("selected.gpkg", "w", **profile) as dst:
        dst.writerecords(src.filter(bbox=(-105, 39, -104, 40)))
```

The output driver must support the schema's geometry and property types. If the
source schema contains a type the target driver cannot represent, change the
schema and normalize each feature before writing rather than relying on silent
conversion.

## Build a tiny dataset from mappings

```python
import fiona

schema = {"geometry": "Point", "properties": [("name", "str:40"), ("n", "int")]}
with fiona.open(
    "points.shp", "w", driver="ESRI Shapefile", schema=schema, crs="EPSG:4326"
) as dst:
    dst.write({
        "type": "Feature", "id": "0",
        "geometry": {"type": "Point", "coordinates": [0.0, 1.0]},
        "properties": {"name": "origin", "n": 1},
    })
```

For long-lived code, use `Feature` and `Geometry` objects when you need Fiona's
mapping/serialization behavior, and validate that all properties fit the
schema before the first write.

## Append and layers

Open an existing compatible layer with `mode="a"`; do not pass write-only
creation metadata when appending. For a multi-layer container, select a layer
by name or index and use `fiona.listlayers(path)` before writing a new layer.
A layer name in write mode must be a string.

## Byte-backed and local archive data

Use `MemoryFile` for bounded bytes and URI schemes such as `zip://`,
`tar://`, or `zip+https://` for virtual paths supported by the installed GDAL
build. Local archive cases are deterministic; remote URI cases need network
access and should be separately approved. For a byte-backed read:

```python
from fiona.io import MemoryFile

with open("small.geojson", "rb") as fh:
    with MemoryFile(fh.read()) as memfile:
        with memfile.open() as src:
            count = sum(1 for _ in src)
            print(count)
```

Close the outer file before assuming its data can be modified. For a write-only
`MemoryFile`, call `memfile.open(driver=..., schema=..., crs=...)` and keep the
memory object alive until the dataset is flushed.
