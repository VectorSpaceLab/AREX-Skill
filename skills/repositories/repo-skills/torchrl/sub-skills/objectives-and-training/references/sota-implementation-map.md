# SOTA implementation map

TorchRL keeps benchmark-style recipes under `sota-implementations/` and launch/check wrappers under `sota-check/`. This generated skill does not bundle or run those long training scripts. Use this map to find the relevant recipe family, then distill only the needed loss/config/trainer choices into a bounded task.

## How to use this map safely

- Treat all listed source scripts/configs as reference-only evidence. They often require long training, simulators, datasets, distributed services, or GPU resources.
- Do not copy a SOTA launcher into a quick helper script. Instead, extract the objective class, key mappings, target updater, replay/collector topology, and config fields.
- Before running any original SOTA command, verify dependencies, hardware, runtime budget, and artifact destinations with the user.
- For code edits to algorithms, also consult `sota-check/` to identify the smoke/release command that maintainers expect for that algorithm family.

## Algorithm-to-recipe index

| Algorithm or family | Reference recipe files | Objective/training surface to inspect | Runtime cautions |
| --- | --- | --- | --- |
| PPO | `sota-implementations/ppo/ppo_atari.py`, `ppo_mujoco.py`, `config_atari.yaml`, `config_mujoco.yaml`; `sota-implementations/ppo_trainer/train.py`; `sota-check/run_ppo_atari.sh`, `run_ppo_mujoco.sh` | `ClipPPOLoss`, GAE, on-policy collector, minibatch epochs, trainer variant | Atari/MuJoCo extras and long runs are not base-scope checks. |
| Async PPO | `sota-implementations/ppo-async/ppo_async_mujoco.py`, `train.py`, configs; no generic helper bundled | PPO loss plus asynchronous collection and weight sync | Optional distributed/process complexity; route collection details to `collectors-and-replay`. |
| A2C | `sota-implementations/a2c/a2c_atari.py`, `a2c_mujoco.py`; `sota-implementations/a2c_trainer/train.py`; `sota-check/run_a2c_atari.sh`, `run_a2c_mujoco.sh` | `A2CLoss`, advantage estimator, actor/critic updates | Simulator dependencies and long training. |
| REINFORCE | `sota-implementations/reinforce_trainer/train.py` | `ReinforceLoss`, trainer configs, on-policy batches | Trainer-specific example; inspect configs before reuse. |
| DQN | `sota-implementations/dqn/dqn_cartpole.py`, `dqn_atari.py`, configs; `sota-implementations/dqn_trainer/train.py`; `sota-check/run_dqn_cartpole.sh`, `run_dqn_atari.sh` | `DQNLoss`, `SoftUpdate`, exploration schedule, replay buffer, target network | Atari extras for full benchmark; CartPole is smaller but still not bundled as runtime helper. |
| Bandits | `sota-implementations/bandits/dqn.py` | DQN-like value loss in bandit setting | Treat as specialized recipe, not standard RL loop. |
| DDPG | `sota-implementations/ddpg/ddpg.py`, `config.yaml`; `sota-implementations/ddpg_trainer/train.py`; `sota-check/run_ddpg.sh` | `DDPGLoss`, deterministic actor, Q/value module, target updater | Continuous-control simulator dependency. |
| TD3 | `sota-implementations/td3/td3.py`, `config.yaml`; `sota-implementations/td3_trainer/train.py`; `sota-check/run_td3.sh` | `TD3Loss`, delayed policy/Q updates, noise smoothing, target updater | Continuous-control simulator dependency. |
| TD3+BC | `sota-implementations/td3_bc/td3_bc.py`, `config.yaml`; `sota-check/run_td3bc.sh` | `TD3BCLoss`, offline data action targets plus TD3 Q updates | Dataset/offline benchmark requirements. |
| SAC | `sota-implementations/sac/sac.py`, `sac-async.py`, `config.yaml`, `config-async.yaml`; `sota-implementations/sac_trainer/train.py`; `sota-check/run_sac.sh` | `SACLoss`, entropy temperature, target updates, replay | Async variant adds collector/service complexity. |
| Discrete SAC | `sota-implementations/discrete_sac/discrete_sac.py`, `config.yaml`; `sota-check/run_discrete_sac.sh` | `DiscreteSACLoss`, discrete action space and entropy settings | Check `action_space` and number of actions in configs. |
| REDQ | `sota-implementations/redq/redq.py`, `config.yaml`; `sota-check/run_redq` is not present in the observed check list, so verify current CI before relying on a launcher | `REDQLoss`, Q ensemble size, subsampling length, entropy temperature | Ensemble/vmap behavior and simulator dependency. |
| TQC | `sota-implementations/tqc/tqc.py`, `config.yaml`; `sota-check/run_tqc.sh` | `TQCLoss`, quantile network outputs, top quantiles to drop | Check output shapes carefully. |
| CrossQ | `sota-implementations/crossq/crossq.py`, `config.yaml`; `sota-check/run_crossq.sh` | `CrossQLoss`, Q ensemble and target-free/off-policy pattern | Requires algorithm-specific batch normalization assumptions. |
| CQL | `sota-implementations/cql/cql_offline.py`, `cql_online.py`, `discrete_cql_offline.py`, `discrete_cql_online.py`, configs; `sota-check/run_cql_offline.sh`, `run_cql_online.sh`, `run_discrete_cql.sh` | `CQLLoss`, `DiscreteCQLLoss`, offline/online data mode, conservative penalties | Offline datasets and online env dependencies differ. |
| IQL | `sota-implementations/iql/iql_offline.py`, `iql_online.py`, `discrete_iql.py`, configs; `sota-implementations/iql_trainer/train.py`; `sota-check/run_iql_offline.sh`, `run_iql_online.sh`, `run_iql_discrete.sh` | `IQLLoss`, `DiscreteIQLLoss`, expectile, temperature, value/Q/actor separation | Offline vs online wiring changes data assumptions. |
| Offline-to-online | `sota-implementations/offline_to_online/train.py` | Transition from dataset losses to online replay/collector loops | Validate data-source ownership with `collectors-and-replay`. |
| Decision Transformer | `sota-implementations/decision_transformer/dt.py`, `online_dt.py`, configs; `sota-check/run_dt.sh`, `run_dt_online.sh` | `DTLoss`, `OnlineDTLoss`, sequence/action target keys | Dataset and sequence packing are central; do not treat as standard TD loss. |
| Diffusion BC | `sota-implementations/diffusion_bc/diffusion_bc.py`, `config.yaml` | `DiffusionBCLoss`, action diffusion model, behavior cloning data | Requires model-specific action/trajectory formatting. |
| Dreamer / DreamerV3 | `sota-implementations/dreamer/dreamer.py`, `dreamer_isaac.py`, configs; `sota-implementations/dreamer_v3/dreamer_v3.py`, configs; `sota-check/run_dreamer_v3.sh` | Dreamer model/actor/value losses, world-model keys, symlog/two-hot utilities | Simulator and long model-based training dependencies. |
| GAIL | `sota-implementations/gail/gail.py`, `config.yaml`; helpers | `GAILLoss`, discriminator expert/collector keys, PPO helper loss | Expert datasets and discriminator data layout must be explicit. |
| RND | `sota-implementations/rnd/rnd_mujoco.py`, `config_mujoco.yaml`; `sota-check/run_rnd_mujoco.sh` | `RNDLoss`, intrinsic reward integration, PPO/DDPG style outer loop | Reward integration crosses collector/env code. |
| PILCO | `sota-implementations/pilco/pilco.py`, `config.yaml`; `sota-check/run_pilco.sh` | `ExponentialQuadraticCost`, model-based control utilities | Specialized model-based workflow. |
| Multi-agent MAPPO/IPPO/QMIX/IQL/SAC/IDDPG | `sota-implementations/multiagent/mappo_ippo.py`, `qmix_vdn.py`, `iql.py`, `sac.py`, `maddpg_iddpg.py`, configs; `sota-check/run_multiagent_*.sh` | `MAPPOLoss`, `IPPOLoss`, `QMixerLoss`, multi-agent key/group conventions | VMAS/PettingZoo/OpenSpiel-style optional deps; agent dimension handling is load-bearing. |
| Multi-agent trainer | `sota-implementations/multiagent_trainer/train.py` | Trainer config composition for multi-agent algorithms | Treat as trainer/config evidence, not a runnable generic script. |
| IMPALA | `sota-implementations/impala/*.py`, configs; `sota-check/run_impala_single_node.sh` | Distributed collector/learner pattern; objective may include V-trace-like estimation | Distributed services and Ray/Submitit require explicit provisioning. |
| GRPO / expert iteration / RLHF | `sota-implementations/grpo/*`, `expert-iteration/*` | LLM RL losses, async/sync rollout services | Route to `llm-vla-and-services`; model downloads, GPU serving, and external evaluation are not covered here. |
| VLA GRPO | `sota-implementations/vla_grpo/*`; `sota-check/run_vla_grpo.sh` | VLA data/action schema plus GRPO-style training | Route VLA schema/serving details to `llm-vla-and-services`. |

## Source-script import decision

For this sub-skill, all SOTA scripts/configs are **reference-only**. No long training script was copied, adapted, or wrapped. The only bundled script is `scripts/inspect_loss_keys.py`, which is deterministic API inspection and performs no environment interaction, data loading, or training.

Excluded from bundling:

- benchmark launch shell scripts from `sota-check/`, because they are long-running and environment-specific;
- simulator-heavy scripts, because optional env dependencies are not part of the CPU base scope;
- distributed/async launchers, because process/Ray/Submitit lifecycle belongs to explicitly provisioned collector/service tasks;
- LLM/VLA GRPO launchers, because they require model-serving backends and are routed to `llm-vla-and-services`.

## When editing an algorithm implementation

1. Identify the loss class and config dataclass involved.
2. Check whether the SOTA directory has a trainer and non-trainer version; update both only when the API change affects both surfaces.
3. Add or update tests under the nearest existing `test/objectives/` file unless the change creates a genuinely new objective.
4. If a SOTA script is part of CI smoke, mirror the expected config field name and default in the relevant Hydra config.
5. If the change requires optional dependencies or newer torch APIs, coordinate CI labels and old-dependency expectations through the development/testing sub-skill.
