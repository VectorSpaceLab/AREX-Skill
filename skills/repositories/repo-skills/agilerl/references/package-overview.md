# AgileRL Package Overview

AgileRL is a deep reinforcement learning package centered on evolvable algorithms and population-based hyperparameter optimization. It supports classical Gymnasium training, PettingZoo multi-agent training, offline RL, contextual bandits, custom evolvable networks, and optional LLM post-training.

## Install And Dependency Groups

| Need | Install guidance | Notes |
| --- | --- | --- |
| Core RL APIs | `pip install agilerl` | Includes Torch, Gymnasium, PettingZoo, JAX CPU, Minari, W&B, Hydra/OmegaConf, and related runtime dependencies from package metadata. |
| Box2D Gymnasium envs | `pip install "agilerl[box2d]"` | Requires `swig` on non-Windows platforms because Box2D builds native code. |
| LLM fine-tuning | `pip install "agilerl[llm]"` | Adds datasets, PEFT, Transformers, vLLM, DeepSpeed, bitsandbytes, and liger-kernel on supported Linux hosts. |
| Everything | `pip install "agilerl[all]"` | Heavy; avoid unless the task truly needs both Box2D and LLM workflows. |
| Development checkout | `pip install -e .` from a cloned repo | For maintaining AgileRL itself, not required to use this generated skill. |

AgileRL declares Python `>=3.10,<3.14`. For ML environments, Python 3.10 or 3.11 is usually safer than 3.13 because compiled package wheels can lag the newest Python release.

## Algorithm Families

| Family | Algorithms | Main route |
| --- | --- | --- |
| On-policy classical RL | `PPO` | `../sub-skills/training-workflows/SKILL.md` |
| Off-policy classical RL | `DQN`, `RainbowDQN`, `DDPG`, `TD3` | `../sub-skills/training-workflows/SKILL.md` |
| Offline RL | `CQN`, `ILQL` | `../sub-skills/offline-bandits-data/SKILL.md` |
| Contextual bandits | `NeuralUCB`, `NeuralTS` | `../sub-skills/offline-bandits-data/SKILL.md` |
| Multi-agent RL | `MADDPG`, `MATD3`, `IPPO` | `../sub-skills/multi-agent-and-wrappers/SKILL.md` |
| LLM post-training | `GRPO`, `CISPO`, `GSPO`, LLM PPO, LLM REINFORCE, `SFT`, `DPO` | `../sub-skills/llm-fine-tuning/SKILL.md` |

## Workflow Pattern

Most AgileRL classical workflows follow this shape:

1. Choose environment and spaces (`make_vect_envs`, a Gymnasium env, or PettingZoo vector env).
2. Define `INIT_HP` and `net_config`.
3. Create a population with `create_population(...)`.
4. Create shared memory when needed (`ReplayBuffer`, `RolloutBuffer`, or `MultiAgentReplayBuffer`).
5. Configure `TournamentSelection` and `Mutations`.
6. Call the matching training helper or write a custom loop.
7. Evaluate, checkpoint, or inspect the elite agent.

## Safety And Runtime Notes

- Full RL training, benchmarks, LLM fine-tuning, remote datasets, and vLLM/DeepSpeed runs can be expensive. Validate imports/configs first.
- Treat W&B logging as optional: set logging flags off or configure credentials before training.
- Box2D, pygame rendering, PettingZoo extras, Minari remote datasets, and UCI examples can require extra packages or network access.
- Use CPU-compatible dry runs unless the user explicitly asks for CUDA/GPU validation.
