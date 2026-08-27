# Closed-loop simulation CLI reference

## Required runtime inputs

The runner needs four absolute nuPlan roots and two checkpoint artifacts:

| Input | Used for |
|---|---|
| `NUPLAN_DEVKIT_ROOT` | locates the installed `nuplan/planning/script/run_simulation.py` |
| `NUPLAN_DATA_ROOT` | data root consumed by the selected nuPlan scenario builder |
| `NUPLAN_MAPS_ROOT` | map database root consumed by the builder |
| `NUPLAN_EXP_ROOT` | experiment/output root used by nuPlan Hydra configs |
| `args.json` | model architecture, normalization, and runtime settings |
| `model.pth` | trained PyTorch weights loaded by `DiffusionPlanner.initialize()` |

The actual paths are machine-specific. Keep them out of the skill and replace
all placeholders before launch. A typical local layout is represented by
variables, not fixed directories:

```bash
export NUPLAN_DEVKIT_ROOT="/absolute/path/to/nuplan-devkit"
export NUPLAN_DATA_ROOT="/absolute/path/to/nuplan-data"
export NUPLAN_MAPS_ROOT="/absolute/path/to/nuplan-maps"
export NUPLAN_EXP_ROOT="/absolute/path/to/nuplan-exp"
export ARGS_FILE="/absolute/path/to/checkpoints/args.json"
export CKPT_FILE="/absolute/path/to/checkpoints/model.pth"
```

The repository's template uses `./checkpoints/args.json` and
`./checkpoints/model.pth` relative to the current working directory. Either
use that layout or pass equivalent absolute Hydra overrides.

## Command meaning

The source runner is intentionally represented here as a path-neutral command
shape. It invokes the nuPlan Hydra entrypoint, selects the DiffusionPlanner
config, chooses a scenario builder/filter, and runs distributed workers:

```bash
python "$NUPLAN_DEVKIT_ROOT/nuplan/planning/script/run_simulation.py" \
  +simulation="$CHALLENGE" \
  planner=diffusion_planner \
  planner.diffusion_planner.config.args_file="$ARGS_FILE" \
  planner.diffusion_planner.ckpt_path="$CKPT_FILE" \
  scenario_builder="$SCENARIO_BUILDER" \
  scenario_filter="$SPLIT" \
  experiment_uid="diffusion_planner/$SPLIT/$BRANCH_NAME/$RUN_ID" \
  verbose=true \
  worker=ray_distributed \
  worker.threads_per_node="$THREADS_PER_NODE" \
  distributed_mode='SINGLE_NODE' \
  number_of_gpus_allocated_per_simulation="$GPU_FRACTION" \
  enable_simulation_progress_bar=true \
  'hydra.searchpath=[pkg://diffusion_planner.config.scenario_filter,pkg://diffusion_planner.config,pkg://nuplan.planning.script.config.common,pkg://nuplan.planning.script.experiments]'
```

Set these variables deliberately:

```bash
SPLIT=val14                         # or test14-random, test14-hard, val14-collision
CHALLENGE=closed_loop_nonreactive_agents  # or closed_loop_reactive_agents
BRANCH_NAME=diffusion_planner_release
RUN_ID="model-$(date +%Y%m%d-%H%M%S)"
THREADS_PER_NODE=128               # reduce for the current host
GPU_FRACTION=0.15                   # reduce/increase for the current host
```

The original launcher also sets `CUDA_VISIBLE_DEVICES` and
`HYDRA_FULL_ERROR`. Set the visible devices for the host rather than copying a
fixed multi-GPU list. `HYDRA_FULL_ERROR=1` is useful while diagnosing config
failures.

### What each override does

- `+simulation=...` selects the nuPlan simulation challenge. Use the exact
  nonreactive or reactive name; do not confuse it with `scenario_filter`.
- `planner=diffusion_planner` selects the planner group. The group target is
  `DiffusionPlanner` and its nested config has the paths/sampling values.
- `planner.diffusion_planner.config.args_file=...` supplies the model-side
  JSON. It is read when the planner is constructed through Hydra.
- `planner.diffusion_planner.ckpt_path=...` supplies the PyTorch file. It is
  loaded at planner initialization.
- `scenario_builder=...` selects which nuPlan database/mapping layout is
  used. It must match the selected dataset and split.
