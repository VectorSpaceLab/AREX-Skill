# High-Level API Reference

This reference summarizes Tianshou 2.0.1 high-level experiment APIs for future agents writing builder-based experiment skeletons. It intentionally favors stable public names and concise decision notes over full source-level detail.

## Core Construction Objects

### `ExperimentConfig`

Run-level dataclass for generic experiment behavior. Important fields:

| Field | Use |
| --- | --- |
| `seed=42` | Seeds PyTorch/numpy and high-level environment creation. |
| `device="cuda" if torch.cuda.is_available() else "cpu"` | Device used for model creation and policy restore; set `"cpu"` for portable examples. |
| `policy_restore_directory=None` | Directory from a prior high-level run to restore policy parameters. |
| `train=True` | Whether `Experiment.run()` trains before optional watch. |
| `watch=True` | Whether to watch/render after training; disable for headless checks. |
| `watch_num_episodes=10`, `watch_render=0.0` | Watch collection count and render delay. |
| `persistence_base_dir="log"` | Base directory for persisted experiment runs. |
| `persistence_enabled=True` | Enables run directories, experiment pickle, model/log persistence. |
| `log_file_enabled=True` | Enables `log.txt` when persistence is enabled. |
| `policy_persistence_mode=PolicyPersistence.Mode.POLICY` | Controls policy persistence strategy. |

### `EnvFactoryRegistered`

Signature: `EnvFactoryRegistered(*, task, venv_type, envpool_factory=None, render_mode_training=None, render_mode_test=None, render_mode_watch="human", **make_kwargs)`.

Use it for Gymnasium-registered tasks. It calls `gymnasium.make(task, **kwargs)` with render-mode settings adapted for training, test, and watch modes. It can delegate vectorized creation to `EnvPoolFactory` when envpool is installed, but portable snippets should use normal Gymnasium creation.

### `VectorEnvType`

Available values include:

| Value | Notes |
| --- | --- |
| `VectorEnvType.DUMMY` | Sequential vector env; safest default for examples and smoke checks. |
| `VectorEnvType.SUBPROC` | Multiprocessing vector env. Avoid in notebooks/Windows/CI unless needed. |
| `VectorEnvType.SUBPROC_SHARED_MEM_DEFAULT_CONTEXT` | Shared-memory subprocess vector env with default multiprocessing context. |
| `VectorEnvType.SUBPROC_SHARED_MEM_FORK_CONTEXT` | Shared-memory subprocess vector env with `fork` context. |
| `VectorEnvType.SUBPROC_SHARED_MEM_AUTO` | Chooses default context on Windows and fork elsewhere. |
| `VectorEnvType.RAY` | Uses Ray; requires Ray installation and initialization assumptions. |

### Training Configs

`TrainingConfig`, `OnlineTrainingConfig`, `OffPolicyTrainingConfig`, and `OnPolicyTrainingConfig` are keyword-only dataclasses.

Common online fields:

| Field | Default | Notes |
| --- | --- | --- |
| `max_epochs` | `100` | Upper bound on epochs. |
| `epoch_num_steps` | `30000` | Online: environment-step target per epoch. |
| `num_training_envs` | `-1` | `-1` expands to CPU count; set an explicit small number in examples. |
| `num_test_envs` | `1` | Test vector env count. |
| `test_step_num_episodes` | `-1` | `-1` becomes `num_test_envs`. |
| `buffer_size` | `4096` | Replay/sample buffer size. |
| `collection_step_num_env_steps` | `2048` | Mutually exclusive with `collection_step_num_episodes`. |
| `collection_step_num_episodes` | `None` | Use episode-count collection instead of step-count collection. |
| `start_timesteps` | `0` | Initial collection before training. |
| `start_timesteps_random` | `False` | Use random actions for prefill when true. |
| `test_in_training` | `False` | Online early-test behavior when stop conditions may be satisfied. |

Off-policy fields:

| Field | Default | Notes |
| --- | --- | --- |
| `batch_size` | `64` | Batch sampled from replay buffer for gradient update. |
| `update_step_num_gradient_steps_per_sample` | `1.0` | Gradient updates per collected sample. |

