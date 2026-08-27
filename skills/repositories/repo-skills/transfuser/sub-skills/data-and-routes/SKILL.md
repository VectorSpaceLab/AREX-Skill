---
name: data-and-routes
description: "Guides TransFuser CARLA training route and scenario preparation,
  dataset-layout validation, privileged autopilot collection, safe command
  construction, and route visualization without launching CARLA or downloading
  data."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# TransFuser Data And Routes

Use this sub-skill when a Researcher needs to understand, validate, or prepare
TransFuser training routes, scenario annotations, generated samples, or the
privileged data-generation agent. Start with the relevant bundled reference;
use the scripts for deterministic local checks and command construction.

## Route by need

1. **Existing files or schema:** read [dataset-layout.md](references/dataset-layout.md)
   for sample folders and [routes-and-scenarios.md](references/routes-and-scenarios.md)
   for XML/JSON validation and route semantics. Run:
   `python scripts/validate_route_files.py --help` and
   `python scripts/validate_dataset_layout.py --help`.
2. **Generating or visualizing files:** read
   [data-generation.md](references/data-generation.md), then build a plan with
   `python scripts/build_route_tool_command.py --help`. The builder only prints
   a command/environment plan; it never starts a server, imports CARLA, writes
   routes, or uses the network.
3. **A failed or incomplete run:** read
   [troubleshooting.md](references/troubleshooting.md), validate inputs before
   retrying, and preserve the distinction between a safe local check and a
   CARLA-backed result.

## Required operating sequence

- Confirm the town set (`Town01`–`Town07`, `Town10HD`), scenario set
  (`Scenario1`, `3`, `4`, `7`, `8`, `9`, `10`), output roots, and whether the
  operation is route generation, scenario generation, visualization, or
  collection.
- Validate paths and schemas first. Route XML and scenario JSON can be parsed
  on CPU without CARLA; route/scenario compatibility is a structural signal,
  not proof that a CARLA map can interpolate the route.
- Generate **scenarios before routes**. Start the matching CARLA 0.9.10.1
  server and then run the scenario launcher, followed by the route launcher.
  Never run the bundled command builder as if it were a launcher.
- Keep `PYTHONPATH` ordered for the CARLA PythonAPI/egg, ScenarioRunner, and
  leaderboard. Use absolute paths at execution time, but do not place a local
  checkout path into a reusable skill file.
- For collection, use the privileged `DataAgent`/`AutoPilot` only after the
  route/scenario pair is validated, the server is reachable, and the output
  directory has enough space. A generated command or valid fixture is never a
  claim that data generation passed.
- Stop before network downloads, simulator launch, Docker, or the 210 GB data
  acquisition boundary unless the Researcher explicitly owns those external
  actions and verifies them separately.

## Invariants and handoffs

- `data-and-routes` owns route/scenario generation, route visualization,
  collection layout, and safe preflight. Link to `model-training` for how
  samples are consumed and to `carla-evaluation` for Longest6/evaluator runs.
- The generated dataset must contain synchronized frame indices across the
  required modalities and enough future `label_raw` frames for the configured
  sequence/prediction window.
- Scenario files describe trigger transforms and event configurations; route
  files describe map/town and waypoint paths. A matching filename alone does
  not prove that an event trigger lies on a route.
- The repository checkout is source evidence only. These bundled references and
  scripts must remain usable when the original checkout is absent.

## Verification status

The route/scenario schemas, selected repository fixtures, and self-contained
script fixtures are CPU-checkable. CARLA 0.9.10.1 and a running `CarlaUE4.sh`
server were absent during construction, so no scenario generation, route
interpolation, visualization against a map, or dataset collection is claimed
as passed. Treat this as an explicit external-runtime block.
