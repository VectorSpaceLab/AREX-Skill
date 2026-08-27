---
name: closed-loop-planning
description: "Configure and run DiffusionPlanner in nuPlan closed-loop
  simulations, including checkpoint loading, trajectory sampling, scenario
  filters, builder selection, Ray execution, and optional NuBoard inspection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# Closed-loop planning

Use this skill when a Researcher needs to run the repository's `DiffusionPlanner`
inside nuPlan, select a checkpoint and its `args.json`, adjust past/future
trajectory sampling, choose a scenario split/filter, select nonreactive or
reactive closed-loop simulation, or inspect a result with NuBoard. It is also
the routing point for questions about `planner=diffusion_planner`, Hydra
search paths, scenario-builder pairing, checkpoint loading, Ray workers, or
trajectory output.

This skill does **not** create training data, train a model, or teach how to
author new guidance functions. For those tasks, route to the corresponding
sibling capability in the parent graph. It only consumes an already-compatible
checkpoint artifact and the model configuration serialized with that artifact.

## Execution boundary

Keep two readiness levels separate:

- **Parser/import readiness:** the package, planner class, nuPlan simulation
  entrypoint, scenario-builder classes, Hydra composition surface, and the
  bundled preflight helper can be imported or checked without a dataset, maps,
  Ray cluster, or checkpoint.
- **Full native simulation:** requires an external nuPlan-devkit installation,
  nuPlan DBs and maps, a readable `args.json` plus trained `model.pth`, a
  compatible CUDA device when `device=cuda`, and enough worker/runtime
  resources. This checkout contains none of the real dataset, maps, or
  checkpoint; do not claim a simulation ran when only import checks passed.

Run the safe preflight before starting Ray or loading a large scenario set:

```bash
python scripts/check_closed_loop_config.py \
  --args-file /absolute/path/to/checkpoints/args.json \
  --checkpoint /absolute/path/to/checkpoints/model.pth \
  --split val14 \
  --challenge closed_loop_nonreactive_agents \
  --builder auto \
  --device cuda \
  --nuplan-devkit-root /absolute/path/to/nuplan-devkit \
  --data-root /absolute/path/to/nuplan-data \
  --maps-root /absolute/path/to/nuplan-maps \
  --exp-root /absolute/path/to/nuplan-exp
```

The helper checks paths, JSON/model configuration shape, split/challenge names,
and the builder decision. It does not substitute for a real nuPlan simulation.
Use `python scripts/check_closed_loop_config.py --help` for all options.

## Standard operating sequence

1. **Establish external roots.** Set `NUPLAN_DEVKIT_ROOT`,
   `NUPLAN_DATA_ROOT`, `NUPLAN_MAPS_ROOT`, and `NUPLAN_EXP_ROOT` to absolute
   paths valid on the current machine. The simulation runner uses the first
   to locate `run_simulation.py`; nuPlan's composed builder uses the others.
   Replace every placeholder value with a verified local path or setting before running.
2. **Check the artifact pair.** Keep `args.json` and `model.pth` from the same
   checkpoint release. `Config(args_file, guidance_fn)` reads JSON immediately,
   constructs state and observation normalizers, and exposes the remaining
   architecture fields to `Diffusion_Planner`. The model file is loaded during
   `initialize`, not in the constructor.
3. **Choose a split and builder together.** Use the table in
   [the CLI reference](references/cli-reference.md). The supplied runner maps
   exactly `val14` to `nuplan` and every other split string to
   `nuplan_challenge`. In particular, `val14-collision` is a token-only custom
   filter and is *not* the same thing as `val14`; with the runner's automatic
   branch it selects `nuplan_challenge`, so review or explicitly override the
   builder for the local database layout.
4. **Choose challenge mode.** `closed_loop_nonreactive_agents` replays/logically
   keeps nonreactive agent behavior; `closed_loop_reactive_agents` runs the
   reactive-agent variant. Both are passed as `+simulation=...` to Hydra.
5. **Align trajectory sampling.** The repository defaults are 20 past poses
   over 2 seconds and 80 future poses over 8 seconds. The planner turns the
   future values into a horizon and step interval (`time_horizon / num_poses`)
   and transforms model output into an `InterpolatedTrajectory`. Keep the
   future pose count/horizon consistent with the checkpoint's serialized
   `future_len` and the model's prediction horizon.
6. **Run with controlled resources.** Start from the command template in
   [cli-reference.md], change worker thread/GPU fractions to fit the host, and
   use an experiment UID that identifies planner, split, challenge, and model.
   Ray and `distributed_mode='SINGLE_NODE'` are operational choices, not
   requirements of the planner API; a sequential worker is useful for a tiny
   debugging run if the nuPlan configuration supports it.
7. **Inspect results only after output exists.** NuBoard is optional. It needs
   a simulation output containing `.nuboard` metadata and a matching nuPlan
   scenario builder. The bundled notebook is a convenience template, not an
   offline smoke test; its placeholders and relative devkit config path must
   be replaced for the local installation. See [workflows](references/workflows.md).

## Planner configuration quick map

The planner group is `diffusion_planner` or `diffusion_planner_guidance`:

- `_target_`: `diffusion_planner.planner.planner.DiffusionPlanner`.
- `config._target_`: `diffusion_planner.utils.config.Config`.
- `config.args_file`: readable model-side JSON, normally the release's
  `args.json`.
- `config.guidance_fn`: `null` for the standard planner; the guidance variant
  constructs the repository's `GuidanceWrapper`.
- `ckpt_path`: readable PyTorch checkpoint, normally `model.pth`.
- `past_trajectory_sampling` / `future_trajectory_sampling`: nuPlan
  `TrajectorySampling` objects with `num_poses` and `time_horizon` (or the
  nuPlan-supported interval form).
- `enable_ema`: constructor default is `true`; set it explicitly when the
  checkpoint is known to contain or not contain `ema_state_dict`.
- `device`: only `cpu` or `cuda` are accepted by `DiffusionPlanner`; the
  default YAML uses `cuda` and asserts CUDA availability.

Hydra must be able to find both the planner group and the scenario-filter
group. The runner supplies package search paths for
`diffusion_planner.config.scenario_filter`, `diffusion_planner.config`, and
the nuPlan common/experiment config packages. Preserve those package URLs;
do not replace them with a private source checkout path.

## Verification record

The inspection environment validated the public planner/config/model imports,
`DiffusionPlanner` and `Config` signatures, nuPlan 1.2.2 simulation import,
`NuPlanScenarioBuilder`, and `TrajectorySampling`. It did not run native
simulation because no real dataset, maps, or checkpoint is present. Keep this
limit explicit in every handoff. Detailed API, CLI, workflow, and recovery
notes are in the bundled references.

- [API and lifecycle](references/api-reference.md)
- [Simulation command and overrides](references/cli-reference.md)
- [NuBoard workflow](references/workflows.md)
- [Troubleshooting](references/troubleshooting.md)
- [Safe preflight helper](scripts/check_closed_loop_config.py)
