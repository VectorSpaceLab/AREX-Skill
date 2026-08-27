# CRS workflows

## Transform a point

```python
from fiona.transform import transform

xs, ys = transform("EPSG:4326", "EPSG:26953", [-105.0], [40.0])
assert len(xs) == len(ys) == 1
print(xs[0], ys[0])
```

Always state whether input coordinates are longitude/latitude, projected
units, or another axis convention. A numerically plausible result can still be
wrong when the CRS is mislabeled.

## Transform a GeoJSON-like geometry

```python
from fiona.transform import transform_geom

point = {"type": "Point", "coordinates": [-105.0, 40.0]}
projected = transform_geom("EPSG:4326", "EPSG:26953", point)
assert projected["type"] == "Point"
assert len(projected["coordinates"]) == 2
```

Pass an iterable when processing multiple geometries. Preserve feature
properties and IDs yourself; `transform_geom` handles geometry, not complete
feature records.

## Combine with a dataset

Use `vector-io` to open a source, read `src.crs`, transform each geometry, and
write using a destination schema and destination CRS. Set the output CRS to the
same `dst_crs` passed to `transform_geom`; otherwise the coordinates and metadata
will disagree.

## Antimeridian and precision

Set `antimeridian_cutting=True` only when the destination is geographic and the
workflow expects dateline splitting. Inspect the resulting geometry type: a
Polygon may become MultiPolygon. Avoid relying on the deprecated `precision`
argument for new code; round output coordinates after transformation if a
stable textual precision is required.
