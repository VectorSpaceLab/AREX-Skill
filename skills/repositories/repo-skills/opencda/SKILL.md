---
name: opencda
description: "Use OpenCDA for cooperative-driving automation research in CARLA,
  optional CARLA-SUMO co-simulation, single-CAV and platooning scenarios,
  configurable sensing/planning/control, V2X, customization, and offline
  evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# OpenCDA

OpenCDA 0.1.3 is a Python cooperative-driving automation framework whose
runtime centers on a synchronous CARLA world and modular CAV managers. Use this
skill to plan or diagnose a scenario, configure modules, extend an algorithm,
operate V2X/platooning or CARLA-SUMO, and post-process dumped YAML data.

## Choose a route

- **Install, choose a benchmark, or author/validate YAML:** read
  [setup-and-scenarios](sub-skills/setup-and-scenarios/SKILL.md).
- **Single-CAV sensing, map, planning, control, safety, or API lifecycle:** read
  [core-driving-stack](sub-skills/core-driving-stack/SKILL.md).
- **V2X, platooning, cooperative merge/stability, SUMO, or ScenarioRunner:**
  read [cooperative-simulation](sub-skills/cooperative-simulation/SKILL.md).
- **Replace a module, preserve an extension contract, or analyze KF/EKF/debug
  output:** read [customization-and-analysis](sub-skills/customization-and-analysis/SKILL.md).
- **Augment dumped trajectories, interpret evaluation output, or make headless
  plots:** read [data-evaluation](sub-skills/data-evaluation/SKILL.md).

For cross-cutting install/import/config/backend failures, read
[references/troubleshooting.md](references/troubleshooting.md). Check whether
this knowledge matches the intended checkout using
[references/repo-provenance.md](references/repo-provenance.md).

## Minimal setup and safety gate

The documented baseline is Python 3.7+ with the package requirements, a CARLA
Python API matching the server (the source documents 0.9.11 and 0.9.12), and a
synchronous CARLA server for actual scenarios. Install the package in an
isolated environment, then verify at least:

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pip check
python -c "import opencda; from opencda.version import __version__; print(__version__)"
python opencda.py --help
```

Do not treat a package import or CLI help check as a live simulation check.
Before using a benchmark, separately verify the matching CARLA client/server,
requested Town05/Town06 or custom map, port, GPU/display requirements, and
synchronous settings. Keep `--apply_ml` off unless the PyTorch/YOLOv5 stack and
model assets are provisioned. Co-simulation additionally needs SUMO, `traci`,
`SUMO_HOME`, and a consistent `.sumocfg`/`.net.xml`/`.rou.xml` map triplet.

## Operating invariants

1. Merge the default YAML with the scenario override; do not silently replace
   the whole configuration. Keep `world.sync_mode` true and make
   `fixed_delta_seconds` agree with Traffic Manager or SUMO.
2. In a CARLA-only loop, tick the scenario manager, update each CAV, run its
   controller, apply the returned `carla.VehicleControl`, and destroy actors and
   sensors on exit.
3. Preserve module contracts: localization produces a CARLA transform and
   speed, perception returns categorized object dictionaries, behavior returns
   target speed/location, and control returns a CARLA vehicle command.
4. Treat CARLA server, GPU/rendering, SUMO, ScenarioRunner, and ML model
   execution as explicit external gates. The construction verification proved
   offline package/core imports and safe algorithms, not those services.
5. Do not copy source-checkout paths, private environments, large maps, model
   weights, or generated review artifacts into a runtime task. Use the bundled
   references and safe helpers instead.