On-policy fields:

| Field | Default | Notes |
| --- | --- | --- |
| `batch_size` | `64` | Set `None` to use the full collected buffer for updates. |
| `update_step_num_repetitions` | `1` | Number of update passes over collected on-policy data. |

## Experiment and Builder Methods

### `Experiment.run`

Installed signature: `Experiment.run(self, run_name=None, logger_run_id=None, raise_error_on_dirname_collision=True)`.

`run_name` controls the persisted subdirectory name when persistence is enabled. `logger_run_id` matters for logger backends such as wandb. Set `raise_error_on_dirname_collision=False` only when intentionally resuming or overwriting a run name.

### Shared `ExperimentBuilder` Methods

All algorithm-specific builders accept `(env_factory, experiment_config=None, training_config=None)` and provide:

| Method | Use |
| --- | --- |
| `.with_name(name)` | Set experiment/run name used by persistence and display. |
| `.with_logger_factory(factory)` | Customize logging backend. |
| `.with_optim_default(factory)` | Change default optimizer factory used by params with `optim=None`. |
| `.with_algorithm_wrapper_factory(factory)` | Wrap created algorithms, for example intrinsic motivation wrappers. |
| `.with_collector_factory(factory)` | Override collector factory; route detailed collector work to data-collection. |
| `.with_epoch_train_callback(callback)` | Callback at beginning of each training epoch. |
| `.with_epoch_test_callback(callback)` | Callback at beginning of each test phase. |
| `.with_epoch_stop_callback(callback)` | Stop condition based on test mean reward. |
| `.build()` | Create an `Experiment` without running it. |
| `.build_seeded_collection(num_experiments)` | Create multiple experiments with incremented seeds. |
| `.build_and_run(num_experiments=1, launcher=..., perform_rliable_analysis=True)` | Build and execute one or more experiments. |

### Algorithm Builder Map

| Builder | Training config | Action-space fit | Main params method | Network/factory methods |
| --- | --- | --- | --- | --- |
| `DQNExperimentBuilder` | `OffPolicyTrainingConfig` | Discrete | `.with_dqn_params(DQNParams(...))` | `.with_model_factory(...)`, `.with_model_factory_default(hidden_sizes, hidden_activation=...)` |
| `IQNExperimentBuilder` | `OffPolicyTrainingConfig` | Discrete | `.with_iqn_params(IQNParams(...))` | `.with_preprocess_network_factory(...)` |
| `DiscreteSACExperimentBuilder` | `OffPolicyTrainingConfig` | Discrete | `.with_sac_params(DiscreteSACParams(...))` | `.with_actor_factory_default(...)`, critic factory methods |
| `PPOExperimentBuilder` | `OnPolicyTrainingConfig` | Discrete or continuous | `.with_ppo_params(PPOParams(...))` | `.with_actor_factory_default(...)`, `.with_critic_factory_default(...)`, `.with_critic_factory_use_actor()` |
| `A2CExperimentBuilder` | `OnPolicyTrainingConfig` | Discrete or continuous | `.with_a2c_params(A2CParams(...))` | actor and critic factory methods |
| `ReinforceExperimentBuilder` | `OnPolicyTrainingConfig` | Discrete or continuous | `.with_reinforce_params(ReinforceParams(...))` | actor factory methods |
| `NPGExperimentBuilder` | `OnPolicyTrainingConfig` | Discrete or continuous | `.with_npg_params(NPGParams(...))` | actor and critic factory methods |
| `TRPOExperimentBuilder` | `OnPolicyTrainingConfig` | Discrete or continuous | `.with_trpo_params(TRPOParams(...))` | actor and critic factory methods |
| `SACExperimentBuilder` | `OffPolicyTrainingConfig` | Continuous | `.with_sac_params(SACParams(...))` | actor plus dual critic factory methods |
| `DDPGExperimentBuilder` | `OffPolicyTrainingConfig` | Continuous | `.with_ddpg_params(DDPGParams(...))` | deterministic actor plus critic methods |
| `TD3ExperimentBuilder` | `OffPolicyTrainingConfig` | Continuous | `.with_td3_params(TD3Params(...))` | deterministic actor plus dual critic methods |
| `REDQExperimentBuilder` | `OffPolicyTrainingConfig` | Continuous | `.with_redq_params(REDQParams(...))` | actor plus critic ensemble methods |

