# JAX Agent Catalog

Acme 0.4.1 exposes JAX agents under `acme.agents.jax.<algorithm>`. The JAX extra is pinned to `jax==0.4.3` and `jaxlib==0.4.3` and also brings the TensorFlow/Reverb/Launchpad stack used by Acme experiment runners.

## Selection Checklist

1. Decide whether training interacts with an environment (`ExperimentConfig`) or learns only from a fixed dataset (`OfflineExperimentConfig` or a manual learner/evaluator loop).
2. Check the action spec: continuous control favors SAC, TD3, D4PG, MPO, PPO, WPO, CRR, CQL, MBOP; discrete control favors DQN, IMPALA, R2D2, PPO, BC, BVE.
3. If demonstrations are present, distinguish imitation without environment rewards (BC, AIL/GAIL/DAC, SQIL, PWIL, ValueDice) from learning from demonstrations with environment rewards (SACfD, TD3fD).
4. If the environment is multiagent and produces dict observations/rewards/actions keyed by agent id, use decentralized multiagent support and homogeneous sub-agent choices.
5. If the workflow needs Launchpad distributed actors, prefer agents whose builders implement full `ActorLearnerBuilder` methods; offline builders need the offline distributed runner.

## Online Continuous Control

| Need | Prefer | Package path | Core constructor | Notes |
| --- | --- | --- | --- | --- |
| Robust baseline for bounded continuous actions | SAC | `acme.agents.jax.sac` | `SACConfig`, `SACBuilder`, `make_networks` | Actor-critic with stochastic policy, twin critics, entropy regularization, and `target_entropy_from_env_spec` for action-dimension based entropy targets. |
| Deterministic actor-critic with exploration noise | TD3 | `acme.agents.jax.td3` | `TD3Config`, `TD3Builder`, `make_networks` | Uses LayerNorm MLP defaults; `TD3Config.bc_alpha` adds BC regularization for offline-style variants. |
| Distributed deterministic actor-critic with distributional critic | D4PG | `acme.agents.jax.d4pg` | `D4PGConfig`, `D4PGBuilder`, `make_networks` | Tune `vmin`/`vmax` in `make_networks`; synchronous local execution is closer to distributional DDPG than truly distributed D4PG. |
| Policy optimization with KL constraints or mixed replay | MPO | `acme.agents.jax.mpo` | `MPOConfig`, `MPOBuilder`, `make_control_networks` | Supports categorical/Gaussian policies, distributional critics, efficient frame stacking, mixed replay via `replay_fraction in (0, 1)` with `samples_per_insert=None`. |
| Clipped surrogate policy optimization | PPO | `acme.agents.jax.ppo` | `PPOConfig`, `PPOBuilder`, `make_continuous_networks` or `make_networks` | Uses replay to batch unrolls; increasing `num_epochs` and `num_minibatches` makes updates more off-policy. |
| Wasserstein policy optimization | WPO | `acme.agents.jax.wpo` | `WPOConfig`, `WPOBuilder`, `make_control_networks` | MPO-derived implementation for WPO-style policy updates; check action-policy assumptions before choosing over MPO. |
| Simple black-box policy search | ARS | `acme.agents.jax.ars` | `ARSConfig`, `ARSBuilder`, `make_networks` | Useful for low-complexity continuous control where augmented random search is acceptable. |

## Online Discrete Control

| Need | Prefer | Package path | Core constructor | Notes |
| --- | --- | --- | --- | --- |
| Value-based discrete baseline | DQN | `acme.agents.jax.dqn` | `DQNConfig`, `DQNBuilder`, `DistributionalDQNBuilder` | Includes prioritized replay, N-step bootstrapping, Double Q-learning; losses include vanilla Q-learning, QR-DQN, C51, Munchausen, and regularized DQN variants. |
| Many asynchronous actors / V-trace style architecture | IMPALA | `acme.agents.jax.impala` | `IMPALAConfig`, `IMPALABuilder`, `make_atari_networks` | Primarily exposed for Atari-style recurrent/discrete workflows. |
| Recurrent replay DQN | R2D2 | `acme.agents.jax.r2d2` | `R2D2Config`, `R2D2Builder`, `make_atari_networks` | Configure `burn_in_length`, `trace_length`, `sequence_period`, replay size, and epsilon schedule for recurrent sequence replay. |
| Policy-gradient discrete baseline | PPO | `acme.agents.jax.ppo` | `PPOConfig`, `PPOBuilder`, `make_discrete_networks` | Useful when discrete actions need actor-critic policy optimization rather than value-based replay learning. |

## Offline RL

