# JAX Agent API Reference

This reference lists evidence-backed import paths and constructor names for Acme 0.4.1 JAX agent workflows.

## Package And Extras

| Fact | Value |
| --- | --- |
| Distribution | `dm-acme` |
| Version inspected | `0.4.1` |
| Import package | `acme` |
| Core requirements | `absl-py`, `dm-env`, `dm-tree`, `numpy`, `pillow`, `typing-extensions` |
| JAX extra | `jax==0.4.3`, `jaxlib==0.4.3`, `chex`, `dm-haiku`, `flax`, `optax`, `rlax`, plus TensorFlow/Reverb/Launchpad stack |
| TF/Reverb/Launchpad stack in extras | `tensorflow==2.8.0`, `tensorflow_probability==0.15.0`, `tensorflow_datasets==4.6.0`, `dm-reverb==0.7.2`, `dm-launchpad==0.5.2` |
| Environment extra | `atari-py`, `bsuite`, `dm-control`, `gym==0.25.0`, `gym[atari]`, `pygame==2.1.0`, `rlds` |

Core-only installs are not enough for `acme.jax.experiments` runners because they import Reverb, TensorFlow savers, Launchpad distributed runners, and JAX utilities.

## Experiment APIs

Import from `acme.jax import experiments` or from `acme.jax.experiments`.

| API | Purpose |
| --- | --- |
| `experiments.ExperimentConfig` | Online actor/learner experiment config. |
| `experiments.OfflineExperimentConfig` | Offline learner/evaluator config using fixed demonstrations. |
| `experiments.CheckpointingConfig` | Checkpoint and replay-checkpoint options. |
| `experiments.run_experiment(experiment, eval_every=100, num_eval_episodes=1)` | Local single-process online runner. |
| `experiments.run_offline_experiment(experiment, eval_every=100, num_eval_episodes=1)` | Local single-process offline runner. |
| `experiments.make_distributed_experiment(experiment, num_actors, **kwargs)` | Launchpad distributed online program builder. |
| `experiments.make_distributed_offline_experiment(experiment, **kwargs)` | Launchpad distributed offline program builder. |
| `experiments.default_evaluator_factory(...)` | Builds an evaluator factory from environment, networks, policy, logger, and observers. |
| `experiments.make_policy(experiment, networks, environment_spec, evaluation)` | Internal helper that prefers deprecated config policy factories when set, otherwise calls `builder.make_policy`. |

### `ExperimentConfig` Fields

Required:

- `builder`: an `acme.agents.jax.builders.ActorLearnerBuilder`.
- `network_factory`: callable taking `EnvironmentSpec` and returning algorithm-specific networks.
- `environment_factory`: callable taking seed and returning an environment.
- `max_num_actor_steps`: total actor/environment steps.
- `seed`: JAX PRNG seed.

Optional:

- `policy_network_factory`: deprecated; behavior policy factory from networks.
- `evaluator_factories`: sequence of custom evaluator factories; `[]` disables evaluators.
- `eval_policy_network_factory`: deprecated; evaluation policy factory from networks.
- `environment_spec`: precomputed spec to avoid repeated environment construction.
- `observers`: environment-loop observers.
- `logger_factory`: logger factory; defaults to `experiment_utils.create_experiment_logger_factory`.
- `checkpointing`: `CheckpointingConfig`, or `None` to disable checkpointing and snapshotting.

### `OfflineExperimentConfig` Fields

Required:

- `builder`: an `acme.agents.jax.builders.OfflineBuilder`.
- `network_factory`: callable taking `EnvironmentSpec` and returning networks.
- `demonstration_dataset_factory`: callable taking a JAX PRNG key and returning an iterator over samples.
- `environment_factory`: evaluation environment factory; required for default evaluators.
- `max_num_learner_steps`: learner steps.
- `seed`: JAX PRNG seed.

Optional:

