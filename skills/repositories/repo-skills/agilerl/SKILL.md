---
name: agilerl
description: "Use AgileRL for reinforcement learning workflows: classical RL
  training, evolutionary HPO, evolvable networks, multi-agent PettingZoo
  training, offline/bandit data, and LLM fine-tuning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AgileRL

Use this repo skill when a task involves AgileRL, `agilerl`, evolutionary hyperparameter optimization for RL, Gymnasium/PettingZoo training with AgileRL algorithms, AgileRL evolvable modules/networks, offline RL datasets, contextual bandits, or AgileRL LLM post-training.

## Quick Start

- Install: `pip install agilerl`.
- Optional LLM stack: `pip install "agilerl[llm]"` only when the task uses GRPO/CISPO/GSPO, DPO/SFT, vLLM, PEFT, DeepSpeed, or transformer datasets.
- Import check: `python -c "import agilerl, importlib.metadata as md; print(md.version('agilerl'))"`.
- Read `references/package-overview.md` for the algorithm family map, `references/troubleshooting.md` for cross-cutting dependency/backend issues, and `references/repo-provenance.md` when checking whether this skill is stale.
- Run `scripts/check_agilerl_install.py --help` for a safe local capability probe; it does not train, download models, or require the source checkout.

## Route By Task

| User task | Read |
| --- | --- |
| Train PPO, DQN, RainbowDQN, DDPG, or TD3 on Gymnasium; wire `create_population`, `train_on_policy`, `train_off_policy`, replay/rollout buffers, or distributed classical training | `sub-skills/training-workflows/SKILL.md` |
| Configure tournament selection, mutations, mutable RL hyperparameters, architecture mutation probabilities, or population evolution | `sub-skills/hpo-and-mutation/SKILL.md` |
| Build custom `EvolvableModule`/`EvolvableNetwork` objects, `net_config`, MLP/CNN/LSTM/MultiInput/SimBa configs, actors, critics, or `DummyEvolvable` wrappers | `sub-skills/evolvable-modules/SKILL.md` |
| Use PettingZoo multi-agent training, `MADDPG`, `MATD3`, `IPPO`, `AsyncPettingZooVecEnv`, agent id grouping, or AgileRL wrappers | `sub-skills/multi-agent-and-wrappers/SKILL.md` |
| Use offline datasets, HDF5/Minari conversion, replay filling, `CQL`/`ILQL`, contextual bandits, `NeuralUCB`, `NeuralTS`, or `BanditEnv` | `sub-skills/offline-bandits-data/SKILL.md` |
| Plan LLM fine-tuning/post-training with `GRPO`, `CISPO`, `GSPO`, LLM PPO, REINFORCE, `SFT`, `DPO`, vLLM, DeepSpeed, PEFT, or AgileRL LLM envs | `sub-skills/llm-fine-tuning/SKILL.md` |
| Compare benchmark scripts or adapt performance runs safely | `references/benchmarking.md` |

## Common AgileRL Building Blocks

- Algorithms: `PPO`, `DQN`, `RainbowDQN`, `DDPG`, `TD3`, `CQN`, `ILQL`, `NeuralUCB`, `NeuralTS`, `MADDPG`, `MATD3`, `IPPO`, `GRPO`, `CISPO`, `GSPO`, LLM PPO, REINFORCE, `SFT`, and `DPO`.
- Population setup usually starts with `agilerl.utils.utils.create_population(...)` and a Gymnasium or PettingZoo observation/action space.
- Evolution usually combines `TournamentSelection(...)` and `Mutations(...)`; use `HyperparameterConfig` and `RLParameter` for mutable algorithm attributes.
- Network configuration usually uses `net_config` with `encoder_config`, `head_config`, and optional recurrent/CNN/MultiInput fields.
- Training helpers return trained populations and fitness metrics; full training can be long, so prefer import/config/smoke checks before launching runs.

## Safe Validation Pattern

1. Check installation and optional dependency availability with `scripts/check_agilerl_install.py`.
2. Validate spaces, algorithm names, `INIT_HP`, `net_config`, and HPO configs with the nearest sub-skill helper script.
3. Run tiny constructor/import checks before full training.
4. Treat demos, tutorials, benchmark launchers, and original repo tests as evidence only; do not depend on the AgileRL source checkout from this generated skill.
5. For long training, LLM, GPU, vLLM, DeepSpeed, Minari remote, UCI, or benchmark tasks, document required hardware/data/network first and ask before expensive execution.

## Troubleshooting First Reads

- Install/import, Python version, missing optional extras, Torch/Gymnasium/PettingZoo/JAX/W&B issues: `references/troubleshooting.md`.
- Training shape/config errors: `sub-skills/training-workflows/references/troubleshooting.md`.
- Mutation/HPO mistakes: `sub-skills/hpo-and-mutation/references/troubleshooting.md`.
- Network architecture/config mistakes: `sub-skills/evolvable-modules/references/troubleshooting.md`.
- Multi-agent env/wrapper mistakes: `sub-skills/multi-agent-and-wrappers/references/troubleshooting.md`.
- Offline/bandit data schema mistakes: `sub-skills/offline-bandits-data/references/troubleshooting.md`.
- LLM optional dependency and backend mistakes: `sub-skills/llm-fine-tuning/references/troubleshooting.md`.
