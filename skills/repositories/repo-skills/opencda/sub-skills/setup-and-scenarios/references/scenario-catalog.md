# Scenario catalog and dependency matrix

All names below are taken from the paired Python module and YAML file under
`opencda/scenario_testing/` and `opencda/scenario_testing/config_yaml/`.
`CARLA` means a CARLA-only path; `SUMO` and `SR` (ScenarioRunner) are external
backends. `ML?` is a runtime choice or known requirement, not a claim that the
model stack is installed.

| Scenario | Backend | Map/setting | ML? | Other prerequisites and intent |
|---|---|---|---|---|
| `single_2lanefree_carla` | CARLA | custom two-lane-freeway helper | no by default | Minimal single-CAV baseline; server/custom map assets required |
| `platoon_stability_2lanefree_carla` | CARLA | custom two-lane-freeway helper | no by default | Four-member platoon speed/stability test |
| `platoon_joining_2lanefree_carla` | CARLA | custom two-lane-freeway helper | no by default | Merge/join platoon with CARLA traffic |
| `platoon_joining_town06_carla` | CARLA | Town06 | usually yes | Back-join/overtake benchmark; perception path uses PyTorch/YOLOv5 |
| `single_intersection_town06_carla` | CARLA | Town06 | inspect YAML/module | Single-CAV intersection test; Town06 map assets |
| `single_town06_carla` | CARLA | Town06 | yes in documented example | Perception/localization/planning/control path; PyTorch/YOLOv5 |
| `v2xp_datadump_town06_carla` | CARLA | Town06 | inspect YAML/module | Offline V2X/cooperative-perception data dumping; storage/output required |
| `v2xp_online_carla` | CARLA | Town06 | inspect YAML/module | Online V2X path with RSU/data dumping; storage/output required |
| `openscenario_carla` | CARLA + SR | configured `scenario_runner.town` (Town06 in supplied YAML) | inspect | ScenarioRunner/OpenSCENARIO installation and assets; not Docker-supported per docs |
| `single_2lanefree_cosim` | CARLA + SUMO | custom two-lane-freeway co-sim files | inspect | SUMO, `traci`, network/route files, co-sim manager |
| `platoon_joining_2lanefree_cosim` | CARLA + SUMO | custom two-lane-freeway co-sim files | inspect | SUMO, `traci`, network/route files, co-sim manager |
| `single_town05_cosim` | CARLA + SUMO | Town05 + SUMO files | inspect | SUMO, `traci`, Town05 and matching SUMO network/route files |
| `single_town06_cosim` | CARLA + SUMO | Town06 + SUMO files | yes in documented example | SUMO, `traci`, PyTorch/YOLOv5 in ML mode, matching SUMO files |

## Choosing a safe first scenario

For dependency diagnosis, choose `single_2lanefree_carla` and omit
`--apply_ml`; it exercises the runner and external CARLA boundary without
requiring the optional perception stack. This still cannot run without a
CARLA server and the custom map/helper assets expected by the scenario.

For a stock-map CARLA check, choose a Town06 entry only after installing the
Town06 package/additional maps appropriate to the selected CARLA release. The
README cautions that OpenCDA is primarily tested on customized maps and Town06;
other maps are not guaranteed to have the same robustness.

Do not infer dependencies solely from a scenario name. Inspect its YAML and
module, and run the static checker first. `--apply_ml` is an explicit opt-in;
without it, the default perception configuration retrieves object positions
from the simulation server rather than loading YOLOv5. A scenario can still
make additional assumptions in its module, so external-gate the first run.

## CARLA-only versus co-simulation

CARLA-only scenarios use `opencda.scenario_testing.utils.sim_api.ScenarioManager`
and CARLA Traffic Manager. Co-simulation modules use the co-simulation manager
and a SUMO file parent path. Do not add SUMO keys to a CARLA-only run as a
substitute for missing CARLA server/map prerequisites, and do not treat a
CARLA-only configuration as sufficient for a `*_cosim` module.