- `evaluator_factories`: sequence of custom evaluator factories; `[]` disables evaluators. If `None`, `environment_factory` must be available.
- `environment_spec`: precomputed environment spec.
- `observers`, `logger_factory`, `checkpointing`: same role as online config.

### Builder Interfaces

`acme.agents.jax.builders.OfflineBuilder` defines:

- `make_learner(random_key, networks, dataset, logger_fn, environment_spec, *, counter=None)`
- `make_actor(random_key, policy, environment_spec, variable_source=None)`
- `make_policy(networks, environment_spec, evaluation)`

`acme.agents.jax.builders.ActorLearnerBuilder` extends offline builder with:

- `make_replay_tables(environment_spec, policy)`
- `make_dataset_iterator(replay_client)`
- `make_adder(replay_client, environment_spec, policy)`
- `make_actor(random_key, policy, environment_spec, variable_source=None, adder=None)`
- `make_learner(random_key, networks, dataset, logger_fn, environment_spec, replay_client=None, counter=None)`

## Algorithm Classes And Factories

| Family | Package | Config | Builder | Networks / policy helpers |
| --- | --- | --- | --- | --- |
| SAC | `acme.agents.jax.sac` | `SACConfig` | `SACBuilder` | `SACNetworks`, `make_networks`, `apply_policy_and_sample`, `default_models_to_snapshot`, `target_entropy_from_env_spec` |
| TD3 | `acme.agents.jax.td3` | `TD3Config` | `TD3Builder` | `TD3Networks`, `make_networks`, `get_default_behavior_policy` |
| D4PG | `acme.agents.jax.d4pg` | `D4PGConfig` | `D4PGBuilder` | `D4PGNetworks`, `make_networks`, `get_default_behavior_policy`, `get_default_eval_policy` |
| DQN | `acme.agents.jax.dqn` | `DQNConfig` | `DQNBuilder`, `DistributionalDQNBuilder` | `DQNNetworks`, `DQNPolicy`, `EpsilonPolicy`, `default_behavior_policy`, losses `QLearning`, `QrDqn`, `PrioritizedDoubleQLearning`, `PrioritizedCategoricalDoubleQLearning` |
| IMPALA | `acme.agents.jax.impala` | `IMPALAConfig` | `IMPALABuilder` | `IMPALANetworks`, `make_atari_networks` |
| R2D2 | `acme.agents.jax.r2d2` | `R2D2Config` | `R2D2Builder` | `R2D2Networks`, `make_atari_networks`, `make_behavior_policy`, `EpsilonRecurrentPolicy` |
| PPO | `acme.agents.jax.ppo` | `PPOConfig` | `PPOBuilder` | `PPONetworks`, `make_networks`, `make_discrete_networks`, `make_continuous_networks`, `make_mvn_diag_ppo_networks`, `make_tanh_normal_ppo_networks`, `make_categorical_ppo_networks`, `make_inference_fn` |
| MPO | `acme.agents.jax.mpo` | `MPOConfig` | `MPOBuilder` | `MPONetworks`, `make_control_networks`, `make_actor_core`, `CriticType`, `GaussianPolicyLossConfig`, `CategoricalPolicyLossConfig` |
| WPO | `acme.agents.jax.wpo` | `WPOConfig` | `WPOBuilder` | `WPONetworks`, `make_control_networks`, `make_actor_core`, `GaussianPolicyLossConfig` |
| ARS | `acme.agents.jax.ars` | `ARSConfig` | `ARSBuilder` | `make_networks`, `make_policy_network` |
| BC | `acme.agents.jax.bc` | `BCConfig` | `BCBuilder` | `BCNetworks`, `BCPolicyNetwork`, `BCLearner`, losses `logp`, `mse`, `peerbc`, `rcal`, conversion helpers |
| CQL | `acme.agents.jax.cql` | `CQLConfig` | `CQLBuilder` | `CQLNetworks`, `CQLLearner`, `make_networks` |
| CRR | `acme.agents.jax.crr` | `CRRConfig` | `CRRBuilder` | `CRRNetworks`, `CRRLearner`, `make_networks`, policy loss coefficient helpers |
| BVE | `acme.agents.jax.bve` | `BVEConfig` | `BVEBuilder` | `BVENetworks`, `BVELoss` |
| MBOP | `acme.agents.jax.mbop` | `MBOPConfig`, `MPPIConfig` | `MBOPBuilder` | `MBOPNetworks`, `MBOPLearner`, `MBOPLosses`, `make_networks`, `make_ensemble_actor_core`, `make_actor`, dataset normalization helpers |
| AIL/GAIL/DAC | `acme.agents.jax.ail` | `AILConfig`, `GAILConfig`, `DACConfig` | `AILBuilder`, `GAILBuilder`, `DACBuilder` | `AILNetworks`, `DiscriminatorMLP`, `DiscriminatorModule`, `AIRLModule`, `make_discriminator`, `compute_ail_reward` |
| SQIL | `acme.agents.jax.sqil` | direct RL config plus SQIL builder args | `SQILBuilder` | Composes with direct RL networks/policies. |
| PWIL | `acme.agents.jax.pwil` | `PWILConfig`, `PWILDemonstrations` | `PWILBuilder` | Wraps direct RL networks/policies and demonstrations. |
| ValueDice | `acme.agents.jax.value_dice` | `ValueDiceConfig` | `ValueDiceBuilder` | `ValueDiceNetworks`, `ValueDiceLearner`, `make_networks`, `apply_policy_and_sample` |
| RND | `acme.agents.jax.rnd` | `RNDConfig` | `RNDBuilder` | `RNDNetworks`, `RNDLearner`, `make_networks`, `compute_rnd_reward`, `rnd_reward_fn` |
| LfD wrappers | `acme.agents.jax.lfd` | `LfdConfig`, `SACfDConfig`, `TD3fDConfig` | `LfdBuilder`, `SACfDBuilder`, `TD3fDBuilder` | `LfdStep` and wrapped SAC/TD3 networks. |
| Decentralized multiagent | `acme.agents.jax.multiagent.decentralized` | `DecentralizedMultiagentConfig` | `DecentralizedMultiAgentBuilder` | `DefaultSupportedAgent`, `default_config_factory`, `network_factory`, `policy_network_factory`, `builder_factory` |

