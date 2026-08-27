# Data Generation And Safe Command Planning

## External runtime contract

Generation is a CARLA-backed operation. The required external pieces are:

- CARLA **0.9.10.1**, matching `CarlaUE4.sh`, PythonAPI, and Python 3.7 egg;
- a running CARLA server reachable on the chosen host/port (the repository
  examples use `localhost:2000`);
- the compatible ScenarioRunner and leaderboard Python trees;
- a compatible TransFuser runtime containing the generator/evaluator modules;
- the privileged `AutoPilot`/`DataAgent` and enough CPU/GPU, time, and disk.

The CARLA runtime was absent during construction. The bundled command builder
therefore emits a plan only. It never launches `CarlaUE4.sh`, opens a socket,
imports `carla`, installs packages, downloads the 210 GB dataset, or invokes a
generator.

## Environment and path contract

At external execution time, use paths supplied by the operator, not paths
copied from a particular checkout:

```text
CARLA_ROOT             directory containing CarlaUE4.sh and PythonAPI/
SCENARIO_RUNNER_ROOT   directory containing the srunner package
LEADERBOARD_ROOT       directory containing the leaderboard package
WORK_DIR               compatible TransFuser project/runtime root
```

The effective import path must put these entries ahead of conflicting
installations:

```text
CARLA_ROOT/PythonAPI
CARLA_ROOT/PythonAPI/carla
CARLA_ROOT/PythonAPI/carla/dist/carla-0.9.10-py3.7-linux-x86_64.egg
SCENARIO_RUNNER_ROOT
LEADERBOARD_ROOT
(existing PYTHONPATH)
```

The exact egg filename can differ in a valid installation; check the actual
CARLA 0.9.10.1 PythonAPI instead of blindly adding a second version. A command
plan containing a path is not a readiness check. First verify the file exists,
imports resolve from the intended interpreter, and a human has independently
started the server.

## Correct generation order

For a chosen town subset, run these phases in order:

1. **Scenario annotations:**
   - Scenario1 and 3 generator (non-junction/curved-road triggers);
   - Scenario4 generator (junction traversals);
   - Scenario7/8/9 generator (signalized-junction turn classes);
   - Scenario10 generator (unsignalized-junction triggers).
2. **Routes:**
   - Scenario1 with `curved` road type;
   - Scenario3 with `curved` road type;
   - Scenario4 with `junction` road type;
   - combined Scenario7/8/9 route generator;
   - Scenario10 route generator;
   - lane-change routes (`lr`, `ll`, `rr`, `rl`) if required.
3. **Validation:** run the route/schema checker on each XML/JSON pair and
   record route counts, towns, warnings, and any no-event/empty file.
4. **Collection:** set one scenario JSON and matching route XML, run the
   privileged data agent with `DATAGEN=1`, and write to a fresh `SAVE_PATH`.
5. **Dataset validation:** check synchronized modalities and frame windows
   before adding the route to training.

Routes must not be generated before their scenario annotations exist. The
route generators load CARLA maps, interpolate sparse points, de-duplicate
endpoints, and scan for viable scenario triggers; the CPU script cannot replace
that map-dependent work.

## What the privileged agent records

`AutoPilot` is a privileged expert: it sees the full simulated world and route,
uses dense route waypoints, predicts hazards, and emits expert steer/throttle/
brake plus future ego waypoints in `measurements`. `DataAgent` extends it with
three RGB, three depth, and three semantic cameras, one LiDAR, and a rendered
bird's-eye representation. It stores the seven modality groups described in
[dataset-layout.md](dataset-layout.md), typically every 0.5 seconds.

The generated label is not a model prediction. It includes privileged actor
boxes, relative positions, extents, speed/brake metadata, ids, and transforms.
The data agent also randomizes weather after saved ticks using a bounded set of
weather families (`Clear`, `Cloudy`, `Wet`, `MidRain`, `WetCloudy`, `HardRain`,
`SoftRain`) and six daylight choices. Treat weather diversity as a collection
property, not a guarantee for every individual route.

## Building a plan safely

Use:

```bash
python scripts/build_route_tool_command.py \
  --mode scenarios \
  --runtime-root /path/to/compatible/runtime \
  --carla-root /path/to/CARLA_0.9.10.1 \
  --towns all \
  --format shell
```

Then use `--mode routes`, `--mode datagen`, or `--mode visualize` as needed.
The output includes the intended environment, server prerequisite, and
non-executing commands. Review every absolute path and output directory before
copying a command into an external terminal. The builder is deliberately
conservative: it does not test a running server and does not claim that a
command is runnable when paths are missing.

For collection, prefer one town/scenario route first, a fresh output root, and
`REPETITIONS=1`. The checkpoint path and `SAVE_PATH` must be distinct from
previous runs unless resume behavior is intentional. Use `DATAGEN=1` only for
the data-generation evaluator; local learned evaluation belongs to
`carla-evaluation` and uses different semantics.

## Visualization boundary

The source-equivalent visualization requires CARLA map image metadata/assets,
pygame, and the input file; it may need a display or an explicitly prepared
headless graphics environment. Build the command but do not treat its output
as a route validity proof. First use the CPU validator, then inspect generated
PNG/TGA output for town mismatch, trigger placement, route direction, and lane
change class.

## Cost and stop rules

Stop and report a block if the next action would:

- download or unpack CARLA, model weights, or the 210 GB dataset;
- launch or control a CARLA server without explicit external execution;
- run thousands of routes when a tiny fixture would answer the question;
- overwrite an existing collection or checkpoint without a deliberate plan;
- build Docker images, upload results, or use cloud credentials.

A complete data-generation claim requires simulator logs, route completion,
nonempty synchronized output, and validator results. A printed plan or schema
parse is only preparation evidence.
