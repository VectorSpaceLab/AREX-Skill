---
name: cooperative-simulation
description: "Operate OpenCDA V2X platooning, cooperative merge, CARLA-SUMO
  co-simulation, SUMO map conversion, and optional ScenarioRunner/OpenSCENARIO
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Cooperative simulation

Use this sub-skill when the task concerns OpenCDA connected-vehicle cooperation,
platoon formation or stability, cooperative merging, SUMO traffic, or the
optional ScenarioRunner/OpenSCENARIO integration.

## Route

- For V2X state, communication range/lag/noise, platoon roles, FSM transitions,
  joining, gap control, or stability metrics, read
  [platooning-and-v2x.md](references/platooning-and-v2x.md).
- For the CARLA-SUMO ownership model and per-step synchronization order, read
  [co-simulation.md](references/co-simulation.md).
- For `.sumocfg`/`.net.xml`/`.rou.xml` preparation and OpenDRIVE conversion, read
  [sumo-conversion.md](references/sumo-conversion.md), then run the read-only
  [preflight checker](scripts/check_sumo_conversion_prereqs.py) before any
  external launch.
- For ScenarioRunner/OpenSCENARIO setup and the OpenCDA handoff, read
  [scenario-runner.md](references/scenario-runner.md).
- For a failure, start with [troubleshooting.md](references/troubleshooting.md).

## Operating boundaries

The offline platoon debug helper is the native-safe candidate. A live platoon,
cooperative merge, CARLA-SUMO bridge, `netconvert`, TraCI server, CARLA server,
ScenarioRunner, and OpenSCENARIO run require external services/assets and are
not implied by package import success. The inspected environment passed core
OpenCDA imports, CARLA 0.9.12 client import, configuration/scientific package
imports, and `pip check`; it did not verify a CARLA server, SUMO/SUMO_HOME,
TraCI, ScenarioRunner, PyTorch, or YOLOv5.

Do not use this sub-skill to launch a simulator or convert a map implicitly.
The bundled checker only reads environment, executable, XML, and file metadata;
it never starts SUMO, TraCI, CARLA, ScenarioRunner, or `netconvert`.
