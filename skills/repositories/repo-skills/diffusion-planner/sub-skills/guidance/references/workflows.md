# Guidance workflows

This is the smallest safe route from a custom reward to a guided planner run.
It assumes a project-owned worktree/package overlay. The original checkout is
source evidence, not a file that a future Researcher should edit in place.

## A. Establish the runtime without private paths

Choose an interpreter that the Researcher owns and can inspect, then set these
values as shell configuration rather than copying the supplied script's
private command:

```bash
PYTHON=/path/to/your/environment/bin/python
NUPLAN_DEVKIT_ROOT=/path/to/your/nuplan-devkit
NUPLAN_DATA_ROOT=/path/to/your/nuplan-data
NUPLAN_MAPS_ROOT=/path/to/your/nuplan-maps
NUPLAN_EXP_ROOT=/path/to/your/nuplan-experiments
export NUPLAN_DEVKIT_ROOT NUPLAN_DATA_ROOT NUPLAN_MAPS_ROOT NUPLAN_EXP_ROOT
```

Check that the selected interpreter imports `torch`, `nuplan`, and the
project's `diffusion_planner` package. CUDA guided simulation requires a CUDA
capable PyTorch installation and a visible device; CPU is sufficient for the
bundled geometry/wrapper smoke. Do not use `sudo`, a hard-coded private
interpreter or a machine-specific absolute path; resolve permissions
and environment activation explicitly instead.

Run the local smoke before acquiring any dataset:

```bash
"$PYTHON" skills/disco/diffusion-planner/sub-skills/guidance/scripts/synthetic_guidance_smoke.py
"$PYTHON" skills/disco/diffusion-planner/sub-skills/guidance/scripts/synthetic_guidance_smoke.py --help
```

A CUDA-only check is opt-in and should be run only on a machine with a usable
GPU:

```bash
"$PYTHON" skills/disco/diffusion-planner/sub-skills/guidance/scripts/synthetic_guidance_smoke.py --device cuda
```

## B. Add a custom guidance function through the extension point

Use a project-owned module/overlay that exports a callable with the stable
contract below. Register that callable in the wrapper's ordered guidance
registry using the deployment mechanism for the active worktree; do not rely
on an import side effect or mutate the original checkout.

```python
import torch


def my_guidance_fn(x, t, cond, inputs, *args, **kwargs) -> torch.Tensor:
    # x: [B, P, T+1, 4], physical units, current state at index 0.
    # t: [B] in the normal sampler path; cond is usually None.
    # inputs: inverse-normalized observation dictionary.
    position = x[:, 0, 1:, :2]
    # Example only: a differentiable, deterministic energy.
    target = torch.zeros_like(position)
    per_batch = ((position - target) ** 2).mean(dim=(1, 2))
    return per_batch
```

Before registering it:

1. Keep the returned energy connected to `x` and finite for every expected
   diffusion time.
2. Make any vectorized time gate explicit; do not use Python `and` on a batch
   tensor.
3. Use `inputs["neighbor_current_mask"]` and other keys only after checking
   their shape and device.
4. Return a graph-connected zero for a legitimate empty mask.
5. Avoid in-place edits to state or observations. Clone a tensor before
   replacing headings, dimensions, or masked entries.
6. Run the synthetic helper, then a focused custom-function test with both a
   valid and an empty/masked case.

When composing multiple functions, the wrapper sums their energies. Establish
a common sign and scale; a large term can dominate the built-in collision
energy. Keep the registry ordering deterministic so a reproducible run can be
compared across revisions.

## C. Understand the guided YAML

The guided planner configuration is a Hydra target for
`diffusion_planner.planner.planner.DiffusionPlanner`. Its important semantics
are:

```yaml
diffusion_planner:
  config:
    args_file: <checkpoint args.json>
    guidance_fn:
      _target_: diffusion_planner.model.guidance.guidance_wrapper.GuidanceWrapper
      _convert_: "all"
  ckpt_path: <checkpoint model.pth>
  past_trajectory_sampling:
    num_poses: 20
    time_horizon: 2
  future_trajectory_sampling:
    num_poses: 80
    time_horizon: 8
  device: cuda
```

`args_file` supplies model dimensions and normalizer construction; it is not a
replacement for `ckpt_path`. `GuidanceWrapper` activates classifier guidance;
the ordinary planner YAML sets `guidance_fn: null`. The future trajectory is
80 poses over 8 seconds, while the past sampling is 20 poses over 2 seconds in
the supplied guided config. Change these only with a checkpoint/configuration
compatibility check.

The launch script's intended overrides are also part of the contract:

- planner selection: `planner=diffusion_planner_guidance`;
- checkpoint overrides:
  `planner.diffusion_planner.config.args_file=...` and
  `planner.diffusion_planner.ckpt_path=...`;
- challenge: a closed-loop nonreactive or reactive simulation;
- scenario split: commonly `val14-collision` for the collision demo;
- nuPlan Hydra search paths include the repository scenario/config package.

The script also sets `CUDA_VISIBLE_DEVICES`, Ray worker counts, and GPU
allocation. Treat those as machine-specific knobs, not requirements. Start
with one visible GPU and conservative worker settings, then scale only after a
short successful run.

## D. Run guided simulation safely

After the smoke and configuration checks pass, invoke the nuPlan simulation
entry point through the selected interpreter and the user-controlled
`NUPLAN_DEVKIT_ROOT`:

```bash
"$PYTHON" "$NUPLAN_DEVKIT_ROOT/nuplan/planning/script/run_simulation.py" \
  +simulation=closed_loop_nonreactive_agents \
  planner=diffusion_planner_guidance \
  planner.diffusion_planner.config.args_file="$ARGS_FILE" \
  planner.diffusion_planner.ckpt_path="$CKPT_FILE" \
  scenario_builder=nuplan \
  scenario_filter=val14-collision \
  experiment_uid="diffusion_planner_guidance/val14-collision/$RUN_ID" \
  verbose=true \
  hydra.searchpath="[pkg://diffusion_planner.config.scenario_filter, pkg://diffusion_planner.config, pkg://nuplan.planning.script.config.common, pkg://nuplan.planning.script.experiments]"
```

The exact worker/distribution arguments depend on the host. Keep the command
free of `sudo` and private absolute paths. Confirm that the checkpoint and
`args.json` are readable by the selected interpreter, that maps/data/experiment
roots are writable as needed, and that the scenario filter is installed before
starting Ray workers. A full closed-loop run is intentionally not part of the
local smoke: it needs external nuPlan data, maps, checkpoint files, and often
CUDA/Ray resources.

## E. Stop and diagnose by stage

- **Import/smoke stage:** use [troubleshooting](troubleshooting.md) and fix
  device, package, signature, shape, or autograd errors first.
- **Hydra construction stage:** compare target paths and `args_file`/checkpoint
  dimensions; do not debug collision gradients yet.
- **First sampler step:** inspect `t`, heading norms, normalizer statistics,
  valid pair count, energy, and gradient finiteness.
- **Trajectory behavior stage:** compare guidance disabled versus enabled on a
  tiny fixed scenario; then inspect sign/scale before increasing worker count.
- **Closed-loop stage:** hand ordinary scenario/filter/Ray problems to the
  [closed-loop-planning sibling](../../closed-loop-planning/SKILL.md), keeping the
  guidance-specific evidence (energy and gradient logs) attached.
