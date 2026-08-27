# Scenario data and layout contract

A scenario has **source inputs** and **generated build assets**. Keep this
separation explicit in reviews, caches, and bug reports.

## Source-side layout

A practical source directory contains:

```text
scenario-root/
├── scenario.py                 # optional if using a prebuilt map-only root
├── map.net.xml                 # SUMO map, or another .net.xml
├── map.xodr                    # OpenDRIVE alternative
├── <dataset files>             # external; do not copy into a skill
├── requirements.txt            # optional social-agent requirements; review first
└── user-owned assets/configs
```

The default map builder scans a directory for conventional map names and known
extensions. An unknown map source returns no road map and makes the scenario
invalid. Map source URIs/URLs are accepted by the `MapSpec` type contract, but
this route does not perform network acquisition; use an already available,
validated local source unless the integration route explicitly handles it.

## Generated layout

`gen_scenario` writes under `<scenario-root>/build`:

```text
build/
├── build.db                         # artifact hashes/cache
├── map/
│   ├── map_spec.pkl                 # when Scenario.map_spec is set
│   └── map.glb                      # built road-map geometry
├── traffic/
│   ├── <name>.rou.xml               # Traffic engine SUMO
│   └── <name>.smarts.xml            # Traffic engine SMARTS
├── missions.pkl                     # when ego_missions is non-empty
├── social_agents/
│   └── <group>.pkl                  # one file per social group
├── bubbles.pkl                      # when bubbles are defined
├── friction_map.pkl                 # when friction_maps are defined
├── <dataset-name>.shf               # imported history, when input is supplied
└── scenario_metadata.yaml           # default metadata is also emitted
```

Some old/generated directories may contain compatibility artifacts such as
route files at different levels. Use the discovery APIs and the validator
rather than assuming every legacy file placement is equivalent.

## Ownership and regeneration

- `scenario.py`, maps, dataset inputs, and custom builders are source-owned.
- `build.db` and all generated XML, pickle, GLB, SHF, and YAML files are
  derived. They can be deleted and recreated from source, subject to external
  data/package availability.
- `gen_scenario` hashes DSL objects and map sources. Missing artifacts, missing
  cache rows, changed hashes, or a rebuilt map cause affected outputs to be
  regenerated.
- A source map change requires a fresh map build. A changed traffic/mission
  object requires the corresponding generated artifact to be refreshed. If in
  doubt, use the public `scl scenario build --clean` route after backing up any
  user-owned files that happen to live in the scenario directory.

## Discovery contract

The runtime discovery class uses `<root>/build/map/map_spec.pkl` when present;
otherwise it creates a default `MapSpec` from the root. It discovers missions
from `build/missions.pkl`, social-agent groups from `build/social_agents/*.pkl`,
bubbles from `build/bubbles.pkl`, friction from `build/friction_map.pkl`,
metadata from `build/scenario_metadata.yaml`, traffic from the two generated
route extensions, and histories from generated history files.

`discover_traffic(root)` returns a list of traffic-file lists:

- only `.rou.xml`: one list per SUMO route file;
- only `.smarts.xml`: one list per SMARTS route file;
- both: one list for each SUMO/SMARTS pairing;
- neither: an empty-traffic placeholder list used by scenario variation logic.

`is_valid_scenario(root)` invokes the map builder and returns a boolean. It does
not prove that `missions.pkl`, traffic routes, social locators, history files,
or map/engine combinations are valid.

## Artifact interpretation

- `map_spec.pkl` is a serialized `MapSpec`, potentially including a custom
  builder callable. Loading it executes trusted serialized Python; do not accept
  it from an untrusted source.
- `map.glb` is generated render/geometry data used by the simulator and is not
the authoritative map definition.
- `missions.pkl`, `bubbles.pkl`, friction, and social files are generated
  Python pickles. They should be regenerated from the DSL rather than edited.
- Route XML is engine input generated from `Flow` and `Trip` definitions. It
  may contain resolved routes and distributions not obvious from the source.
- `scenario_metadata.yaml` is descriptive and does not change simulation
  dynamics; metadata such as actor-interest filters can affect visualization.
- History files are imported/processed trajectories. Their existence does not
  prove that the original dataset coordinate alignment was correct.

When reporting a failure, include the source map format, selected traffic
engine, seed, whether the source DSL was rerun, and the missing/stale artifact
names. Do not report a generated asset as a replacement for its source.
