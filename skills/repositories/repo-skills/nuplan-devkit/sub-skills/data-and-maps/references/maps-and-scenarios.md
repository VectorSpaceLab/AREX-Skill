# Maps and scenario construction

## Constructing a map API

The package version and location are separate arguments. Use the package
metadata version for the second argument and the DB's location/map name for the
third:

```python
from nuplan.common.maps.nuplan_map.map_factory import get_maps_api

map_api = get_maps_api(
    map_root,
    "nuplan-maps-v1.0",
    "us-ma-boston",
)
```

For factory or compatibility access:

```python
from nuplan.common.maps.nuplan_map.map_factory import NuPlanMapFactory, get_maps_db
from nuplan.database.maps_db.map_api import NuPlanMapWrapper

maps_db = get_maps_db(map_root, "nuplan-maps-v1.0")
map_api = NuPlanMapFactory(maps_db).build_map_from_name("us-ma-boston")
legacy_api = NuPlanMapWrapper(maps_db, "us-ma-boston")
```

`get_maps_db(map_root, map_version)` is cached. The direct constructor is
`GPKGMapsDB(map_version, map_root)`, with argument order intentionally
reversed from `get_maps_db`. `GPKGMapsDB` reads `<map_version>.json`, uses the
metadata location version to find `location/<version>/map.gpkg`, and exposes
`get_locations()`, `get_version(location)`, `version_names`, `layer_names`,
`vector_layer_names`, `get_raster_layer_names`, `load_vector_layer`, and
`load_layer`.

The current `GPKGMapsDB` constructor initializes a `.maplocks` directory and
loads a dummy vector layer for each standard location; depending on
`NUPLAN_DATA_STORE` and configured remote roots this can download/cache absent
maps. Do not construct it as part of a local-only layout diagnosis. Run the
bundled validator first; it checks presence without creating locks or contacting
S3/HTTP.

The four standard locations are `sg-one-north`, `us-ma-boston`,
`us-nv-las-vegas-strip`, and `us-pa-pittsburgh-hazelwood`. `NuPlanMapFactory`
and `get_maps_api` remove a trailing `.gpkg` from a map name, but passing the
location name is clearer.

## Semantic map objects and layers

Coordinates for vector queries are projected global metres, represented by
`Point2D`, not raster pixels. The current `NuPlanMap` semantic-to-vector
mapping is:

| `SemanticMapLayer` | GeoPackage layer |
| --- | --- |
| `LANE` | `lanes_polygons` |
| `ROADBLOCK` | `lane_groups_polygons` |
| `INTERSECTION` | `intersections` |
| `STOP_LINE` | `stop_polygons` |
| `CROSSWALK` | `crosswalks` |
| `DRIVABLE_AREA` | `drivable_area` |
| `LANE_CONNECTOR` | `lane_connectors` (point containment also loads `gen_lane_connectors_scaled_width_polygons`) |
| `ROADBLOCK_CONNECTOR` | `lane_group_connectors` |
| `BASELINE_PATHS` | `baseline_paths` |
| `BOUNDARIES` | `boundaries` |
| `WALKWAYS` | `walkways` |
| `CARPARK_AREA` | `carpark_areas` |

Use the semantic API for semantic questions:

- `get_available_map_objects()` and `get_available_raster_layers()` list
  supported enum layers.
- `get_map_object(object_id, layer)` resolves a known string ID.
- `get_all_map_objects(Point2D(x, y), layer)` returns containing objects;
  `get_one_map_object` returns `None` for none and asserts if multiple exist.
- `get_proximal_map_objects(point, radius, layers)` searches a square patch.
- `get_distance_to_nearest_map_object(point, layer)` returns `(id, distance)`.
- `is_in_layer(point, layer)` answers point containment.
- `get_raster_map_layer(layer)` and `get_raster_map(layers)` return raster data.

Semantic enum names and raw GeoPackage names are not interchangeable. For
example, use `SemanticMapLayer.LANE` with `NuPlanMap`, but
`lanes_polygons` with raw layer methods. `DRIVABLE_AREA` has a semantic raster
and vector representation named `drivable_area`; do not assume a raw layer
called `drivable_area` is valid for every compatibility patch helper. Check
`vector_layer_names(location)` first.

`NuPlanMapWrapper` compatibility methods include
`load_vector_layer(layer_name)`, `load_raster_layer_as_numpy(layer_name)`,
`get_map_dimension()`, `get_map_aspect_ratio()`, `get_bounds(layer_name,
tokens=None)`, `layers_on_point(x, y, layer_names=None)`,
`records_on_point(x, y, layer_name)`,
`get_records_in_patch([x_min, y_min, x_max, y_max], layer_names, mode)` with
`mode` `intersect` or `within`, `get_patch_coord([x_center, y_center, height,
width], angle_degrees)`, `get_layer_polygon`, and `get_layer_line`. The patch
box order is center-x, center-y, height, width. Raster and vector coordinates
must stay in their respective coordinate systems.

## Scenario builder and exact filter contract

The standard builder is:

