# Database, schema, and sensor queries

## Exact SQLite table set

A standard nuPlan DB is SQLite. The exact table set used by the devkit is:
`category`, `log`, `camera`, `lidar`, `ego_pose`, `image`, `lidar_pc`,
`track`, `lidar_box`, `scene`, `scenario_tag`, and `traffic_light_status`.
Primary keys and foreign keys are SQLite `BLOB` values even though the Python
query boundary usually exposes tokens as hexadecimal strings.

The complete documented column inventory is:

| Table | Columns |
| --- | --- |
| `category` | `token`, `name`, `description` |
| `log` | `token`, `vehicle_name`, `date`, `timestamp`, `logfile`, `location`, `map_version` |
| `camera` | `token`, `log_token`, `channel`, `model`, `translation`, `rotation`, `intrinsic`, `distortion`, `width`, `height` |
| `lidar` | `token`, `log_token`, `channel`, `model`, `translation`, `rotation` |
| `ego_pose` | `token`, `timestamp`, `x`, `y`, `z`, `qw`, `qx`, `qy`, `qz`, `vx`, `vy`, `vz`, `acceleration_x`, `acceleration_y`, `acceleration_z`, `angular_rate_x`, `angular_rate_y`, `angular_rate_z`, `epsg`, `log_token` |
| `image` | `token`, `next_token`, `prev_token`, `ego_pose_token`, `camera_token`, `filename_jpg`, `timestamp` |
| `lidar_pc` | `token`, `next_token`, `prev_token`, `ego_pose_token`, `lidar_token`, `scene_token`, `filename`, `timestamp` |
| `track` | `token`, `category_token`, `width`, `length`, `height` |
| `lidar_box` | `token`, `lidar_pc_token`, `track_token`, `next_token`, `prev_token`, `x`, `y`, `z`, `width`, `length`, `height`, `vx`, `vy`, `vz`, `yaw`, `confidence` |
| `scene` | `token`, `log_token`, `name`, `goal_ego_pose_token`, `roadblock_ids` |
| `scenario_tag` | `token`, `lidar_pc_token`, `type`, `agent_track_token` |
| `traffic_light_status` | `token`, `lidar_pc_token`, `lane_connector_id`, `status` |

`image` and `lidar_pc` contain metadata only: JPEG and point-cloud bytes are
in the sensor blob store. `scene.roadblock_ids` is a route string consumed by
map lookup; preserve the stored delimiter and inspect the actual value before
splitting it.

## Stable read helpers

For common read-only facts, use the DB CLI helpers. They accept a DB filename:

```python
from nuplan.database.nuplan_db.db_cli_queries import (
    get_db_description,
    get_db_duration_in_us,
    get_db_log_duration,
    get_db_log_vehicles,
    get_db_scenario_info,
)
```

- `get_db_description(db_file)` returns table descriptions, columns, and row
  counts.
- `get_db_duration_in_us(db_file)` returns max minus min `lidar_pc.timestamp`
  in microseconds; an empty lidar table cannot provide a duration.
- `get_db_log_duration(db_file)` yields `(logfile, duration_us)` after joining
  `log`, `scene`, and `lidar_pc`, sorted by logfile.
- `get_db_log_vehicles(db_file)` yields `(logfile, vehicle_name)`.
- `get_db_scenario_info(db_file)` yields `(scenario_type, count)` ordered by
  descending count.

For custom reads use the fixed, code-controlled SQL text with bound values:

```python
from nuplan.database.nuplan_db.query_session import execute_many, execute_one

for row in execute_many(
    "SELECT logfile, location, map_version FROM log ORDER BY logfile",
    (),
    db_file,
):
    print(row["logfile"], row["location"], row["map_version"])

row = execute_one(
    "SELECT COUNT(*) AS count FROM lidar_pc WHERE timestamp >= ?",
    (start_timestamp_us,),
    db_file,
)
```

`execute_many` streams any number of rows. `execute_one` returns zero or one
row and raises `RuntimeError` if the query returns multiple rows. SQL
identifiers cannot be bound, so table and column names must remain fixed by
trusted code; user values belong in `?` parameters. The helper itself opens a
normal SQLite connection, so use `SELECT` statements and a trusted local DB
when strict read-only behavior is required. The bundled validator separately
uses SQLite `mode=ro`.

