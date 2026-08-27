# CRS integrations

## PyProj

Use PyProj when the workflow needs richer transformer selection, datum-grid
control, explicit axis-order policy, or transformations outside Fiona's small
helpers. Convert the resulting geometry through a GeoJSON-like mapping before
writing with Fiona. Keep one authoritative source and destination CRS in the
workflow.

## Shapely

Use Shapely for geometry operations such as centroid, intersection, validity,
and orientation. A common safe boundary is:

1. Read a Fiona geometry mapping.
2. Convert it with `shapely.geometry.shape`.
3. Perform geometry operations in a known CRS.
4. Convert back with `shapely.geometry.mapping` or `Geometry.from_dict`.
5. Write through Fiona with a schema matching the result geometry.

Fiona does not provide these operations itself. Do not describe a Shapely
operation as a Fiona API, and do not mix coordinate transformation with a
geometry validity claim without checking both explicitly.
