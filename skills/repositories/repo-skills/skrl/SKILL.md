---
name: skrl
description: "Route public skrl 2.1.0 reinforcement-learning workflows across
  PyTorch, JAX, NVIDIA Warp, Gymnasium environments, multi-agent IPPO/MAPPO,
  runners, checkpoints, and experiment operations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# skrl

Use this skill when a task names **skrl**, asks for modular reinforcement
learning with Gym/Gymnasium, or needs skrl agents, models, memories, trainers,
framework wrappers, IPPO/MAPPO, Runner configurations, checkpoints, or
TensorBoard/W&B experiment controls. This is a public package-use guide, not a
maintainer guide for editing a checkout.

## Start with the route

1. Identify whether the environment is single-agent or multi-agent and whether
   it is Gymnasium, Gym, PettingZoo, or an external simulator. Read
   [`environment-integration`](sub-skills/environment-integration/SKILL.md)
   before choosing a wrapper.
2. Choose exactly one compute family. Read
   [`framework-selection`](references/framework-selection.md), then use the
   matching route: [`torch-agent-training`](sub-skills/torch-agent-training/SKILL.md),
   [`jax-agent-training`](sub-skills/jax-agent-training/SKILL.md), or
   [`warp-agent-training`](sub-skills/warp-agent-training/SKILL.md).
3. For IPPO, MAPPO, per-agent model/memory dictionaries, simultaneous scopes,
   Runner YAML, or distributed launch, use
   [`multi-agent-and-runner`](sub-skills/multi-agent-and-runner/SKILL.md) after
   the environment route. Do not reuse a single-agent model dictionary for a
   multi-agent constructor.
4. Read the nearest sub-skill reference for model role keys, spaces, config
   defaults, and failure recovery. Keep a small component/wrapper smoke separate
   from training, checkpoint writes, or external simulator startup.

## Installation and first check

`skrl` requires Python 3.10 or newer and installs common dependencies
Gymnasium, packaging, TensorBoard, and tqdm. Install only the framework extra
needed by the task:

```bash
python -m pip install "skrl[torch]"
# JAX: install the desired CPU/CUDA jaxlib first, then:
python -m pip install "skrl[jax]"
python -m pip install "skrl[warp]"
```

Use `skrl[all]` only when the task genuinely needs all three framework
families. Optional simulator packages (Isaac Lab, ManiSkill, MuJoCo Playground,
Shimmy, and PettingZoo) are separate prerequisites; an skrl extra does not
install their simulators, assets, or middleware. Verify the selected extra
without assuming a CUDA device:

```bash
python -c "import skrl; print(skrl.__version__)"
python scripts/check_frameworks.py --help
python scripts/check_frameworks.py --framework torch
```

The bundled check reports missing optional dependencies and performs a CPU
configuration probe; it does not train, download data, write experiment files,
or prove accelerator execution. Read [`framework-selection`](references/framework-selection.md)
for the JAX installation ordering and device rules.

## Core composition contract

A normal single-agent flow is: create the original environment, call the
framework-specific `wrap_env`, inspect `observation_space`, optional
`state_space`, `action_space`, `num_envs`, and `device`, define models with the
required role keys, allocate `RandomMemory` when the algorithm needs it,
configure an agent, and pass it to a trainer. `PPO`, for example, normally
needs `policy` and `value` models; off-policy algorithms add target and critic
roles. The framework routes contain the exact table.

For multi-agent flows, first inspect `possible_agents`, `agents`, per-agent
spaces and global state. Then construct nested dictionaries keyed by every
possible agent and use IPPO or MAPPO as documented by the multi-agent route.

## Operational boundaries

- Set experiment `write_interval` and `checkpoint_interval` to `0` for a
  read-only construction probe. `auto` creates TensorBoard/checkpoint output
  during a real trainer run.
- Checkpoint loading requires the same model architecture, role keys and
  framework-specific module arrangement used at save time. Recreate the agent
  before calling `load` and validate the path.
- CPU imports do not validate CUDA, distributed NCCL/JAX multi-process, Warp
  kernels, or simulator integrations. External stacks require their own
  installation, assets, drivers, and often headless/GPU configuration.
- For install, import, device, wrapper, config, and checkpoint failures, start
  with [`troubleshooting`](references/troubleshooting.md).

## Version and refresh

This graph was distilled from the repository state in
[`repo-provenance.md`](references/repo-provenance.md). Read it before using a
checkout-specific detail; if its commit, package version, public entry points,
or evidence paths differ, use `refresh-repo-skill` rather than treating this
graph as current.
