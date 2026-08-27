# Cooperative simulation troubleshooting

## `SUMO_HOME` is missing

`cosim_api.py` and `netconvert_carla.py` require `SUMO_HOME` before importing
SUMO tools. Install a compatible SUMO distribution, set `SUMO_HOME` to its
installation root in the process environment, and make its tools importable.
Then verify `sumo`, `netconvert`, and the Python `traci`/`sumolib` modules in
the same interpreter. The preflight checker reports these independently. Do
not “fix” the problem by pointing `SUMO_HOME` at a random route directory.

## Map basename or triplet mismatch

If a directory is `MapName`, OpenCDA expects `MapName/MapName.sumocfg`; the
configuration should in turn resolve the intended `.net.xml` and `.rou.xml`.
Run `check_sumo_conversion_prereqs.py MapName` and fix the first error. Check
case, extensions, symlinks, and relative XML paths. A config that points to a
network from another map may parse successfully yet produce coordinate,
landmark, or route mismatches; compare the OpenDRIVE source and SUMO network
before launching.

## TraCI/SUMO startup or connection failure

Check that the SUMO binary is installed and executable, the config parses, the
network has edges, and the route file has valid vehicle types/routes. If using
an external SUMO server, confirm host, port, `client_order`, and that the
server is waiting for a TraCI client. If OpenCDA starts SUMO itself, ensure the
port is not already occupied and the selected `sumo`/`sumo-gui` binary matches
the Python tools. A TraCI exception after startup may indicate a bad route,
vehicle type, actor id, or a second client ticking the same simulation.

## CARLA connection or synchronization failure

Confirm the CARLA server is running, reachable, and the Python client version
matches it (the supported examples document 0.9.11/0.9.12; inspection passed a
0.9.12 client import only). Use synchronous mode with one tick owner and match
CARLA and SUMO step lengths. Missing actors, stale actor maps, transform
jumps, or traffic-light disagreement usually indicate map/offset mismatch,
double ticks, an actor destroyed by another client, or incompatible bridge
vehicle mappings. Do not diagnose a live problem from import success alone.

## Platoon does not form or merge

Check V2X `enabled`, communication range, peer state updates, capacity,
blacklist, FSM status, and front/rear references. Inspect whether the CAV is
`DISABLE`, whether it ever reaches `SEARCHING`, and whether `cav_nearby` has
current peers. For a merge, check warm-up speed, `inter_gap`, `open_gap`, lane
availability, obstacles, and the destination route. A join response may
briefly reduce leader speed; allow the recovery counter to expire before
judging steady-state speed. Verify actual lane and gap traces rather than
trusting console messages or a single FSM transition.

## ScenarioRunner/OpenSCENARIO failure

Match CARLA and ScenarioRunner releases, set `SCENARIO_RUNNER_ROOT` and
`PYTHONPATH` in the same interpreter, and first run `python -c "import
scenario_runner"`. Check the scenario XML/custom module paths, town, hero role,
actor count, and runner port. If the hero never appears, inspect server logs
and the scenario's actor definitions. If actors appear but OpenCDA does not
control the hero, confirm the role and manager creation happened after the
wait loop. Keep ScenarioRunner and OpenCDA from both calling `world.tick()`.

## What was not verified

No CARLA server, SUMO server/binaries/SUMO_HOME, TraCI, ScenarioRunner,
OpenSCENARIO execution, torch, or YOLOv5 runtime was available in inspection.
Those failures remain external-gated; do not report them as native package
regressions without reproducing in the required backend environment.
