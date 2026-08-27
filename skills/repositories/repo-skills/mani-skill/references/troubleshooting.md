# ManiSkill Troubleshooting

Use this root reference for package-wide failures before routing into a sub-skill-specific troubleshooting file.

## Install and import

Symptoms:

- `ModuleNotFoundError: mani_skill`
- Gymnasium cannot find an env id such as `PickCube-v1`
- demo or replay modules fail before showing help

Checks:

```bash
python scripts/check_install.py --json
python -c "import gymnasium as gym; import mani_skill.envs; print('registrations loaded')"
python -m mani_skill.examples.demo_random_action -h
```

Fixes:

- Install the package and a compatible `torch` build in the active environment.
- Import `mani_skill.envs` before calling `gym.make(...)` so public environments register with Gymnasium.
- Keep dev/docs/baseline extras separate from the runtime package unless the workflow truly needs them.

## CPU smoke versus GPU simulation

- `num_envs=1` with `sim_backend="auto"` uses PhysX CPU.
- `num_envs>1` with `sim_backend="auto"` uses PhysX CUDA.
- Use `render_backend="none"` and `render_mode=None` for headless checks.
- On multi-GPU machines, set `CUDA_VISIBLE_DEVICES` explicitly before GPU tests. For CPU-only smoke, first try the documented no-render CPU path; do not hide CUDA devices unless that configuration has already been verified on the host.

Use [sub-skills/environment-usage/scripts/smoke_no_render_cpu.py](../sub-skills/environment-usage/scripts/smoke_no_render_cpu.py) when the next safe action is a bounded reset/step.

## Rendering and Vulkan

Symptoms:

- GUI or `human` render mode fails
- `rgb_array`/`sensors` render paths crash or return unusable frames
- SAPIEN reports missing Vulkan/driver support

Checks:

- First prove the package with no-render CPU simulation.
- Then verify host Vulkan/driver tooling and the intended render backend.
- Avoid ray-tracing shaders until ordinary rendering works.

Do not present rendering as verified unless the current host has passed a rendering smoke. The production inspection verified CPU and no-render CUDA simulation, not Vulkan rendering.

## Assets and demonstrations

Some environments and datasets require assets that are not bundled with the package.

- Use `MS_SKIP_ASSET_DOWNLOAD_PROMPT=1` in non-interactive smoke runs so missing assets fail fast.
- Plan downloads before running them; downloads require network and may alter the user's cache directory.
- For asset/demo planning, use [sub-skills/trajectories-and-datasets/scripts/preview_download_options.py](../sub-skills/trajectories-and-datasets/scripts/preview_download_options.py).

## Trajectory conversion dependencies

The LeRobot converter imports `pandas` before help output and real conversion may also need parquet/LeRobot dependencies. If conversion fails before parsing flags, route to [sub-skills/trajectories-and-datasets/](../sub-skills/trajectories-and-datasets/) and run its planning helper before installing extras.

## Baseline training and benchmarks

Baseline training, dataset generation, and benchmark sweeps are expensive by default.

- Route training/evaluation questions to [sub-skills/learning-and-baselines/](../sub-skills/learning-and-baselines/).
- Do not assume WandB login, external clones, large datasets, or GPU availability.
- Preserve the evaluation contract: no partial resets, reconfigure on reset, record metrics, and aggregate complete episodes.

## Custom tasks

Custom task failures usually come from load-time collisions, unbatched reset/evaluation tensors, missing replay state, or unsupported robot/controller combinations. Route authoring/debugging questions to [sub-skills/custom-environments/](../sub-skills/custom-environments/) and start from its bundled scaffold helper.
