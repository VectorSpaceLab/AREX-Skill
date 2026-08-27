---
name: crs-transform
description: "Guides Fiona CRS construction, inspection, coordinate
  transformation, geometry transformation, and PROJ-backed interoperability
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Fiona CRS and transforms

Use this route when the task names EPSG/PROJ/WKT, needs to inspect collection
CRS, transform coordinates or GeoJSON-like geometries, or combine Fiona with
PyProj or Shapely. Read [the API reference](references/api-reference.md) for
verified signatures and [workflows](references/workflows.md) for patterns.

- Use `vector-io` for opening and writing datasets and copying profile metadata.
- Use `environment-cloud` when CRS operations fail because PROJ/GDAL data or
  compiled libraries are missing.
- Read [integrations](references/integrations.md) before crossing into Shapely
  or PyProj.
- Read [troubleshooting](references/troubleshooting.md) for invalid CRS,
  axis/units, antimeridian, or precision issues.

Fiona transforms coordinates through GDAL/PROJ but does not perform general
geometry analysis, topology repair, buffering, or spatial predicates.
