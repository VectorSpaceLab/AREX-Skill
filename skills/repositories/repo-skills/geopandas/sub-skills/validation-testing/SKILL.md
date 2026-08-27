---
name: validation-testing
description: "Use when validating GeoPandas outputs, using geopandas.testing
  assertions, designing fixtures, or selecting focused GeoPandas repository
  tests."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Validation and Testing

Use this sub-skill when the task is about proving GeoPandas results are correct, writing assertions for geometry-aware outputs, or maintaining/testing the GeoPandas repository.

## Read First

- [Testing reference](references/testing-reference.md): `geopandas.testing` assertion helper behavior, equality options, fixture design, and output comparison patterns.
- [Maintainer workflows](references/maintainer-workflows.md): focused test selection, optional dependency awareness, contributor-oriented checks, and when not to run expensive/service tests.
- [Troubleshooting](references/troubleshooting.md): assertion mismatches, CRS/index/order differences, optional dependency skips, and service/network test boundaries.
- [geopandas_assertion_demo.py](scripts/geopandas_assertion_demo.py): tiny demonstration of `assert_geodataframe_equal` and deliberate mismatch handling.

## Route Here When

- The user asks how to compare two `GeoDataFrame` or `GeoSeries` objects in tests.
- The task mentions `geopandas.testing.assert_geodataframe_equal`, `assert_geoseries_equal`, geometry equality tolerance, CRS/index checking, or expected output fixtures.
- The user is editing the GeoPandas repository and needs focused pytest commands or optional-dependency triage.
- A result from `core-data-model`, `io-formats`, `spatial-operations`, or `mapping-geocoding` needs assertion-backed validation.

## Route Elsewhere

- Use `../core-data-model/SKILL.md` for object construction and CRS semantics.
- Use `../io-formats/SKILL.md` for I/O workflow behavior before asserting round trips.
- Use `../spatial-operations/SKILL.md` for analysis logic before comparing outputs.
- Use `../mapping-geocoding/SKILL.md` for plot/geocoding optional dependencies before validation.

## Default Operating Rules

1. Prefer `geopandas.testing` helpers over raw pandas equality for geometry-aware objects.
2. Choose equality flags deliberately: CRS, index type/order, geometry type, coordinate tolerance, and column order can all matter differently by task.
3. Keep fixtures tiny, explicit, and CRS-labeled.
4. When testing optional workflows, distinguish missing optional dependency skips from real failures.
5. Avoid full test-suite runs unless the user asks and the environment has the needed optional/service dependencies.
6. For repository maintenance, start with focused tests around changed behavior, then broaden only when failures or risk justify it.

## Minimal Check

```bash
python scripts/geopandas_assertion_demo.py
```

Expected high-level signal: the script passes equal GeoDataFrame assertions, catches an intentional CRS mismatch, and reports the assertion helper behavior.

## Handoff

- Use this sub-skill at the end of a workflow to turn expected GeoPandas outputs into assertions.
- For production verification of this generated skill, pair its scripts with selected native tests and integration cases from the review artifacts.