For a token filter, convert a hex token to the SQLite BLOB representation:

```python
row = execute_one(
    "SELECT timestamp FROM lidar_pc WHERE token = ?",
    (bytearray.fromhex(lidar_pc_token),),
    db_file,
)
```

Never compare a hex string directly to a BLOB parameter and never interpolate a
user token into SQL.

## ORM and sensor sources

The typed ORM class is imported from
`nuplan.database.nuplan_db_orm.nuplandb`:

```python
from nuplan.database.nuplan_db_orm.nuplandb import NuPlanDB

db = NuPlanDB(data_root, load_path, maps_db=None, verbose=False)
log_name = db.log_name       # log.logfile
map_name = db.map_name       # log.map_version
rows = db.lidar_pc.select_many(scene_token=scene_token)
```

`NuPlanDB` exposes typed table properties `category`, `log`, `camera`, `lidar`,
`ego_pose`, `image`, `lidar_pc`, `lidar_box`, `track`, `scene`,
`scenario_tag`, and `traffic_light_status`. A table supports token lookup,
`get`, `select_one`, `select_many`, `count`, `all`, `len`, slices, and
iteration. Call `detach_tables()` only when all DB queries are finished.

Use the declared sensor source rather than hand-writing a camera/lidar join:

```python
from nuplan.database.nuplan_db.nuplan_db_utils import (
    get_camera_channel_sensor_data,
    get_lidarpc_sensor_data,
)

lidar_source = get_lidarpc_sensor_data()
# SensorDataSource(table='lidar_pc', sensor_table='lidar',
#                  sensor_token_column='lidar_token', channel='MergedPointCloud')
front_source = get_camera_channel_sensor_data("CAM_F0")
# SensorDataSource(table='image', sensor_table='camera',
#                  sensor_token_column='camera_token', channel='CAM_F0')
```

Useful query functions in `nuplan.database.nuplan_db.nuplan_scenario_queries`
include `get_sensor_token_by_index_from_db`,
`get_end_sensor_time_from_db`, `get_sensor_data_token_timestamp_from_db`,
`get_sensor_token_map_name_from_db`,
`get_sampled_sensor_tokens_in_time_window_from_db`,
`get_sensor_data_from_sensor_data_tokens_from_db`,
`get_sensor_transform_matrix_for_sensor_data_token_from_db`, `get_images_from_lidar_tokens`,
`get_cameras`, `get_statese2_for_lidarpc_token_from_db`,
`get_ego_state_for_lidarpc_token_from_db`,
`get_mission_goal_for_sensor_data_token_from_db`,
`get_roadblock_ids_for_lidarpc_token_from_db`, and
`get_traffic_light_status_for_lidarpc_token_from_db`. Timestamps are integer
microseconds; lidar is normally 20 Hz and images normally 10 Hz.

## Scenario SQL boundary

`get_scenarios_from_db` applies DB-side `filter_tokens`, `filter_types`, and
`filter_map_names`. The map filter compares `filter_map_names` to
`log.map_version`, not to `nuplan-maps-v1.0`. It joins `lidar_pc` to `lidar`
and `log`, left-joins `scenario_tag`, and keeps only scenes with at least two
ordered scenes before and after the selected scene. Untagged rows may return
`scenario_type=None` and are mapped by builder code to its default `unknown`
name. `include_cameras=True` adds an image join; disabling invalid mission
goals adds scene/goal-pose joins. Any of these joins can remove rows before
later scenario-level filters run.

## Remote-store limit

S3/HTTP support is optional and controlled by the devkit's remote-store
configuration (`NUPLAN_DATA_STORE`, `NUPLAN_DATA_ROOT_S3_URL`, and related
HTTP/S3 roots). A missing local blob may be fetched and cached by scenario
loading when remote mode is deliberately enabled. The validator in this
bundle never contacts a remote store, never sets credentials, and never
repairs a local DB. Record the exact DB, table, column, and relative blob key
that is missing instead of promising remote availability. Large datasets also
make full blob verification expensive: use bounded validator samples and
`--db-limit`, then state the coverage limit.