- `scenario_filter=...` selects one of the package filter configs. It is a
  Hydra group name, not a filesystem path.
- `experiment_uid=...` makes output directories distinguishable and determines
  where NuPlan writes simulation artifacts under `NUPLAN_EXP_ROOT`.
- `worker=ray_distributed` enables Ray-backed distributed execution. The
  thread and GPU-fraction values are scheduling settings, not model settings.
- `distributed_mode='SINGLE_NODE'` keeps the run on one node. Remove or change
  it only when the local nuPlan/Ray deployment is configured for another mode.
- `hydra.searchpath=[...]` exposes both this package's planner/filter groups
  and nuPlan's common/experiment groups. Keep the `pkg://` entries; a missing
  scenario-filter entry commonly appears as `Could not load
  'scenario_filter=...'`.

## Split and builder pairing

The bundled filters contain different semantics; they are not interchangeable:

| Filter | Selection semantics | Important values | Runner's automatic builder |
|---|---|---|---|
| `val14` | explicit scenario types and a large explicit token list; validation log names via `${splitter.log_splits.val}` | 100 per type, 15 s timestamp threshold, invalid goals removed, no shuffle | `nuplan` |
| `test14-random` | the 14 listed scenario types; tokens/logs/maps are null, so nuPlan selects from the challenge data | 20 per type, 15 s timestamp threshold, invalid goals removed, no shuffle | `nuplan_challenge` |
| `test14-hard` | 14 listed types plus an explicit hard-case token list | no per-type cap, 15 s timestamp threshold, invalid goals removed, no shuffle | `nuplan_challenge` |
| `val14-collision` | exactly four explicit tokens; no type/log/map filter and no timestamp/per-type cap | invalid goals retained, no shuffle; targeted diagnostic filter | `nuplan_challenge` because the template branches on exact equality with `val14` |

For `val14-collision`, the automatic result is a consequence of the shell
condition, not a universal statement that challenge data is required. Inspect
the local DB and mapping, then pass `scenario_builder=nuplan` explicitly if
that is the valid pairing. Use the helper's strict pairing warning before
launching a diagnostic run.

The filter fields are standard nuPlan `ScenarioFilter` fields: `scenario_types`,
`scenario_tokens`, `log_names`, `map_names`, `num_scenarios_per_type`,
`limit_total_scenarios`, `timestamp_threshold_s`, ego speed/displacement
thresholds, `expand_scenarios`, `remove_invalid_goals`, and `shuffle`. A null
field disables that filter; a string token list is still a curated selection,
not a random split.

## Sampling overrides

Use Hydra overrides when a compatible checkpoint explicitly supports a
non-default history or horizon:

```bash
planner.diffusion_planner.past_trajectory_sampling.num_poses=20 \
planner.diffusion_planner.past_trajectory_sampling.time_horizon=2 \
planner.diffusion_planner.future_trajectory_sampling.num_poses=80 \
planner.diffusion_planner.future_trajectory_sampling.time_horizon=8 \
planner.diffusion_planner.enable_ema=true \
planner.diffusion_planner.device=cuda
```

The model's `future_len` in `args.json`, not a generic nuPlan default, is the
source of truth for output horizon compatibility. If you change sampling,
verify the DataProcessor history contract and the checkpoint before a full
run. `device=cpu` is useful for construction/import checks but is not a claim
that the full diffusion simulation is practical or validated on CPU.

## Safe launch order

```bash
python scripts/check_closed_loop_config.py --help
python scripts/check_closed_loop_config.py \
  --args-file "$ARGS_FILE" --checkpoint "$CKPT_FILE" \
  --split "$SPLIT" --challenge "$CHALLENGE" --builder auto \
  --device cuda --nuplan-devkit-root "$NUPLAN_DEVKIT_ROOT" \
  --data-root "$NUPLAN_DATA_ROOT" --maps-root "$NUPLAN_MAPS_ROOT" \
  --exp-root "$NUPLAN_EXP_ROOT"
# Only after the helper reports ready:
# bash the locally adapted runner, or use the command shape above.
```

No simulated scenario is run by the helper. A missing external root,
checkpoint, or dataset is a blocked prerequisite rather than a package import
failure.
