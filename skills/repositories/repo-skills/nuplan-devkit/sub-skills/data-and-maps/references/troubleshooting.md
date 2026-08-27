# Data, map, and scenario troubleshooting

Run `scripts/validate_nuplan_data_root.py` before importing the ORM, map, or
scenario builder. It is local-only and read-only. Exit codes are `0` for no
errors, `1` for a missing/invalid required layout, `2` for CLI usage errors,
and `3` for an unexpected validator failure. `--json` is suitable for a
machine-readable handoff.

## Failure matrix

| Symptom | Evidence to collect | Safe recovery |
| --- | --- | --- |
| `NUPLAN_DATA_ROOT` or `NUPLAN_MAPS_ROOT` is wrong | Print explicit roots and selected split; run validator with CLI paths | Set the variables for the launching process or pass explicit arguments. Do not create a new tree just to satisfy the check. |
| Split has no `.db` files | Confirm `mini`, `trainval`, or challenge `test`; inspect archive extraction and any explicit `db_files` override | Select the intended split or explicit local DB. The validator never downloads an archive. |
| Missing required SQLite table/column | Run with `--json`; use `get_db_description` on the exact DB | Treat the file as non-nuPlan, partial, or schema-incompatible and replace it from the approved source. Do not run repair SQL. |
| `sqlite-open` or malformed DB | Record DB basename and read-only error | Check permissions and file integrity. Do not let an inspection command write a journal or migrate the DB. |
| Missing map metadata JSON | Confirm `maps-root` and exact package version, normally `nuplan-maps-v1.0.json` | Point at the approved maps root/package. Do not rename a location version or rely on remote fallback during local diagnosis. |
| Metadata location has no `map.gpkg` | Record location, metadata `version`, and computed path | Restore the matching location package through the user's approved source, then rerun the validator. |
| DB `log.location` is absent from map metadata | Record `log.location`, `log.map_version`, package version, and metadata locations | Resolve the correct map package or treat the DB/map pairing as incompatible. `log.map_version` is not the package filename. |
| Map API creates locks or attempts a long download | `GPKGMapsDB` was constructed before a local check; inspect `NUPLAN_DATA_STORE` and remote roots | Stop using the map API for diagnosis; run the validator first. Clear only user-approved caches outside this skill's read-only procedure. |
| GeoPackage exists but layer is unavailable | Call `vector_layer_names(location)` only in an approved map runtime and distinguish raw names from `SemanticMapLayer` values | Use the layer list and semantic mapping. `DRIVABLE_AREA` and lane-connector point containment have special mappings. |
| `NuPlanMapWrapper` says a name is not a vector layer | A raster, semantic, or unsupported raw name was passed to `load_vector_layer` | Use `load_raster_layer_as_numpy` for raster data and a listed raw vector layer for vector calls. |
| Sensor root is unset or missing | Record explicit sensor root and the exact DB-relative key from `image.filename_jpg` or `lidar_pc.filename` | Pass the correct `sensor_root` and restore the matching local blob. An omitted optional sensor root is an incomplete sensor check, not permission to invent a path. |
| Sensor blob is missing | Record DB basename, table/column, channel, and relative key; check containment below sensor root | Restore the exact sensor archive or explicitly provision approved remote mode. The validator does not download or cache it. |
| Image lookup returns no row/blob | Check `include_cameras`, camera channel, anchor `ego_pose_token`, and `camera`/`image` join | Use a channel present in the DB and enable cameras only when needed. Do not substitute a different channel. |
| Low-level token query returns no row | Hex token was bound as text, token belongs to another DB, or the sensor source/channel is wrong | Bind `bytearray.fromhex(token)` and use `SensorDataSource` helpers. |
| `execute_one` reports multiple rows | Cardinality assumption is false | Use `execute_many` or add a fixed, code-controlled uniqueness predicate. Never hide the condition by taking the first row. |
| ORM `select_one` returns `None` | Exact/case-sensitive field mismatch or wrong DB | Inspect exact `db.log_name`, `db.map_name`, and controlled `count`/`select_many` results. |
| `ScenarioFilter` rejects construction | Missing required positional field, non-positive count, or invalid limit type | Supply all 11 required fields; use positive integer counts. Use a float strictly below `1.0` for the builder's fractional filter. |
| Plausible DB yields zero scenarios | `log_names` suffix, map name, scenario type, goal/camera join, or valid-scene boundary | Start broad with no nullable DB filters and `remove_invalid_goals=False`; inspect `get_db_scenario_info`; add one filter at a time. |
| Route filter yields zero | Wrong map root/package/location, no nearby on-route lane, or radius too small | Verify map identity and route IDs, then intentionally adjust `ego_route_radius`. |
| Timestamp filter removes too much | Threshold is seconds while DB timestamps are microseconds | Lower the threshold deliberately or unset it; it is a scenario-spacing filter, not the sensor rate. |
| Fractional limit keeps tagged types but loses `unknown` | This is the documented prioritization behavior | Inspect per-type counts; use an explicit integer/per-type policy if class balance is required. |
| Remote DB/S3 path asks for credentials or stalls | Optional remote store unavailable, wrong URL, or no credentials | Record remote dependency and missing local artifact. Ask the user to provision/approve remote access; never set credentials or download as part of diagnosis. |

## Filter-zero recovery recipe

Use a reproducible narrowing record:

1. Run the validator with the exact `--data-root`, `--maps-root`, `--split`, and
   bounded `--db-limit`.
2. Select the DB by basename without `.db`; inspect its log identity and
   `get_db_scenario_info`.
3. Construct `ScenarioFilter` with all required fields, but leave nullable
   selection and later filters unset where possible.
4. Compare counts after DB-side type/token/map selection, then after
   `remove_invalid_goals` and `include_cameras`.
5. Add builder filters in their actual order and record the count after each:
   per-type, total, timestamp, displacement, start, stop, token set, route.
6. When a stage reaches zero, revert only that stage for diagnosis and report
   the exact restrictive value; do not silently broaden the user's requested
   result.

For a zero at the DB stage, remember the SQL requires a valid scene with at
least two preceding and two following ordered scenes. For a zero at the route
stage, map loading and route IDs are lazy and may fail only after DB selection.

## Escalation record

If local recovery is not possible, hand off:

- explicit data, maps, sensor roots (redact credentials);
- selected split and map package version;
- DB basename, `log.location`, and `log.map_version`;
- missing table, column, map metadata, location package, layer, channel, or
  relative blob key;
- validator command and exit code;
- controlled query or builder error;
- whether the evidence is complete local, partial local, or remote-dependent;
- `--db-limit`/blob-sample limits that constrain coverage.

Do not silently change split, DB, map package, location, camera channel, filter,
or remote store. A present `map.gpkg` proves a file exists, not that every layer
is usable; a bounded blob sample proves only the sampled references.
