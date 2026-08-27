---
name: model-based-rl
description: "Guides AI-Optimizer model-based RL baselines, world-model
  workflows, planning algorithms, and safe MuZero command construction."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Model-Based RL

Use this sub-skill when a task mentions model-based reinforcement learning, world models, learned dynamics, planning, Dreamer, PlaNet, MuZero, Sampled MuZero, MBPO, ED2-MBPO, BMPO, ED2-Dreamer, CaDM, MBRL baselines, training/test command construction, or config changes for these algorithms.

Do not use this route for offline RL algorithms such as BCQ, BEAR, CQL, AWAC, REDQ, UWAC, ISPI, COMBO, MOPO, E2O, or PEX; route those to `offline-rl`. Do not use it for Easy-MARL or multi-agent workflows; route those to `multi-agent-rl`.

## Fast route

1. Read [model-based-overview.md](references/model-based-overview.md) to choose the algorithm family, understand the collection taxonomy, and confirm heavy prerequisites.
2. For MuZero or Sampled MuZero, read [muzero-workflow.md](references/muzero-workflow.md). Use the safe helper [build_muzero_command.py](scripts/build_muzero_command.py) to construct MuZero commands without importing Ray/Torch or starting training.
3. For Dreamer or ED2-Dreamer, read [dreamer-workflows.md](references/dreamer-workflows.md).
4. For MBPO, ED2-MBPO, or BMPO, read [mbpo-bmpo-workflows.md](references/mbpo-bmpo-workflows.md).
5. For PlaNet, read [planet-workflows.md](references/planet-workflows.md).
6. Before running any heavy workflow, read [troubleshooting.md](references/troubleshooting.md) for old TensorFlow, Ray, MuJoCo, dm_control, Gym, CUDA/GPU, logging, result-directory, and missing-entry-point caveats.

## Safety and verification stance

- This sub-skill preserves command recipes and config knowledge; it does not claim that long RL training, CUDA execution, MuJoCo, dm_control, Atari, D4RL, or dataset downloads were verified.
- Prefer command construction, parser/static checks, dependency probes, and tiny configuration inspections before launching experiments.
- Treat full training, simulator execution, background `nohup` loops, and GPU allocation as user-approved heavy actions.
- Runtime links in this sub-skill point only to bundled references and scripts. The references distill the relevant repository evidence so future agents do not need to rely on source READMEs for basic operation.
