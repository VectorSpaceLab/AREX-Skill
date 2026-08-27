# easy-MARL Workflows

## Purpose

Read this to choose an easy-MARL entry script, construct a command, understand how a run is wired, and interpret the expected output locations. The commands here are derived from the tutorial README and the inspected entry scripts, not from a completed training benchmark.

## Before running a training command

- Work from an easy-MARL checkout where the tutorial entry scripts and packages are importable.
- Confirm required runtime packages first: at least NumPy, PyTorch, Gym-compatible APIs, and `tensorboardX`; MAGYM and MPE scenarios may require additional Gym compatibility work.
- Decide whether full RL training is acceptable. Even tutorial episode counts can be slow and produce logs/models.
- Use the bundled command builder first when you only need to validate command routing:

```bash
python scripts/build_easy_marl_command.py --agent-name IDQN --env-name discrete_meeting
```

The helper prints a command; it does not import PyTorch, instantiate environments, download data, or run training.

## Compatibility table

| Agent | Family | Entry script | Allowed environments | Scenario required? | Training-readiness notes |
| --- | --- | --- | --- | --- | --- |
| `IDQN` | DQN | `main_dqn.py` | `discrete_meeting`, `discrete_magym` | For `discrete_magym` only | Hyperparameter dispatch exists for both listed environments. |
| `VDN` | DQN | `main_dqn.py` | `discrete_meeting`, `discrete_magym` | For `discrete_magym` only | Hyperparameter dispatch exists for both listed environments. |
| `QMIX` | DQN | `main_dqn.py` | `discrete_meeting`, `discrete_magym` | For `discrete_magym` only | Hyperparameter dispatch exists for both listed environments. |
| `CommNet` | DQN | `main_dqn.py` | `discrete_meeting`, `discrete_magym` | For `discrete_magym` only | Source branch/class exists, but hyperparameter modules and buffer-interface alignment are missing in the inspected code. Treat as extension work. |
| `IDDPG` | DDPG | `main_ddpg.py` | `continuous_meeting`, `continuous_mpe` | For `continuous_mpe` only | Hyperparameter dispatch exists for both listed environments. |
| `MADDPG` | DDPG | `main_ddpg.py` | `continuous_meeting`, `continuous_mpe` | For `continuous_mpe` only | Hyperparameter dispatch exists for both listed environments. |
| `IPPO` | PPO | `main_ppo.py` | `discrete_meeting`, `discrete_magym`, `continuous_meeting`, `continuous_mpe` | For `discrete_magym` and `continuous_mpe` | Hyperparameter dispatch exists for all four easy-MARL environments. |
| `MAPPO` | PPO | `main_ppo.py` | `discrete_meeting`, `discrete_magym`, `continuous_meeting`, `continuous_mpe` | For `discrete_magym` and `continuous_mpe` | Hyperparameter dispatch exists for all four easy-MARL environments. |

## Example command patterns

DQN-based discrete commands:

```bash
python main_dqn.py --agent-name IDQN --env-name discrete_meeting
python main_dqn.py --agent-name VDN --env-name discrete_magym --scenario-name Switch4-v0
python main_dqn.py --agent-name QMIX --env-name discrete_magym --scenario-name Switch4-v0
```

DDPG-based continuous commands:

```bash
python main_ddpg.py --agent-name IDDPG --env-name continuous_meeting
python main_ddpg.py --agent-name MADDPG --env-name continuous_mpe --scenario-name simple_spread
```

PPO-based commands across discrete and continuous environments:

```bash
python main_ppo.py --agent-name IPPO --env-name discrete_meeting
python main_ppo.py --agent-name MAPPO --env-name discrete_magym --scenario-name Combat-v0
python main_ppo.py --agent-name IPPO --env-name continuous_meeting
python main_ppo.py --agent-name MAPPO --env-name continuous_mpe --scenario-name simple_tag
```

## Entry-script wiring

All three entry scripts follow the same high-level pattern:

1. `hyper_param_setting.parse_arguments()` parses `--env-name`, `--scenario-name`, and `--agent-name`.
2. The dispatcher chooses a hyperparameter class based on `env_name + "_" + agent_name`.
3. Scenario-aware environments pass `scenario_name` into their hyperparameter class; meeting environments ignore it.
4. The entry script instantiates the selected environment.
5. The script derives runtime dimensions from the environment: `agent_count`, per-agent observation dimensions, optional `state_dim`, and per-agent action dimensions.
6. The script imports the selected agent class and loops over `exp_count` experiments.
7. Training writes scalar metrics through `SummaryWriter` and calls `save_model` at configured intervals.

DQN-specific flow:

- `main_dqn.py` supports `discrete_meeting` and `discrete_magym`.
- It builds a replay `Buffer`, uses epsilon-greedy action selection, samples batches every `train_interval`, and logs `loss`, `training_episode_reward`, and optional `test_episode_reward`.
- DQN model checkpoints use the model path prefix `./logs/{exp_name}/{exp_id}/{train_step}` inside the training working directory.

DDPG-specific flow:

- `main_ddpg.py` supports `continuous_meeting` and `continuous_mpe`.
- It stores continuous actions in the buffer, trains actor and critic losses, and logs `actor_loss`, `critic_loss`, `training_episode_reward`, and optional `test_episode_reward`.
- The source has an exploration-noise function, but the main training loop leaves its call commented as a TODO. Do not assume exploration noise is active.

PPO-specific flow:

- `main_ppo.py` supports all four easy-MARL environment families.
- It creates a new `Buffer` per episode, samples that episode's buffer after the episode ends, and logs `loss`, `training_episode_reward`, and optional `test_episode_reward`.
- It branches on `env_name.startswith("discrete_")` versus `env_name.startswith("continuous_")` to derive action dimensions.

## Scenario handling

- `discrete_meeting` and `continuous_meeting` do not need a scenario. The dispatcher constructs `exp_name` as `{env_name}_{agent_name}`.
- `discrete_magym` defaults internally to `Switch4-v0` if an empty or `None` scenario reaches the hyperparameter class, but operationally prefer passing an explicit scenario so commands are reproducible. The bundled helper requires it.
- `continuous_mpe` defaults internally to `simple_tag` if an empty or `None` scenario reaches the hyperparameter class, but operationally prefer passing an explicit scenario. The bundled helper requires it.
- `exp_name` for scenario-aware environments becomes `{env_name}_{scenario_name}_{agent_name}`.

Useful scenario examples:

- MAGYM-style: `Switch4-v0`, `Combat-v0`, plus registered Switch, Checkers, TrafficJunction, Lumberjacks, PongDuel, and PredatorPrey variants.
- MPE-style: `simple_tag`, `simple_spread`, `simple`, `simple_adversary`, `simple_crypto`, `simple_push`, `simple_reference`, `simple_speaker_listener`, `simple_world_comm`.

## Outputs and side effects

- Training creates a `logs/` directory relative to the training working directory.
- TensorBoard event files are written under `./logs/{exp_name}/{exp_id}`.
- Model saves call `torch.save` with names derived from `./logs/{exp_name}/{exp_id}/{train_step}-net.pkl`, `-actor.pkl`, and/or `-critic.pkl` depending on the algorithm.
- Meeting environments have unimplemented `render()` methods; avoid enabling rendering unless you are prepared to handle `NotImplementedError`.
- This skill does not certify benchmark quality, convergence, CUDA behavior, MuJoCo/DMControl/D4RL/Waymo dependencies, or external SMAC/MPE downloads.