## Important Config Fields

### Continuous Online

`SACConfig`:

- `batch_size=256`, `learning_rate=3e-4`, `reward_scale=1`, `discount=0.99`, `n_step=1`
- `entropy_coefficient=None`, `target_entropy=0.0`, `tau=0.005`
- replay controls: `min_replay_size=10000`, `max_replay_size=1000000`, `replay_table_name`, `prefetch_size=4`, `samples_per_insert=256`, `samples_per_insert_tolerance_rate=0.1`
- `num_sgd_steps_per_step=1`, `input_normalization=None`

`TD3Config`:

- `batch_size=256`, `policy_learning_rate=3e-4`, `critic_learning_rate=3e-4`
- `policy_gradient_clipping=None`, `discount=0.99`, `n_step=1`
- TD3 options: `sigma=0.1`, `delay=2`, `target_sigma=0.2`, `noise_clip=0.5`, `tau=0.005`
- replay controls: `min_replay_size=1000`, `max_replay_size=1000000`, `samples_per_insert=256`, `prefetch_size=4`
- `bc_alpha=None` for optional BC regularization

`D4PGConfig`:

- `sigma=0.3`, `target_update_period=100`, `samples_per_insert=32.0`
- `n_step=5`, `discount=0.99`, `batch_size=256`, `learning_rate=1e-4`, `clipping=True`
- replay controls: `min_replay_size=1000`, `max_replay_size=1000000`, `prefetch_size=4`, `num_sgd_steps_per_step=1`

