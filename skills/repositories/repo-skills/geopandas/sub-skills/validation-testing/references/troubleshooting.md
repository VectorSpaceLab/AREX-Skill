# Validation and Testing Troubleshooting

## Assertion Fails Because CRS Differs

Decide whether CRS must be equal for the task.

- If yes, fix the workflow that lost or changed CRS.
- If no, document why and choose assertion options deliberately rather than ignoring CRS by habit.
- Never hide a `set_crs()` versus `to_crs()` mistake by relaxing assertion flags.

## Assertion Fails Because Row or Index Order Differs

Likely cause: joins, overlays, groupby/dissolve, or file readers changed row order/index.

Fix:

1. Sort by stable columns when order is not semantically important.
2. Reset indexes only when index values are not part of the expected result.
3. Preserve index assertions when output identity depends on input index.

## Geometry Equality Fails after Reprojection or Overlay

Likely cause: floating-point differences, precision changes, or geometry type changes.

Fix:

1. Compare in the CRS and precision appropriate for the task.
2. Use approximate geometry equality only when numerical tolerance is expected.
3. Check `geom_type`, `.is_valid`, and `.is_empty` before relaxing equality.

## Optional Dependency Test Fails

Symptoms: tests fail with missing `pyarrow`, `fiona`, matplotlib, folium, mapclassify, geopy, SQLAlchemy, psycopg, or PostGIS service errors.

Fix:

1. Confirm whether the changed workflow requires that dependency.
2. If optional and unrelated, skip or avoid that test selection.
3. If required for the change, install the focused optional package/service and rerun only the relevant tests.
4. Keep real network/provider/database tests opt-in and credential-aware.

## Native Test Command Is Too Broad

If a task only changes one workflow, do not start with the whole suite. Build a sequence:

1. Bundled skill smoke script for the workflow.
2. One focused native test file or selected test functions.
3. Adjacent files that share the changed API.
4. Broader suite only after focused checks pass or risk warrants it.

## pandas Equality Used on Geometry Data

Symptoms: pandas assertion compares object arrays, ignores CRS, or produces confusing Shapely object diffs.

Fix: switch to `geopandas.testing.assert_geodataframe_equal` or `assert_geoseries_equal`, then deliberately choose flags for CRS, index, geometry type, and tolerance.