```python
from nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_builder import NuPlanScenarioBuilder

builder = NuPlanScenarioBuilder(
    data_root=data_root,
    map_root=map_root,
    sensor_root=sensor_root,
    db_files=db_files,                 # None, path, directory, or list
    map_version="nuplan-maps-v1.0",
    include_cameras=False,
)
```

Build a complete `ScenarioFilter` before calling `builder.get_scenarios`; its
required positional fields are:

```text
scenario_types, scenario_tokens, log_names, map_names,
num_scenarios_per_type, limit_total_scenarios, timestamp_threshold_s,
ego_displacement_minimum_m, expand_scenarios, remove_invalid_goals, shuffle
```

Its optional fields are:

```text
ego_start_speed_threshold, ego_stop_speed_threshold,
speed_noise_tolerance, token_set_path,
fraction_in_token_set_threshold, ego_route_radius
```

The meanings are:

| Field | Behavior |
| --- | --- |
| `scenario_types` | Allowlisted `scenario_tag.type` values; untagged rows become `unknown` in builder output. |
| `scenario_tokens` | Allowlisted scenario token values as configured by callers. |
| `log_names` | DB basenames without `.db`; compared by `absolute_path_to_log_name`. |
| `map_names` | Compared to `log.map_version`, not the map package version. |
| `num_scenarios_per_type` | Positive integer per-type cap; random sample when shuffled, equisampling otherwise. |
| `limit_total_scenarios` | Positive integer cap, or a float strictly in `(0, 1)` in the filtering implementation. |
| `timestamp_threshold_s` | Minimum spacing between retained initial lidar timestamps, in seconds; DB timestamps are microseconds. |
| `ego_displacement_minimum_m` | Inclusive cumulative ego-center displacement in metres. |
| `expand_scenarios` | Expand a mapped multi-sample scenario into single-sample scenarios. |
| `remove_invalid_goals` | Remove rows whose scene goal pose cannot be joined/resolved. |
| `shuffle` | Randomize sampling and final order; false yields sorted scenario tokens after flattening. |
| `ego_start_speed_threshold` | Require a rising edge strictly above the speed threshold. |
| `ego_stop_speed_threshold` | Require a falling edge to or below the threshold. |
| `speed_noise_tolerance` | Ignore smaller start/stop speed changes; the implementation defaults to `0.1` when omitted during edge detection. |
| `token_set_path` | JSON list of lidar-PC token strings used by the token-set filter. |
| `fraction_in_token_set_threshold` | Keep a scenario when its token fraction is strictly greater than the threshold, except threshold `1` requires exact set equality. |
| `ego_route_radius` | Require a nearby lane segment whose roadblock ID intersects the scenario route. |

`ScenarioFilter.__post_init__` requires positive
`num_scenarios_per_type`, positive integer total limits, and float limits in
`(0, 1]`; the later `filter_total_num_scenarios` implementation rejects a
float exactly equal to `1.0`, so use an integer for “keep all” or leave the
field unset. The builder applies enabled filters in this order:

1. per-type count;
2. total count;
3. timestamp spacing;
4. non-stationary ego displacement;
5. start-speed edge;
6. stop-speed edge;
7. token-set fraction;
8. route presence.

DB-side scenario selection happens before that sequence. It can already remove
rows through type/token/map filters, camera inclusion, invalid-goal joins, and
the valid-scene boundary (the SQL deliberately drops the first two and last
scene positions).

## Recovering from zero scenarios

A zero result is usually an over-constrained selection, not an empty DB. Check
in this order without silently broadening the request:

1. Run the validator for the selected split and verify the selected DB files.
2. Inspect `get_db_scenario_info(db_file)` for actual tag types and inspect
   `log.logfile`, `log.location`, and `log.map_version`.
3. Remove `.db` from `log_names`; use the exact DB `map_version` in
   `map_names`, not `nuplan-maps-v1.0`.
4. Start with nullable type/token/log/map filters unset,
   `remove_invalid_goals=False`, `include_cameras=False`, and no later
   sampling filters. Add one restriction at a time and record counts.
5. Confirm the DB has enough ordered scenes and lidar rows for the valid-scene
   boundary; very small synthetic DBs can legitimately yield zero scenarios.
6. If camera inclusion is enabled, verify a matching image at the anchor pose
   and the requested channel. If goal removal is enabled, inspect the scene's
   `goal_ego_pose_token` join.
7. If route filtering is enabled, verify map package/version/location first,
   then compare route roadblock IDs with nearby vector-map roadblocks. Change
   `ego_route_radius` only intentionally.
8. Check timestamp threshold units, ego displacement, speed edges, and token-set
   JSON last. Note that total-limit filtering removes `unknown` scenarios first
to preserve tagged classes, so a fractional limit can yield few or no unknowns.

## Remote and data limits

S3/HTTP DB, map, and sensor roots are optional deployment features, not a
recovery shortcut. Remote scenario loading can download a DB or blob and cache
it locally; `GPKGMapsDB` can download maps and create map locks. This sub-skill
never enables credentials or downloads data. State whether evidence is local,
partial, or remote-dependent, and include the exact split, DB basename, map
package/location, channel, and relative blob key in an escalation. The
validator's `--db-limit` and blob sample bound are intentional for large
archives and do not prove complete dataset integrity.