`MPOConfig` / `WPOConfig` highlights:

- `batch_size=256`, `discount=0.99`, `replay_fraction=1.0`, `samples_per_insert=32.0`, replay sizes
- `num_samples=20`, policy loss config fields, `learning_rate=1e-4`, `dual_learning_rate=1e-2`, `grad_norm_clip=40.0`
- `target_update_period=100`, `target_update_rate=None`, `variable_update_period=1000`, `jit_learner=True`
- MPO adds `discrete_policy`, `critic_type`, `value_tx_pair`, model rollout fields, and categorical critic restrictions.

`PPOConfig`:

- `unroll_length=8`, `num_minibatches=8`, `num_epochs=2`, `batch_size=256`
- `ppo_clipping_epsilon=0.2`, `normalize_advantage=False`, `normalize_value=False`, `gae_lambda=0.95`, `discount=0.99`
- `learning_rate=3e-4`, `entropy_cost=3e-4`, `value_cost=1.0`, `max_gradient_norm=0.5`
- `variable_update_period=1`, `pmap_axis_name='devices'`, optional observation normalization factory

### Discrete Online

`DQNConfig`:

- `epsilon=0.05`, `eval_epsilon=None`, `learning_rate=1e-3`, `discount=0.99`, `n_step=5`
- `target_update_period=100`, `max_gradient_norm=np.inf`, `batch_size=256`
- `min_replay_size=1000`, `max_replay_size=1000000`, `importance_sampling_exponent=0.2`, `priority_exponent=0.6`, `samples_per_insert=0.5`
- helper `logspace_epsilons(num_epsilons, epsilon=0.017)`

`IMPALAConfig`:

- `seed=0`, `discount=0.99`, `sequence_length=20`, `sequence_period=None`, `variable_update_period=1000`
- `batch_size=32`, `learning_rate=2e-4`, Adam parameters, `max_gradient_norm=40.0`
- `baseline_cost=0.5`, `entropy_cost=0.01`, `max_abs_reward=np.inf`
- replay controls: `num_prefetch_threads`, `samples_per_insert=1.0`, `max_queue_size=types.Batches(10)`

`R2D2Config`:

- `discount=0.997`, `target_update_period=2500`, `evaluation_epsilon=0.0`, `num_epsilons=256`, `variable_update_period=400`
- sequence settings: `burn_in_length=40`, `trace_length=80`, `sequence_period=40`, `bootstrap_n=5`
- replay controls: `samples_per_insert=4.0`, `min_replay_size=50000`, `max_replay_size=100000`, `batch_size=64`, `prefetch_size=2`, priority exponents

### Offline

`BCConfig`:

- `learning_rate=1e-4`
- `num_sgd_steps_per_step=1`

`CQLConfig`:

- `batch_size=256`, `policy_learning_rate=3e-5`, `critic_learning_rate=3e-4`, `tau=0.005`
- `fixed_cql_coefficient=5.0` or `None` for adaptive coefficient
- `cql_lagrange_threshold=None`, `cql_num_samples=10`, `num_sgd_steps_per_step=1`
- `reward_scale=1.0`, `discount=0.99`, `fixed_entropy_coefficient=0.0`, `target_entropy=0`, `num_bc_iters=50000`

`CRRConfig`:

- `learning_rate=3e-4`, `discount=0.99`, `target_update_period=100`, `use_sarsa_target=False`

`BVEConfig`:

- `epsilon=0.05`, `learning_rate=3e-4`, `discount=0.99`, `target_update_period=2500`
- `max_gradient_norm=np.inf`, `max_abs_reward=1.0`, `huber_loss_parameter=1.0`, `batch_size=256`, `num_sgd_steps_per_step=1`

`MBOPConfig`:

- `mppi_config=MPPIConfig()`
- `learning_rate=3e-4`
- `num_networks=5`
- `num_sgd_steps_per_step=1`

