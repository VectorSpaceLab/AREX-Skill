---
name: spatial-operations
description: "Use when running GeoPandas spatial joins, nearest joins, overlays,
  clips, dissolves, spatial indexes, and Shapely-backed geometry analysis
  operations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Spatial Operations

Use this sub-skill when the task combines, filters, aggregates, or transforms geometries with GeoPandas analysis APIs.

## Read First

- [Operations reference](references/operations-reference.md): verified signatures and parameter notes for joins, overlay, clip, dissolve, spatial index, and common geometry methods.
- [Workflows](references/workflows.md): recipes for CRS-safe joins, nearest analysis, overlay/clip, dissolve, invalid-geometry repair, and metric operations.
- [Troubleshooting](references/troubleshooting.md): fixes for CRS mismatch, unexpected join cardinality, invalid geometries, empty overlays, distance warnings, and spatial-index confusion.
- [spatial_operations_smoke.py](scripts/spatial_operations_smoke.py): tiny deterministic check covering `sjoin`, `overlay`, `clip`, `dissolve`, and `.sindex`.

## Route Here When

- The task mentions `sjoin`, `GeoDataFrame.sjoin`, `sjoin_nearest`, `predicate`, `lsuffix`, `rsuffix`, `distance_col`, or spatial predicates.
- The task asks for `overlay`, set operations (`intersection`, `union`, `identity`, `symmetric_difference`, `difference`), `keep_geom_type`, `make_valid`, or polygon validity repair.
- The task uses `clip`, `dissolve`, `explode`, `union_all`, `intersection_all`, `buffer`, `distance`, `dwithin`, `contains`, `within`, `intersects`, `nearest`, or spatial index queries.
- The user needs to choose a projected CRS for metric analysis, use a spatial index explicitly, or reason about output row/cardinality behavior.

## Route Elsewhere

- Use `../core-data-model/SKILL.md` to create GeoDataFrames, repair active geometry columns, or understand CRS assignment versus reprojection basics.
- Use `../io-formats/SKILL.md` to read/write layers before or after operations.
- Use `../mapping-geocoding/SKILL.md` to visualize operation results.
- Use `../validation-testing/SKILL.md` for equality assertions or focused native tests.

## Default Operating Rules

1. Inspect `.crs` on every input before combining layers. Reproject, do not override, when coordinates need transformation.
2. For metric operations (`buffer`, `distance`, `dwithin`, nearest thresholds), use a projected CRS with linear units.
3. Validate polygon inputs before overlay or union. Use `make_valid()` when invalid geometry is an expected data-quality issue.
4. Choose the predicate intentionally: `intersects` is broad; `within`/`contains` are directional; boundary-only relationships may surprise users.
5. Expect join and overlay outputs to change row counts and add suffixes/index columns. Document cardinality and column naming.
6. Use `.sindex.valid_query_predicates` to discover available spatial index predicates in the current environment.

## Minimal Check

```bash
python scripts/spatial_operations_smoke.py
```

Expected high-level signal: the script reports successful spatial join, overlay, clip, dissolve, and spatial-index assertions on tiny in-memory geometries.

## Handoff

- Validate objects and CRS with `core-data-model` first when inputs are uncertain.
- Persist operation outputs with `io-formats` only after verifying CRS and geometry validity.
- Use `mapping-geocoding` for visualization and `validation-testing` for assertion-backed comparisons.
