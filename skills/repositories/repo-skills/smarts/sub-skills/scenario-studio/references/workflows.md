# Scenario Studio workflows

## 1. Generate a minimal scenario

Keep `scenario.py` executable as an ordinary Python script. Resolve
`output_dir` from `Path(__file__).parent` or an explicit caller path, not from a
working-directory assumption. A minimal local definition is:

```python
from pathlib import Path
from smarts.sstudio import gen_scenario, types as t

root = Path(__file__).resolve().parent
actor = t.TrafficActor(name="car")
gen_scenario(
    t.Scenario(
        traffic={
            "background": t.Traffic(
                engine="SUMO",
                flows=[t.Flow(
                    route=t.RandomRoute(), rate=30, begin=0, end=60,
                    actors={actor: 1.0},
                )],
            )
        }
    ),
    output_dir=root,
    seed=42,
)
```

`RandomRoute()` still needs a map capable of route generation. For a fixed map,
add `map_spec=t.MapSpec(source=str(root / "map.net.xml"))` and use real edge
ids for deterministic `Route` objects. `gen_scenario` creates/updates
`build/build.db` and caches by object/map hashes. The same seed is the baseline
for repeatable route generation; it does not fix nondeterministic agent actions
or external services.

## 2. Map-first authoring

Choose the map and engine together:

1. SUMO map: place a `.net.xml` map (the conventional name is `map.net.xml`)
   in the scenario source tree. `MapSpec` defaults to the SUMO builder when the
   extension is recognized. Use `Traffic(engine="SUMO")` only here and ensure
   the SUMO Python/runtime integration is installed when building or running.
2. OpenDRIVE: use `map.xodr` or `MapSpec(source=...)`; the optional OpenDRIVE
   parser and geometry dependencies must be installed. Use `engine="SMARTS"`
   for traffic on a non-SUMO map.
3. Waymo: use the supported TFRecord/Scenario-proto source with the Waymo
   dependencies and an appropriate `MapSpec`; dataset acquisition and parsing
   are optional integrations.
4. Argoverse: use the map archive recognized by the default builder and install
   its optional package. It is not covered by the core CPU environment.
5. Custom: implement a callable `builder_fn(map_spec)` that returns
   `(RoadMap-or-None, map_hash-or-None)`. Keep the implementation importable
   from the user's runtime Python path and treat it as executable code.

`lanepoint_spacing` controls generated lane-point density. Set
`default_lane_width` when the map lacks lane widths. `shift_to_origin` is
supported by general map builders but is not supported by the OpenDRIVE road
network in this release; it also risks misalignment with traffic histories.

## 3. Traffic flows and trips

Use a `Flow` for repeated emissions and `Trip` for one named vehicle:

```python
car = t.TrafficActor(
    name="car",
    speed=t.Distribution(mean=0.8, sigma=0.1),
)
traffic = t.Traffic(
    engine="SUMO",
    flows=[t.Flow(
        route=t.Route(
            begin=("entry", 0, "random"),
            end=("exit", 0, "max"),
            via=("middle",),
        ),
        rate=60,             # vehicles/hour
        begin=0,
        end=600,
        actors={car: 1.0},
        randomly_spaced=True,
        repeat_route=False,
    )],
    trips=[t.Trip(
        vehicle_name="lead",
        route=t.Route(begin=("entry", 1, 10), end=("exit", 1, "max")),
        depart=5,
        actor=t.TrafficActor(name="lead"),
    )],
)
```

A flow's `end` is simulation seconds, while `rate` is vehicles per hour. Keep
`end` at least as long as the expected training episode when the same scenario
is reset repeatedly; otherwise a flow may stop replenishing vehicles. Use
`repeat_route` only when repeated completed trips are intended. Traffic actor
weights select behavior types; they do not override route/map validity.

## 4. Ego and social missions

Use a `Mission(Route(...))` for a finite route, or `EndlessMission(begin=...)`
when the agent should continue without a destination. `via` points require a
lane/offset and required speed. For delayed or conditional entry, use an entry
tactic such as `TrapEntryTactic(start_time=...)` or `IdEntryTactic(...)` and
ensure a trap zone's starting edge agrees with the mission start edge.

Social groups are keyed by a group name:

```python
social = t.SocialAgentActor(
    name="keep-lane",
    agent_locator="my_agent_package.prefabs:keep-lane-v0",
)
scenario = t.Scenario(
    social_agent_missions={
        "group": ([social], [t.Mission(route=t.RandomRoute())])
    }
)
```

Actor names must be unique across social mission groups. A group with multiple
actors/missions cycles according to the documented sequence rules; keep actor
and mission counts aligned unless intentionally using that cycling behavior.
The locator must resolve in the execution environment; `scenario.py` can
compile while the social agent still fails at runtime.

## 5. Bubbles and friction

A bubble has a zone and an actor. Use `PositionalZone` for a fixed rectangle,
`MapZone` for lane-relative capture, or `ConfigurableZone` for explicit polygon
coordinates. Set `margin >= 0`. Traveling bubbles require one follow id and a
2-D `follow_offset`; validate that the follow actor/vehicle exists in the
scenario. Conditions can be composed from `LiteralCondition`, time windows,
subject conditions, and compound operators, but broadphase activation cannot
require current actor state.

Friction patches are independent `RoadSurfacePatch` objects in
`Scenario(friction_maps=[...])`. They generate one `build/friction_map.pkl`.
Use nonnegative time windows and a physically meaningful coefficient. The
runtime converts patches to dictionaries and applies them to vehicles; it does
not validate whether the polygon intersects a drivable lane.

## 6. Traffic histories and metadata

Add `TrafficHistoryDataset(name=..., source_type=..., input_path=...)` to
`traffic_histories`. Generation preprocesses supplied datasets into a history
artifact under `build/`; a missing `input_path` is deliberately treated as a
placeholder and skipped. Use one of the supported dataset source names and
match the map coordinate system. `filter_off_map`, `flip_y`, and axis/margin
settings can alter alignment; `shift_to_origin` with histories is warned
against because it can break map/data alignment.

Waymo and Argoverse examples require external data and optional packages; NGSIM
and INTERACTION also require their trajectory inputs. Do not substitute a path
placeholder and report the scenario as generated-history-ready.

## 7. Build, clean, and discover

After the DSL has generated source-side artifacts, use the public CLI route
from the SMARTS installation when a full scenario build is needed:

```bash
scl scenario build --seed 42 /absolute/path/to/scenario
scl scenario build --clean --seed 42 /absolute/path/to/scenario
scl scenario build-all --seed 42 /absolute/path/to/scenarios
scl scenario clean /absolute/path/to/scenario
```

These commands can execute scenario code and optional `requirements.txt`
installation. Never use an unreviewed scenario requirements file in a trusted
runtime. The bundled helper intentionally does not invoke these commands.

At runtime, pass scenario roots to the environment route. Discovery builds or
loads the map and enumerates `build/traffic/*.rou.xml` and
`build/traffic/*.smarts.xml`; if both engine families exist it produces their
cartesian combinations. `Scenario.is_valid_scenario` means only that the map
builder returned a road map.
