# CLI and evaluation reference

## Static first

From any working directory, substitute the checkout for `REPO_ROOT`:

```bash
python REPO_ROOT/opencda.py --help
python REPO_ROOT/skills/disco/opencda/sub-skills/setup-and-scenarios/scripts/check_scenario_cli.py \
  --repo-root REPO_ROOT
python REPO_ROOT/skills/disco/opencda/sub-skills/setup-and-scenarios/scripts/check_scenario_cli.py \
  --repo-root REPO_ROOT --scenario single_2lanefree_carla
```

The checker reads filenames and Python syntax/AST only. It does not import
OpenCDA, import CARLA, load OmegaConf, connect to a port, start a process, or
launch a simulation. A selected scenario must have both:

- `opencda/scenario_testing/<name>.py`, containing a `run_scenario` function;
- `opencda/scenario_testing/config_yaml/<name>.yaml`.

An unknown name is an error. Orphaned module/config names are warnings because
custom development trees may intentionally be incomplete; fix them before a
benchmark run.

## Runner syntax

```bash
cd REPO_ROOT
python opencda.py -t SCENARIO -v 0.9.11
python opencda.py -t SCENARIO -v 0.9.12 --record
python opencda.py -t SCENARIO -v 0.9.11 --apply_ml
```

`-t/--test_scenario` is required. `-v/--version` defaults to `0.9.11` and the
supported values in this release are `0.9.11` and `0.9.12`. `--record` enables
CARLA recording; `--apply_ml` requests the ML/perception path and therefore
requires the optional ML stack.

The runner loads `default.yaml`, loads the scenario YAML with OmegaConf, and
merges the scenario into the default before importing the matching scenario
module and calling `run_scenario(opt, scene_dict)`. The source runner currently
imports the scenario module before its missing-config check and contains a
misspelled variable in that error branch (`test_cenario`); use the static
checker to catch missing pairs before invoking the runner.

## Scenario-manager flow

CARLA-only scenario modules normally construct `ScenarioManager`, create
platoons and/or single CAV managers, create CARLA Traffic Manager traffic, tick
synchronously, and call `EvaluationManager` at the end. The conceptual
sequence is:

1. load merged configuration;
2. connect to CARLA and load a town/custom map;
3. apply synchronous settings and weather;
4. spawn CAVs/platoons and background traffic;
5. tick, update managers, plan, and apply controls;
6. evaluate and save run statistics.

The evaluation API is exposed by
`opencda.scenario_testing.evaluations.evaluate_manager.EvaluationManager`.
Scenario modules generally instantiate it with the CAV world, script name, and
current time, then call `evaluate()` after the loop. Output locations and
scenario-specific data-dump behavior vary; treat output paths printed by the
run as authoritative and keep them outside the runtime skill tree.

## Version and server checks

The Python API and server must match the selected `-v`. OpenCDA's source
contains version-dependent blueprint names (`vehicle.lincoln.mkz2017` for
0.9.11 versus `vehicle.lincoln.mkz_2017` for 0.9.12) and CARLA API differences.
A successful `import carla` proves only the client package is importable; it does
not prove that a server is listening on the configured `world.client_port`
(default 2000) or that a requested town/map is installed.