## Algorithm Params Notes

### `DQNParams`

Live installed facts include DQN algorithm signature `DQN(policy, optim, gamma=0.99, n_step_return_horizon=1, target_update_freq=0, is_double=True, huber_loss_delta=None)`. High-level `DQNParams` feeds these plus policy epsilon and optimizer settings:

- `lr=1e-3`, `optim=None`, `lr_scheduler=None` from the single-model optimizer mixin.
- `gamma=0.99` and `n_step_return_horizon=1`.
- `target_update_freq=0`; nonzero values enable periodic target network updates.
- `eps_training=0.0`, `eps_inference=0.0`; increase training epsilon for exploration.
- `is_double=True` and `huber_loss_delta=None`.

### `PPOParams`

Live installed facts include PPO algorithm signature `PPO(policy, critic, optim, eps_clip=0.2, dual_clip=None, value_clip=False, advantage_normalization=True, recompute_advantage=False, vf_coef=0.5, ent_coef=0.01, max_grad_norm=None, gae_lambda=0.95, max_batchsize=256, gamma=0.99, return_scaling=False)`.

High-level `PPOParams` exposes matching names and optimizer/model factory values through inherited actor-critic params. Use `eps_clip`, `dual_clip`, `value_clip`, `advantage_normalization`, and `recompute_advantage` for PPO-specific behavior; use `vf_coef`, `ent_coef`, `max_grad_norm`, `gae_lambda`, `gamma`, and `return_scaling` for actor-critic/general advantage behavior.

### `SACParams` and `DiscreteSACParams`

Live installed facts include SAC algorithm signature `SAC(policy, policy_optim, critic, critic_optim, critic2=None, critic2_optim=None, tau=0.005, gamma=0.99, alpha=0.2, n_step_return_horizon=1, deterministic_eval=True)`.

High-level SAC params map optimizer factories and learning rates to actor/critic optimizers. Continuous `SACParams` also covers exploration noise and action scaling behavior. `DiscreteSACParams` uses the same SAC core without continuous action-scaling fields.

## Trainer Callback Helpers

Useful built-ins from `tianshou.highlevel.trainer`:

| Class | Use |
| --- | --- |
| `EpochStopCallbackRewardThreshold(threshold=None)` | Stop after test mean reward reaches a threshold; `None` uses `env.spec.reward_threshold`. |
| `EpochTrainCallbackDQNSetEps(eps)` | Set DQN training epsilon at epoch start. |
| `EpochTrainCallbackDQNEpsLinearDecay(eps_train, eps_train_final, decay_steps=1000000)` | Linear DQN epsilon decay by environment step. |
| `EpochTestCallbackDQNSetEps(eps)` | Set DQN inference epsilon at test phase. |

Callback details that touch collector behavior or trainer internals should stay small in high-level examples; deep custom callback/data-flow work belongs in procedural or data-collection guidance.

## Safe Construction Checks

For a construction-only validation, future agents can:

1. Import high-level classes.
2. Build `EnvFactoryRegistered(task="CartPole-v1", venv_type=VectorEnvType.DUMMY)`.
3. Build `ExperimentConfig(device="cpu", persistence_enabled=False, log_file_enabled=False, watch=False)`.
4. Build a tiny `OffPolicyTrainingConfig`.
5. Chain `DQNExperimentBuilder(...).with_dqn_params(...).with_model_factory_default(...).build()`.
6. Assert that `experiment.config.persistence_enabled is False`, `experiment.config.watch is False`, and `experiment.training_config.num_training_envs` matches the requested value.

Use the bundled `scripts/check_highlevel_cartpole.py` for this exact smoke path.
