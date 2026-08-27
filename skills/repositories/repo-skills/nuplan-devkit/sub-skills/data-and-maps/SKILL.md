---
name: data-and-maps
description: "Use for nuPlan dataset roots and layout, SQLite/ORM queries,
  sensor blobs, map layers and objects, or scenario builder and scenario filter
  selection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# nuPlan data and maps

Use this sub-skill when the task is about the local nuPlan dataset contract rather
than model training, simulation metrics, or submission presentation. It covers
DB discovery, schema-aware read queries, camera/lidar blob lookup, map API
objects/layers, and `NuPlanScenarioBuilder` selection.

## Route the request

1. Establish the three roots before querying anything:
   `NUPLAN_DATA_ROOT` for DBs and sensor data, `NUPLAN_MAPS_ROOT` for maps, and
   `NUPLAN_EXP_ROOT` only for experiment/cache output. Do not use the experiment
   root as a dataset root.
2. Select the split path (`nuplan-v1.1/splits/mini`, `trainval`, or the
   challenge `test` path) and confirm that it contains `.db` files.
3. Run the bundled read-only validator first:
   `python scripts/validate_nuplan_data_root.py --data-root "$NUPLAN_DATA_ROOT" --maps-root "$NUPLAN_MAPS_ROOT"`.
   Add `--split mini`, `--db-limit N`, or `--json` when a bounded report is
   preferable. A non-zero exit is actionable evidence, not a reason to fetch
   data automatically.
4. For DB facts, prefer `get_db_description`, `get_db_duration_in_us`,
   `get_db_log_duration`, `get_db_log_vehicles`, and `get_db_scenario_info`.
   For custom reads use `execute_one` or `execute_many` with bound values; never
   interpolate user values into SQL.
5. For map facts, construct the map DB with the requested map version, then use
   `NuPlanMapFactory`, `get_maps_api`, `NuPlanMap`, or the compatibility
   `NuPlanMapWrapper` described in [maps and scenarios](references/maps-and-scenarios.md).
6. For scenarios, keep DB selection and scenario filtering separate: construct
   `NuPlanScenarioBuilder`, create a complete `ScenarioFilter`, call
   `get_scenarios`, and inspect the count/type/map before expanding downstream
   processing.

## Dataset contract

The documented local roots are:

| Variable | Meaning | Typical derived paths |
| --- | --- | --- |
| `NUPLAN_DATA_ROOT` | Read-mostly dataset root | `nuplan-v1.1/splits/<split>`, `nuplan-v1.1/sensor_blobs` |
| `NUPLAN_MAPS_ROOT` | Map package root | `<map_version>.json`, `<location>/<local-version>/map.gpkg` |
| `NUPLAN_EXP_ROOT` | Writable experiment/cache root | `exp`, `cache` |

The standard map version is `nuplan-maps-v1.0`. Its metadata names four map
locations: `sg-one-north`, `us-ma-boston`, `us-nv-las-vegas-strip`, and
`us-pa-pittsburgh-hazelwood`. The location version below each location is not
necessarily the map package version; read it from the metadata JSON.

A DB stores metadata, annotations, and relative blob keys; it does not embed
JPEG images or point clouds. The sensor root must therefore resolve the
`image.filename_jpg` and `lidar_pc.filename` keys. Camera channels normally
include `CAM_F0`, `CAM_B0`, `CAM_L0`, `CAM_L1`, `CAM_L2`, `CAM_R0`, `CAM_R1`,
and `CAM_R2`; merged lidar uses `MergedPointCloud`.

Read [dataset layout](references/dataset-layout.md) for path resolution and
split/version checks, and [database and schema](references/database-and-schema.md)
for tables, joins, tokens, and query helpers.

## API selection

- Use `nuplan.database.nuplan_db.query_session.execute_many` for streaming
  SQLite rows and `execute_one` for a query that must return at most one row.
- Use `nuplan.database.nuplan_db.db_cli_queries` for DB description, duration,
  per-log duration/vehicle, and scenario-type counts. Those helpers are
  read-only and accept a DB filename.
- Use `NuPlanDB` and its typed table properties (`log`, `camera`, `lidar`,
  `ego_pose`, `image`, `lidar_pc`, `lidar_box`, `track`, `scene`,
  `scenario_tag`, and `traffic_light_status`) for ORM-style access.
- Use `get_lidarpc_sensor_data()` or `get_camera_channel_sensor_data(channel)`
  to define sensor queries. Sensor tokens are hex strings at the Python API
  boundary but are stored as SQLite BLOB values.
- Use semantic map layers and object methods for geometric questions; do not
  treat a GeoPackage layer name as a `SemanticMapLayer` enum without checking
  the mapping.

## Scenario selection checklist

`ScenarioFilter` requires all of these positional fields:
`scenario_types`, `scenario_tokens`, `log_names`, `map_names`,
`num_scenarios_per_type`, `limit_total_scenarios`, `timestamp_threshold_s`,
`ego_displacement_minimum_m`, `expand_scenarios`, `remove_invalid_goals`, and
`shuffle`. Optional fields are `ego_start_speed_threshold`,
`ego_stop_speed_threshold`, `speed_noise_tolerance`, `token_set_path`,
`fraction_in_token_set_threshold`, and `ego_route_radius`.

`num_scenarios_per_type` is a positive integer. `limit_total_scenarios` is a
positive integer count or a float in `(0, 1]` (the implementation's float
sampling path requires a value strictly below 1 when filtering). Filters are
applied in builder order: per-type count, total count, timestamp spacing,
non-stationary ego, start/stop speed, token-set fraction, and route presence.
`scenario_types`, `map_names`, `log_names`, and tokens are applied while reading
DB rows. `remove_invalid_goals` and `include_cameras` can remove rows before
later filters. A zero result usually means a split, map name, log name, goal,
route, or filter combination is wrong—not that the database is empty.

## Boundaries and safety

- Route metric, simulation, and evaluation questions to
  `simulation-and-evaluation`; route feature construction and training cache
  questions to `training-and-preprocessing`; route command formatting to
  `submission-and-cli`.
- Treat S3/HTTP blob stores as optional. This sub-skill diagnoses local layout;
  it does not download data, set credentials, or promise remote availability.
- Never mutate, purge, repair, or delete dataset files as part of diagnosis.
  Use the bundled validator and read-only queries, then report the missing
  data item and the smallest user-controlled recovery action.
- Preserve the distinction between DB `log.map_version` (a location/map name
  in scenario queries) and the requested package map version
  (`nuplan-maps-v1.0`).
- When data is missing, record the exact root, split, map version, DB basename,
  channel, and referenced blob key that failed. Do not silently substitute a
  different split or map.

For detailed joins, map conventions, scenario examples, and failure recovery,
read the linked references before answering a complex request.