| Need | Prefer | Package path | Builder type | Notes |
| --- | --- | --- | --- | --- |
| Supervised policy cloning from observation/action data | BC | `acme.agents.jax.bc` | `BCBuilder` (`OfflineBuilder`) | Losses include `logp`, `mse`, `peerbc`, and `rcal`; examples often use a manual learner/evaluator loop. |
| Conservative continuous offline RL | CQL | `acme.agents.jax.cql` | `CQLBuilder` (`OfflineBuilder`) | SAC-like offline algorithm with conservative critic regularization, `fixed_cql_coefficient`, optional adaptive Lagrange threshold, and `num_bc_iters`. |
| Critic-regularized continuous offline policy learning | CRR | `acme.agents.jax.crr` | `CRRBuilder` (`OfflineBuilder`) | Continuous action policy network; policy-loss coefficients include constant, advantage indicator, and exponential advantage forms. |
| Value estimation and one-step policy improvement | BVE | `acme.agents.jax.bve` | `BVEBuilder` (`OfflineBuilder`) | Value-based offline method using a DQN-style network and SARSA-style loss. |
| Model-based offline planning | MBOP | `acme.agents.jax.mbop` | `MBOPBuilder` (`OfflineBuilder`) | Trains world model, policy prior, and n-step return ensembles; dataset should be normalized timestep-batched transition triples. |
| Offline TD3 variant | TD3 with `bc_alpha` | `acme.agents.jax.td3` | `TD3Builder` (`ActorLearnerBuilder`) or manual learner usage | `TD3Config.bc_alpha` adds BC regularization; ensure dataset shape and replay/adaptation match the chosen runner. |

## Imitation And Demonstrations

| Need | Prefer | Package path | How it composes |
| --- | --- | --- | --- |
| Direct supervised imitation | BC | `acme.agents.jax.bc` | Offline builder or manual `BCLearner` with a demonstration iterator. |
| Adversarial imitation such as GAIL/DAC | AIL | `acme.agents.jax.ail` | Wraps a direct RL `ActorLearnerBuilder`; exposes `AILBuilder`, `GAILBuilder`, `DACBuilder`, `AILConfig`, `GAILConfig`, `DACConfig`, discriminator helpers. |
| SQIL-style imitation rewards | SQIL | `acme.agents.jax.sqil` | Requires an off-policy direct RL builder. |
| PWIL imitation distance reward | PWIL | `acme.agents.jax.pwil` | Wraps direct RL networks/policies and uses `PWILConfig` plus `PWILDemonstrations`; pre-fills replay concurrently to avoid Reverb deadlocks. |
| ValueDice imitation | ValueDice | `acme.agents.jax.value_dice` | Supports offline demonstrations-only and mixed mode; offline training is achieved by setting `nu_reg_scale` and `alpha` to `0`. |
| Learning from demonstrations with environment rewards | SACfD / TD3fD | `acme.agents.jax.lfd` | `LfdBuilder` wrappers expose `SACfDBuilder`, `SACfDConfig`, `TD3fDBuilder`, `TD3fDConfig`; configure demonstration replay insertion via `LfdConfig`. |

## Model-Based And Exploration Wrappers

| Need | Prefer | Package path | Notes |
| --- | --- | --- | --- |
| Offline model-based planning | MBOP | `acme.agents.jax.mbop` | `MBOPConfig` includes an `MPPIConfig`, `learning_rate`, `num_networks`, and `num_sgd_steps_per_step`. |
| Intrinsic exploration reward | RND | `acme.agents.jax.rnd` | Requires a direct RL `ActorLearnerBuilder`; by default ignores extrinsic reward unless intrinsic/extrinsic weights are passed to `make_networks`. |

## Decentralized Multiagent

Use `acme.agents.jax.multiagent.decentralized` when each agent can run a supported homogeneous sub-algorithm and the environment uses multiagent dict structures.

Key imports:

- `DecentralizedMultiAgentBuilder`
- `DecentralizedMultiagentConfig`
- `DefaultSupportedAgent`
- `default_config_factory(agent_types, batch_size, config_overrides=None)`
- `network_factory(environment_spec, agent_types, network_factory_fn)`
- `policy_network_factory(...)`

The underlying environment should produce observation and reward dictionaries keyed by string agent ids, consume an action dictionary with the same style of keys, and use a shared scalar discount.

## Practical Choices

- For continuous-control online baselines, start with SAC unless the user explicitly wants distributional deterministic control (D4PG), TD3-style deterministic control, MPO/WPO policy optimization constraints, or PPO compatibility.
- For distributed continuous control, keep the existing `ExperimentConfig` shape and swap builder/config/network factory; avoid installing TF agents extras separately because `dm-acme[jax]` already includes the shared TensorFlow/Reverb/Launchpad stack needed by JAX runners.
- For offline CQL/BC, do not use an environment interaction training loop. Provide a demonstration dataset iterator to `OfflineExperimentConfig.demonstration_dataset_factory` or create a manual learner loop that calls `learner.step()` and uses an evaluation-only actor.
- For image/Atari discrete workflows, use the discrete examples as architecture evidence but validate the `EnvironmentSpec` and network factory against the actual observation/action shapes.
- For multiagent tasks, decide the per-agent algorithm first, then use `default_config_factory` overrides to tune homogeneous sub-agent configs.
