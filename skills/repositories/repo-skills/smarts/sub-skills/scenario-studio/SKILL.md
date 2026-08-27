---
name: scenario-studio
description: "Define, generate, inspect, and troubleshoot SMARTS scenarios from
  supported maps, traffic, missions, social agents, bubbles, surface patches,
  traffic histories, and metadata. Use this route when the task is scenario DSL
  or generated scenario layout; route live SUMO/TraCI, Envision replay, or
  environment lifecycle elsewhere."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Scenario Studio

Use this route when you need a self-contained SMARTS scenario definition or
need to explain why generated scenario artifacts are missing or incompatible.
The runtime DSL is `smarts.sstudio.types` (`smarts.sstudio.sstypes` is the
implementation module) and the high-level entry point is
`smarts.sstudio.genscenario.gen_scenario(scenario, output_dir, seed=42)`.

## Decide the boundary first

- Use `Scenario` from `smarts.sstudio.types` for the authoring DSL. It combines
  `map_spec`, named `traffic`, `ego_missions`, `social_agent_missions`,
  `bubbles`, `friction_maps`, `traffic_histories`, and `scenario_metadata`.
- Use the runtime `smarts.core.scenario.Scenario` only after generation, when
  SMARTS discovers a map and `build/` assets. It is not the authoring dataclass.
- Use `scripts/validate_scenario_layout.py` for a read-only layout check and
  `scripts/generate_minimal_scenario.py` for a bounded local fixture. Both take
  explicit paths and never start SUMO, TraCI, Envision, or a network download.
- Route `scl scenario build`, `scl scenario clean`, SUMO/TraCI, Waymo/Argoverse
  conversion, and other system integrations to `cli-integrations`.
- Route Gym/RLlib environment reset/step/close to `simulation-environments`.
  Route Envision replay and rendered sensors to `sensors-visualization`.

Read the linked references before authoring a nontrivial scenario:

- [API reference](references/api-reference.md) for live constructor signatures
  and the stable meaning of each DSL object.
- [Workflows](references/workflows.md) for minimal generation, custom maps,
  social agents, histories, deterministic rebuilds, and discovery.
- [Data formats](references/data-formats.md) for source-vs-build layout and
  artifact ownership.
- [Maps and traffic](references/maps-and-traffic.md) for map engines, routes,
  flows, missions, bubbles, friction, and dataset boundaries.
- [Troubleshooting](references/troubleshooting.md) for actionable recovery.

## Minimal authoring contract

1. Create an application-owned scenario directory and put a `scenario.py` in
   it. Keep input maps and data paths explicit; do not depend on the current
   working directory.
2. Select a map source: `map.net.xml`/another `.net.xml` for SUMO, `map.xodr`
   for OpenDRIVE, a Waymo `.tfrecord` source, an Argoverse map archive, or a
   `MapSpec(source=..., builder_fn=...)` for a custom `RoadMap` implementation.
3. Define named traffic, missions, and optional social/bubble/history metadata.
   Use edge/lane/offset tuples only when the referenced roads and lanes exist.
4. Call `gen_scenario(..., output_dir=scenario_dir, seed=<integer>)`. Set the
   same seed for comparable generated output; seed random choices before the
   call as well when authoring code uses Python or NumPy randomness.
5. Validate the source and then the generated `build/` tree. Build assets are
   generated state, not source code; regenerate after changing the DSL or map.
6. Before simulation, ensure the selected engine is compatible with the map and
   manually check that ego mission starts do not overlap traffic starts. Studio
   does not detect that collision-prone overlap for you.

## Fast recipe

```python
from pathlib import Path
from smarts.sstudio import gen_scenario, types as t

root = Path("my_scenario").resolve()
car = t.TrafficActor(name="car")
scenario = t.Scenario(
    map_spec=t.MapSpec(source=str(root / "map.net.xml")),
    traffic={"background": t.Traffic(
        engine="SUMO",
        flows=[t.Flow(
            route=t.Route(begin=("edge_in", 0, "random"),
                          end=("edge_out", 0, "max")),
            rate=60, begin=0, end=60, actors={car: 1.0},
        )]
    )},
    ego_missions=[t.Mission(t.Route(
        begin=("edge_in", 1, 10), end=("edge_out", 1, "max")
    ))],
)
gen_scenario(scenario, root, seed=42)
```

`SUMO` traffic requires a SUMO road network and the SUMO Python/runtime
integration; use `engine="SMARTS"` for supported non-SUMO road maps. The recipe
is a shape example: replace edge ids with ids from the selected map and install
optional dependencies before claiming a successful build.

## Generated-artifact explanation

A successful generation normally creates `build/build.db`, a map artifact under
`build/map/`, route files under `build/traffic/`, and optional files for
missions, social agents, bubbles, friction, histories, and metadata. The exact
set is determined by non-empty `Scenario` fields; see the data-format reference.
`smarts.core.scenario.Scenario.is_valid_scenario()` checks that a map can be
built, not that every optional artifact or traffic combination is semantically
safe. Missing `build/map/map.glb`, stale `build.db`, or absent route files means
regenerate/build rather than edit generated pickle/XML files manually.

## Checks and handoff

Run the validator from any cwd:

```bash
python /path/to/skills/disco/smarts/sub-skills/scenario-studio/scripts/validate_scenario_layout.py \
  --scenario /absolute/path/to/my_scenario --require-build
```

For a safe local fixture (OpenDRIVE is used only when the installed optional
parser can load the supplied map), write to an explicit empty output directory:

```bash
python /path/to/skills/disco/smarts/sub-skills/scenario-studio/scripts/generate_minimal_scenario.py \
  --map /absolute/path/to/map.net.xml --output /absolute/path/to/out --seed 42
```

The helper refuses to overwrite non-empty output unless `--force` is supplied,
uses no external service, and exits nonzero with the failing path or import
reason. Treat missing SUMO, Waymo, Argoverse, or dataset packages as explicit
integration gaps, not as evidence that core Scenario Studio is broken.
