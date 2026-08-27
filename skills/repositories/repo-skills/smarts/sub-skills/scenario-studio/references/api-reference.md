# Scenario Studio API reference

Verified against SMARTS package version 2.0.1 in the prepared Python 3.11
inspection environment. Prefer the public alias `from smarts.sstudio import
types as t`; it exposes the authoring types from `smarts.sstudio.sstypes`.

## Live signatures

```text
Scenario(
  map_spec: Optional[MapSpec] = None,
  traffic: Optional[Dict[str, Traffic]] = None,
  ego_missions: Optional[Sequence[Union[Mission, EndlessMission]]] = None,
  social_agent_missions: Optional[
    Dict[str, Tuple[Sequence[SocialAgentActor], Sequence[Mission]]]
  ] = None,
  bubbles: Optional[Sequence[Bubble]] = None,
  friction_maps: Optional[Sequence[RoadSurfacePatch]] = None,
  traffic_histories: Optional[
    Sequence[Union[TrafficHistoryDataset, str]]
  ] = None,
  scenario_metadata: Optional[ScenarioMetadata] = <default metadata>,
) -> None

MapSpec(
  source: str,
  lanepoint_spacing: float = 1.0,
  default_lane_width: Optional[float] = None,
  shift_to_origin: bool = False,
  builder_fn: Callable[[Any], Tuple[Optional[RoadMap], Optional[str]]] = get_road_map,
) -> None

Traffic(
  flows: Sequence[Flow],
  trips: Optional[Sequence[Trip]] = None,
  engine: str = "SUMO",
) -> None

Flow(
  route: Union[RandomRoute, Route],
  rate: float,
  begin: float = 0,
  end: float = 3600,
  actors: Dict[TrafficActor, float] = {},
  randomly_spaced: bool = False,
  repeat_route: bool = False,
) -> None

Route(
  begin: Tuple[str, int, Any],
  end: Tuple[str, int, Any],
  via: Tuple[str, ...] = (),
  map_spec: Optional[MapSpec] = None,
) -> None

Mission(
  route: Union[RandomRoute, Route],
  via: Tuple[Via, ...] = (),
  start_time: float = sys.maxsize,
  entry_tactic: Optional[EntryTactic] = None,
) -> None

gen_scenario(scenario: Scenario, output_dir: Union[str, Path], seed: int = 42)
```

The displayed default for `Mission.start_time` is the package's missing-value
sentinel (`sys.maxsize` in this release). Prefer `EntryTactic(start_time=...)`
when delayed entry is needed; passing a legacy non-sentinel `start_time` emits a
deprecation warning.

## Core authoring objects

- `TrafficActor(name=..., ...)` describes traffic behavior. Useful fields include
  `speed=Distribution(mean=..., sigma=...)`, `depart_speed`, `vehicle_type`,
  `min_gap`, and lane/junction models. Flow actor weights are relative weights,
  not necessarily percentages that must sum to one.
- `Trip(vehicle_name, route, vehicle_type="passenger", depart=0, actor=None)`
  emits one named actor. Its post-init replaces the actor name/type with the
  trip's name/type; names must be unique for the intended scenario.
- `RandomRoute()` asks Studio to generate a route. `Route` uses
  `(road_id, lane_index, offset)` at each endpoint. Offset may be a number,
  `"random"`, or `"max"`; `via=(road_id, ...)` forces intermediate roads.
- `Mission(route, via=..., entry_tactic=...)` is a finite route mission.
  `EndlessMission(begin=(road, lane, offset), ...)` starts without a finite end.
  `LapMission` and `GroupedLapMission` cover repeated loops where needed.
- `SocialAgentActor(name, agent_locator, policy_kwargs={}, initial_speed=None)`
  references a registered agent locator in the form `python.module:locator`.
  This is a runtime import boundary; do not put a checkout path in the locator.
- `Bubble(zone, actor, margin=2, ...)` captures vehicles for a social actor.
  A traveling bubble must choose exactly one of `follow_actor_id` and
  `follow_vehicle_id` and must provide `follow_offset`. `keep_alive` is only
  valid for boid-style actors in this release.
- `PositionalZone(pos=(x, y), size=(length, width), rotation=None)` and
  `ConfigurableZone(ext_coordinates=[...], rotation=None)` are map-independent
  geometry descriptors. `MapZone(start=(road, lane, offset), length, n_lanes=2)`
  resolves geometry using the built road map.
- `RoadSurfacePatch(zone, begin_time, end_time, friction_coefficient)` is used
  in `friction_maps`; check bounds and units before simulation.
- `TrafficHistoryDataset` describes imported trajectories. Supported source type
  names in the type contract are `NGSIM`, `INTERACTION`, `Waymo`, and
  `Argoverse`; the input data and importer are external to this core helper.
- `ScenarioMetadata` accepts `actor_of_interest_re_filter`,
  `actor_of_interest_color`, `scenario_difficulty`, and `scenario_duration`,
  plus custom metadata. Metadata does not change simulation dynamics.

## Runtime discovery API

Do not confuse the authoring `sstudio` `Scenario` with
`smarts.core.scenario.Scenario(scenario_root, traffic_specs=..., missions=...)`.
The runtime class discovers resources and supports:

- `Scenario.is_valid_scenario(root)`: attempts to build a map and returns a
  boolean. It is not a full semantic validation.
- `Scenario.discover_scenarios(root)` and `get_scenario_list(...)`: find valid
  scenario roots; an invalid/empty directory raises an actionable assertion.
- `Scenario.discover_map(root, ...)`, `build_map(root)`,
  `discover_traffic(root)`, `discover_agent_missions(...)`,
  `discover_friction_map(root)`, and `scenario_variations(...)`.
- Instance properties include `root_filepath`, `road_map`, `road_map_hash`,
  `traffic_specs`, `missions`, `social_agents`, `bubbles`, `traffic_history`,
  `metadata`, and `supports_sumo_traffic`.

`discover_traffic` combines SUMO route files and SMARTS route files when both
are present; a generated scenario may therefore yield concrete traffic
combinations rather than a single run.
