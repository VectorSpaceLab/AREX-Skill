---
name: multi-agent-rl
description: "Use AI-Optimizer easy-MARL tutorial code for multi-agent RL
  commands, environments, hyperparameters, and safe MARL extension."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Multi-Agent RL

Use this sub-skill when the task mentions multi-agent reinforcement learning (MARL), easy-MARL, IDQN, VDN, QMIX, CommNet, IDDPG, MADDPG, IPPO, MAPPO, discrete or continuous meeting environments, MAGYM, MPE, scenario names, or easy-MARL hyperparameter dispatch.

Do not use this sub-skill for model-based RL, offline RL, unrelated single-agent training, or external SMAC/API-network code. The AI-Optimizer MARL overview discusses those research directions, but the checked tutorial code covered here is the easy-MARL tutorial workflow. Treat uninitialized or external MARL code as a limitation, not an available runtime surface.

## Fast route

1. Read [references/marl-overview.md](references/marl-overview.md) when the user asks what MARL capability exists in AI-Optimizer, how the algorithms differ, or how easy-MARL fits the broader taxonomy.
2. Read [references/easy-marl-workflows.md](references/easy-marl-workflows.md) to choose the correct entry script, algorithm family, environment family, scenario, and expected logs/models.
3. Read [references/configuration-and-extension.md](references/configuration-and-extension.md) before changing hyperparameters, adding an algorithm, adding an environment/config pair, or repairing a missing dispatch branch.
4. Read [references/troubleshooting.md](references/troubleshooting.md) when commands fail, scenario names are rejected, optional dependencies are missing, logs/models are unexpected, or a workflow would require expensive/full training.
5. Use [scripts/build_easy_marl_command.py](scripts/build_easy_marl_command.py) to build a shell-quoted easy-MARL command without importing ML libraries or starting training.

## Command selection summary

- DQN-style discrete workflows use `main_dqn.py` with `IDQN`, `VDN`, `QMIX`, or the source-level `CommNet` branch on `discrete_meeting` or `discrete_magym`.
- DDPG-style continuous workflows use `main_ddpg.py` with `IDDPG` or `MADDPG` on `continuous_meeting` or `continuous_mpe`.
- PPO-style workflows use `main_ppo.py` with `IPPO` or `MAPPO` on any easy-MARL environment family.
- `discrete_magym` requires an explicit scenario name such as `Switch4-v0` or `Combat-v0`; `continuous_mpe` requires an explicit scenario name such as `simple_tag` or `simple_spread`.
- The meeting environments do not use scenario names.

Example safe command construction:

```bash
python scripts/build_easy_marl_command.py --agent-name MAPPO --env-name continuous_mpe --scenario-name simple_tag
```

The helper prints the command to run from an easy-MARL working tree; it does not run training. Before executing a printed training command, verify dependencies and resource expectations. This sub-skill does not claim full RL training, CUDA, MAGYM, MPE, SMAC, or benchmark reproduction verification.
