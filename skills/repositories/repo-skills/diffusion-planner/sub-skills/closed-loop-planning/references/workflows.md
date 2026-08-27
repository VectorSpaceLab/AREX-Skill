# Closed-loop and NuBoard workflows

## Preflight workflow

Use the bundled helper before touching Ray:

```bash
python scripts/check_closed_loop_config.py --help
python scripts/check_closed_loop_config.py \
  --args-file "$ARGS_FILE" \
  --checkpoint "$CKPT_FILE" \
  --split "$SPLIT" \
  --challenge "$CHALLENGE" \
  --builder auto \
  --device cuda \
  --nuplan-devkit-root "$NUPLAN_DEVKIT_ROOT" \
  --data-root "$NUPLAN_DATA_ROOT" \
  --maps-root "$NUPLAN_MAPS_ROOT" \
  --exp-root "$NUPLAN_EXP_ROOT"
```

The helper is deliberately dependency-light: it uses the standard library for
path, JSON, split, and planner-argument checks. `--check-cuda` is optional and
only probes PyTorch availability/device state. It never downloads data,
constructs a Ray worker, deserializes a checkpoint by default, or runs a
scenario.

## Nonreactive/reactive run workflow

1. Install the repository package and a compatible nuPlan-devkit environment.
   The verified inspection environment had `nuplan-devkit==1.2.2`; treat
   another version as a compatibility decision, not an automatic upgrade.
2. Set the four `NUPLAN_*` roots and artifact paths. Confirm that the DB layout
   selected by the builder exists below the data root and that maps are
   available for the configured `map_version`.
3. Select `SPLIT` and its builder. Start with `val14` plus `nuplan` for a
   standard validation-style check, or the challenge builder for the two
   test14 filters. For `val14-collision`, make the builder decision explicit.
4. Select `CHALLENGE` as either `closed_loop_nonreactive_agents` or
   `closed_loop_reactive_agents`. Reactive runs require the corresponding
   nuPlan observation/agent configuration and normally cost more than a
   parser smoke.
5. Run the command shape in [cli-reference.md](cli-reference.md), changing
   thread count, GPU fraction, visible devices, and experiment UID to the
   current machine. Keep `HYDRA_FULL_ERROR=1` while debugging.
6. Check that the experiment directory contains simulation logs, metrics, and
   `.nuboard` metadata before attempting visualization. Record the exact
   args/checkpoint hashes and Hydra overrides with the result.

A successful planner import or model construction is not a successful
simulation. The scenario builder must be able to open real DBs/maps, and the
planner must complete `initialize()` and repeated
`compute_planner_trajectory()` calls.

## Optional NuBoard workflow

`run_nuboard.ipynb` is a convenience notebook with this sequence:

1. Set a concrete `RESULT_FOLDER` pointing to a completed experiment.
2. Set `NUPLAN_DEVKIT_ROOT`, `NUPLAN_DATA_ROOT`, `NUPLAN_MAPS_ROOT`, and
   `NUPLAN_EXP_ROOT` in the notebook process. It also sets
   `NUPLAN_SIMULATION_ALLOW_ANY_BUILDER=1` for its visualization setup.
3. Point Hydra at the installed nuPlan NuBoard config package, select
   `default_nuboard`, choose `scenario_builder=nuplan` (or the builder that
   produced the results), and provide the `.nuboard` simulation path.
4. Run the final cell importing `main` from
   `nuplan.planning.script.run_nuboard`.

Caveats:

- The notebook contains placeholders and a relative devkit config path. It is
  not portable until those values are changed for the current environment.
- It needs actual simulation output and the corresponding scenario data/maps;
  a notebook kernel launch alone proves nothing about result availability.
- `simulation_path` is a list of directories/files discovered by walking the
  result folder. If no `.nuboard` file exists, NuBoard cannot load the run;
  inspect the experiment output before debugging Hydra.
- NuBoard is optional and does not affect planner inference or simulation
  correctness. Prefer the CLI/run artifacts for reproducible execution.

## Tiny diagnostic workflow

For a first native run, choose the smallest permitted filter or a known
single-scenario filter in a local config, lower Ray resources, and keep one
worker. Use a real checkpoint and a real DB/map fixture. Do not repurpose
`val14-collision` as a generic mini split: it names four curated tokens and
may not exist in the selected DB.

If the first failure happens before scenario enumeration, diagnose package
imports, Hydra search path, JSON/checkpoint loading, and builder configuration.
If it happens after scenario enumeration, diagnose data/map/schema availability,
observation history, device memory, and worker scheduling.
