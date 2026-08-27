# Configuration and merge semantics

OpenCDA 0.1.3 uses OmegaConf. A scenario run combines:

```text
default = opencda/scenario_testing/config_yaml/default.yaml
specific = opencda/scenario_testing/config_yaml/<scenario>.yaml
merged = OmegaConf.merge(default, specific)
```

The specific file is an override, not a complete replacement. Keep the file
small and copy only keys that differ from `default.yaml`. OmegaConf's nested
merge preserves unspecified defaults and replaces scalar values or the
corresponding nested values supplied by the scenario. Lists are replaced as a
value rather than appended; write the complete list when changing
`vehicle_list`, camera positions, CAV lists, or platoon members. The supplied
examples also use YAML anchors/aliases (`&name`, `*name`) and merge keys
(`<<: *name`) for reusable nested defaults. Validate that the installed
OmegaConf version accepts the syntax before relying on anchors in a custom
file.

## Core keys

The following are the operational groups in `default.yaml`:

- `world`: `sync_mode`, `client_port`, `fixed_delta_seconds`, `seed`, and
  `weather` fields (`sun_altitude_angle`, `cloudiness`, `precipitation`,
  `precipitation_deposits`, `wind_intensity`, `fog_density`, `fog_distance`,
  `fog_falloff`, `wetness`). `sync_mode: true` is required by the CARLA
  `ScenarioManager` in this release; async mode exits with an error. Keep
  `carla_traffic_manager.sync_mode` consistent with it.
- `rsu_base`: RSU sensing/perception/localization defaults.
- `vehicle_base`: CAV sensing, camera/lidar, localization, map manager,
  safety manager, behavior/local planner, controller, and V2X defaults.
  Important switches include `sensing.perception.activate`,
  `sensing.localization.activate`, `map_manager.activate`, and `v2x.enabled`.
- `carla_traffic_manager`: `sync_mode`, `global_distance`,
  `global_speed_perc`, `set_osm_mode`, `auto_lane_change`,
  `ignore_lights_percentage`, `random`, `vehicle_list`, and `range`.
  `vehicle_list` as a list gives explicit `spawn_position` entries. A null or
  non-list value selects range spawning and uses range rows of
  `[x_min, x_max, y_min, y_max, x_step, y_step, vehicle_num]`.
- `platoon_base`: `max_capacity`, `inter_gap`, `open_gap`, `warm_up_speed`,
  leader speed profile controls, and stage duration.
- `scenario`: `single_cav_list` and `platoon_list`; scenario entries can
  override vehicle/platoon defaults and must contain valid spawn/destination
  structures for their module.
- `sumo` (co-simulation only): `port`, `host`, `gui`, `client_order`, and
  `step_length`. The step length must agree with CARLA's fixed delta.
- `scenario_runner` (OpenSCENARIO path): the supplied configuration selects a
  town for ScenarioRunner; ScenarioRunner/OpenSCENARIO remains an external
  prerequisite.
- `blueprint` (optional): custom blueprint metadata/probabilities. The
  referenced metadata file must exist at runtime if `use_multi_class_bp` is
  enabled.

## Minimal ML-disabled override

A minimal override should preserve the default sensor structure and change
only the needed switches, for example:

```yaml
vehicle_base:
  sensing:
    perception:
      activate: false
scenario:
  single_cav_list: []
  platoon_list: []
```

This does not make a run simulator-free: the scenario module may expect CAV
entries and a map-specific spawn helper. For a real benchmark, start from the
matching checked-in scenario YAML and change only the intended nested keys.
Do not remove required `world`, `vehicle_base`, or `scenario` structure to
"disable ML"; disabling perception is not the same as removing its
configuration.

## Common override patterns

```yaml
world:
  client_port: 2001
  weather:
    cloudiness: 40
    precipitation: 10

vehicle_base:
  map_manager:
    activate: false
    visualize: false
  sensing:
    perception:
      activate: false
      camera:
        num: 0
        positions: []

carla_traffic_manager:
  vehicle_list: []
  global_distance: 5
```

Check the effective structure before running. A plain text/YAML parser can
catch indentation and syntax errors, but only OmegaConf can reproduce the
actual interpolation/merge behavior. Use a throwaway Python command such as
`python -c "from omegaconf import OmegaConf; print(OmegaConf.merge(OmegaConf.load('opencda/scenario_testing/config_yaml/default.yaml'), OmegaConf.load('opencda/scenario_testing/config_yaml/single_2lanefree_carla.yaml')) )"`
from the repository root; this loads configuration only and does not start
CARLA. Never use an untrusted config with arbitrary constructor/evaluation code
without reviewing the scenario module that consumes it.