### Imitation / Demonstrations / Exploration

`AILConfig`:

- `direct_rl_batch_size`, `is_sequence_based=False`, `share_iterator=True`, `num_sgd_steps_per_step=1`
- `discriminator_batch_size=256`, `policy_variable_name=None`, `discriminator_optimizer=None`
- replay controls: `replay_table_name='ail_table'`, `prefetch_size=4`, `discount=0.99`, `min_replay_size=1000`, `max_replay_size=1e6`
- `policy_to_expert_data_ratio=None`

`PWILConfig`:

- `num_transitions_rb=50000`, `use_actions_for_distance=True`, `alpha=5.0`, `beta=5.0`, `prefill_constant_reward=True`, `num_sgd_steps_per_step=1`

`LfdConfig`:

- `initial_insert_count=0`
- `demonstration_ratio=0.01`

`ValueDiceConfig`:

- `policy_learning_rate=1e-5`, `nu_learning_rate=1e-3`, `discount=0.99`, `batch_size=256`
- `alpha=0.05`, `policy_reg_scale=1e-4`, `nu_reg_scale=10.0`
- replay controls and `num_sgd_steps_per_step=1`

`RNDConfig`:

- `predictor_learning_rate=1e-4`, `is_sequence_based=False`, `num_sgd_steps_per_step=1`

## Actor And Variable Utilities

Import paths:

- `from acme.agents.jax import actor_core`
- `from acme.agents.jax import actors`
- `from acme.jax import variable_utils`

Useful APIs:

- `actor_core.batched_feed_forward_to_actor_core(policy)` converts a feed-forward policy function into an `ActorCore`.
- `actors.GenericActor(actor_core, random_key, variable_client, adder=None, jit=True, backend='cpu', per_episode_update=False)` implements a JAX actor on top of `ActorCore`.
- `variable_utils.VariableClient(client, key, update_period=1, device=None)` fetches variables from learners or variable sources; use key `'policy'` for most policy learners.
- `variable_utils.ReferenceVariableSource` is used by distributed inference-server mode to pass variable references instead of copying params to actors.

## Saving, Snapshotting, And Running Statistics

Import paths:

- `from acme.jax import savers`
- `from acme.jax import snapshotter`
- `from acme.jax import running_statistics`

Useful APIs:

- `savers.save_to_path(ckpt_dir, state)` and `savers.restore_from_path(ckpt_dir)` save/load nested JAX array state.
- `savers.Checkpointer(object_to_save, directory='~/acme', subdirectory='default', **kwargs)` wraps the TensorFlow checkpointer.
- `savers.CheckpointingRunner` wraps saveable workers with periodic checkpointing.
- `snapshotter.JAXSnapshotter(variable_source, models, path, subdirectory=None, max_to_keep=None, add_uid=False)` periodically writes converted TensorFlow SavedModels.
- `snapshotter.model_to_tf_module(model)` converts `types.ModelToSnapshot` through `jax2tf`.
- `running_statistics.NestedMeanStd`, `RunningStatisticsState`, `NestStatisticsConfig`, `init_state`, `update`, and normalization helpers support observation/data normalization. Pay attention to exact nested structure and batch dimensions.

## Offline Dataset Shape Notes

Acme offline JAX builders expect iterators over Acme sample types, commonly `acme.types.Transition` or `reverb.ReplaySample` depending on the builder. The dataset factory should use the same `EnvironmentSpec` that the network factory uses.

For MBOP, dataset preparation is stricter:

- demonstrations should be timestep-batched transition triples;
- examples convert episodes with `mbop.episodes_to_timestep_batched_transitions(..., return_horizon=...)`;
- normalization statistics can be computed with `mbop.get_normalization_stats(...)` and applied with `running_statistics.normalize`;
- `MPPIConfig.n_trajectories` should be a multiple of `num_networks` when using ensemble planning.
