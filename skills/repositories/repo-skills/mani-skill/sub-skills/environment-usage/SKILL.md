---
name: environment-usage
description: "Run, inspect, wrap, record, and smoke-test ManiSkill environments
  from the public package with CPU/GPU, observation/control/render, and demo
  guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Environment Usage

Use this sub-skill when the task is about existing ManiSkill environments only: quickstart creation, observation/control/render selection, CPU vs GPU backend choice, wrapper composition, demo modules, and safe smoke tests from the public package.

Start here:

- [references/workflows.md](references/workflows.md) for safe run flows, wrapper order, and smoke patterns.
- [references/api-reference.md](references/api-reference.md) for `gym.make`, `BaseEnv`, backend, and wrapper contracts.
- [references/cli-and-modules.md](references/cli-and-modules.md) for runnable demo and visualization commands.
- [references/troubleshooting.md](references/troubleshooting.md) when import, render, backend, asset, or wrapper issues appear.
- [scripts/smoke_no_render_cpu.py](scripts/smoke_no_render_cpu.py) for a bounded CPU smoke run that works from any cwd.

What this sub-skill covers:

- `gym.make` / `mani_skill.envs` usage for public tasks
- `BaseEnv` runtime options and backend selection
- `CPUGymWrapper`, `ManiSkillVectorEnv`, `RecordEpisode`
- `FlattenObservationWrapper`, `FlattenRGBDObservationWrapper`, `FlattenActionSpaceWrapper`
- `demo_random_action`, `demo_robot`, visual demo modules, `demo_reset_distribution`
- help-only guidance for benchmarking / GPU sim
- safe CPU smoke patterns and backend caveats

What it does not cover:

- custom task authoring internals
- trajectory conversion, replay, teleop, or dataset collection details
- learning baselines and training recipes
- asset download internals beyond user-facing caveats

Routing:

- Custom task building -> [../custom-environments/](../custom-environments/)
- Replay, teleop, datasets -> [../trajectories-and-datasets/](../trajectories-and-datasets/)
- Training baselines -> [../learning-and-baselines/](../learning-and-baselines/)

Operating rules:

1. Prefer `import mani_skill.envs` followed by `gym.make(...)` for ordinary use. Reach for `mani_skill.envs.sapien_env.BaseEnv` only when you need constructor details, `print_sim_details()`, or low-level runtime inspection.
2. Treat `obs_mode` as the observation contract and `control_mode` as the action contract. If the user is unsure which mode to choose, inspect `env.observation_space`, `env.action_space`, and the bundled API notes before changing code.
3. Use `num_envs=1` for CPU smoke and `num_envs>1` for GPU parallelization. Default `sim_backend="auto"` selects PhysX CPU for one env and PhysX CUDA for multiple envs; use explicit `physx_cpu`, `physx_cuda`, or `physx_cuda:n` when you need to pin the backend.
4. Keep rendering explicit. Use `render_backend="none"` or `None` for headless smoke checks, and only ask for `human`, `rgb_array`, `sensors`, or `all` after display/Vulkan support is known.
5. Apply ManiSkill-native wrappers before outer API adapters. `RecordEpisode` should be last among ManiSkill wrappers, `CPUGymWrapper` is for single-env CPU runs only, and `ManiSkillVectorEnv` is the outer adapter for batched GPU envs that need Gymnasium vector semantics.
6. Use the demo modules for feature-specific inspection before custom code when possible. Prefer help output first for benchmark scripts and expensive visualizations.
7. When a task mentions replay, teleoperation, dataset collection, or training, route it to the dedicated sibling sub-skill instead of extending environment usage.
