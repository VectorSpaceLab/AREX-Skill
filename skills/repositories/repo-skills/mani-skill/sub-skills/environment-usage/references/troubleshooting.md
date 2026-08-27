# Troubleshooting

This file lists the most common ManiSkill environment-usage failures and the
fastest safe checks.

## 1) Install or import failures

Symptoms:

- `ModuleNotFoundError: mani_skill`
- `gym.make(...)` says the environment is unknown
- `ImportError` when a demo module is started

Checks:

```bash
python -c "import mani_skill, gymnasium; print(mani_skill.__version__)"
python -m mani_skill.examples.demo_random_action -h
```

Fixes:

- make sure the package is installed in the active environment
- import `mani_skill.envs` before the first `gym.make(...)`
- if you are running a bundled helper script directly, confirm it can find the repo root or the editable install

## 2) Observation / control-mode confusion

Symptoms:

- the observation has the wrong shape or nesting
- the action space is a dict when a vector `Box` was expected
- the task appears to ignore the intended controller

Checks:

```python
print(env.observation_space)
print(env.action_space)
print(env.single_observation_space)
print(env.single_action_space)
print(env.unwrapped.obs_mode_struct)
print(env.unwrapped.control_mode)
```

Rules:

- `obs_mode` decides the observation contract.
- `control_mode` decides the action contract.
- `state` is flattened state, `state_dict` is hierarchical, `sensor_data` is raw, and `pointcloud` is fused camera output.
- use `FlattenActionSpaceWrapper` only if the controller exposes a flat dict action space and you need a `Box`.

## 3) CPU vs GPU backend selection

Symptoms:

- the env runs on the wrong device
- CPU simulation refuses multiple envs
- a GPU env is unexpectedly slow or unavailable

Checks:

```python
print(env.unwrapped.gpu_sim_enabled)
print(env.unwrapped.backend)
print(env.unwrapped.device)
```

Rules:

- `sim_backend="auto"` chooses CPU for `num_envs==1` and CUDA for `num_envs>1`.
- `physx_cpu` is single-env only.
- use `physx_cuda:n` or `sapien_cuda:n` to pin a device.
- for CPU vectorization, use `gym.vector.AsyncVectorEnv` instead of forcing one CPU backend into many envs.

## 4) Wrapper misuse and vector API quirks

Symptoms:

- wrapper assertions about `num_envs`
- NumPy/Torch or batched/unbatched confusion
- `ManiSkillVectorEnv` auto-reset surprises
- partial reset plus reconfiguration errors

Checks:

- make sure only one final API adapter is in use: `CPUGymWrapper` for single-env CPU or `ManiSkillVectorEnv` for batched GPU
- keep ManiSkill-native wrappers inside the adapter, not outside it
- if using `ManiSkillVectorEnv`, inspect whether `ignore_terminations` and `auto_reset` are appropriate for the rollout style

Relevant quirks:

- `CPUGymWrapper` only accepts single-env CPU runs.
- `ManiSkillVectorEnv` returns torch tensors and inserts `final_observation` / `final_info` after auto resets.
- if `record_metrics=True`, both wrappers add episode summaries.
- partial resets with automatic reconfiguration are restricted; if you see that error, check `reconfiguration_freq` and `num_envs`.

## 5) Render and Vulkan caveats

Symptoms:

- GUI does not open
- `vulkaninfo` or SAPIEN rendering fails
- `human` / `rgb_array` / `sensors` returns nothing useful

Checks:

- first try a no-render run with `render_mode=None` and `render_backend="none"`
- verify the host has the expected Vulkan/driver stack before asking for rendering
- use `python -m mani_skill.examples.demo_random_action -h` to confirm safe options before turning on render

Caveats:

- rendering requires a working display and driver stack
- point-cloud and other visualization demos are display-dependent
- on limited platforms, the runtime may fall back to CPU rendering or disable the renderer

## 6) Missing assets or no-render smoke tips

Symptoms:

- an environment pauses to ask for asset downloads
- a demo fails because a required asset is unavailable
- a smoke test should be headless but is still trying to render

Checks:

- run the no-render CPU helper first
- set `MS_SKIP_ASSET_DOWNLOAD_PROMPT=1` for non-interactive runs
- if the user wants the asset-backed task, use the public `download_asset` command for that task id

Preferred fallback:

- keep the smoke run on a built-in, known-good task such as `PickCube-v1`
- do not switch to a different task silently unless the user explicitly allows that

## 7) Benchmarking and visualization help-only guidance

Symptoms:

- the user wants to benchmark, but the backend is still unverified
- visualization commands are requested in a headless shell

Checks:

```bash
python -m mani_skill.examples.benchmarking.gpu_sim -h
python -m mani_skill.examples.demo_vis_pcd -h
```

Guidance:

- inspect help first
- keep `--save-video` off until rendering works
- use small env counts for exploratory runs
- treat `gpu_sim` as a benchmark script, not a smoke script
