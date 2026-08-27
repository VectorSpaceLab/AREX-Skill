# High-Level Builder Workflows

This reference is for constructing Tianshou 2.0.1 high-level experiments without reopening the source repository. It focuses on declarative experiment builders that create environments, policies, algorithms, collectors, replay buffers, trainers, logging, persistence, and optional watch runs from configuration objects.

## Choose the High-Level API

Use high-level builders when the user wants to apply an existing Tianshou algorithm with minimal boilerplate. They are a good fit for:

- Gymnasium-style tasks with standard observation and action spaces.
- Benchmark-like experiment skeletons that should be easy to repeat.
- Quick DQN/PPO/SAC/A2C/DDPG/TD3/TRPO/NPG/Reinforce/REDQ/IQN setup.
- Requests that mention `ExperimentBuilder`, `DQNExperimentBuilder`, `PPOExperimentBuilder`, `ExperimentConfig`, or algorithm params dataclasses.

Switch to `../procedural-training/SKILL.md` when the user needs to manually construct networks, policies, optimizers, replay buffers, collectors, trainer params, or custom training loops. Switch to `../data-collection/SKILL.md` for replay-buffer or collector internals. Switch to `../envs-and-vectorization/SKILL.md` for optional environment backends, vector engine troubleshooting, or environment registration issues.

## Builder Skeleton

A portable construction-first skeleton uses small counts, CPU, no persistence, and no watch:

```python
from tianshou.highlevel.config import OffPolicyTrainingConfig
from tianshou.highlevel.env import EnvFactoryRegistered, VectorEnvType
from tianshou.highlevel.experiment import DQNExperimentBuilder, ExperimentConfig
from tianshou.highlevel.params.algorithm_params import DQNParams
from tianshou.highlevel.trainer import EpochStopCallbackRewardThreshold

experiment = (
    DQNExperimentBuilder(
        EnvFactoryRegistered(task="CartPole-v1", venv_type=VectorEnvType.DUMMY),
        ExperimentConfig(
            seed=42,
            device="cpu",
            persistence_enabled=False,
            log_file_enabled=False,
            watch=False,
        ),
        OffPolicyTrainingConfig(
            max_epochs=1,
            epoch_num_steps=32,
            num_training_envs=1,
            num_test_envs=1,
            buffer_size=256,
            batch_size=32,
            collection_step_num_env_steps=8,
            update_step_num_gradient_steps_per_sample=0.125,
        ),
    )
    .with_dqn_params(DQNParams(lr=1e-3, gamma=0.9, n_step_return_horizon=3, target_update_freq=32, eps_training=0.1))
    .with_model_factory_default(hidden_sizes=(64, 64))
    .with_epoch_stop_callback(EpochStopCallbackRewardThreshold(195))
    .with_name("cartpole_dqn_highlevel")
    .build()
)
```

Call `experiment.run()` only when the user asked to train or when a bounded verification run is appropriate. For a build-only check, inspect the resulting `experiment.name`, `experiment.config`, and `experiment.training_config` instead of starting training.

## Main Configuration Decisions

### Environment Factory

Use `EnvFactoryRegistered(task=..., venv_type=VectorEnvType.DUMMY, **make_kwargs)` for environments registered with Gymnasium. Pass Gymnasium creation options such as render modes or custom environment kwargs through `EnvFactoryRegistered`; Tianshou handles train/test/watch modes internally.

Prefer `VectorEnvType.DUMMY` for local smoke tests and notebooks because it avoids multiprocessing and optional services. Consider `VectorEnvType.SUBPROC` or shared-memory variants only for long runs where process spawning is safe. Use `VectorEnvType.RAY` only when Ray is installed and intentionally selected.

Tianshou high-level env factories seed created environments from `ExperimentConfig.seed` during experiment-world construction. Avoid relying on old constructor patterns that pass separate `training_seed` or `test_seed` values unless the installed package signature explicitly supports them.

### ExperimentConfig

`ExperimentConfig` controls run-level behavior rather than RL hyperparameters:

- `seed`: initializes Tianshou/PyTorch/numpy and drives environment factory seeding.
- `device`: defaults to CUDA when `torch.cuda.is_available()`; set `device="cpu"` for portable examples.
- `train`: set `False` only when restoring/watching or constructing worlds without training.
- `watch`: defaults to `True`; set `False` for CI, headless servers, and smoke scripts.
- `watch_num_episodes` and `watch_render`: affect post-training watch only.
- `persistence_base_dir`: base directory for saved experiment runs when persistence is enabled.
- `persistence_enabled`: set `False` to avoid creating log/pickle/model directories.
- `log_file_enabled`: only matters when persistence is enabled.
- `policy_restore_directory`: restores policy parameters from a persisted prior run.

For safe generated examples, use `ExperimentConfig(persistence_enabled=False, log_file_enabled=False, watch=False, device="cpu")` unless the user explicitly asks for saved experiment artifacts or rendered watching.

### Training Config

Use `OffPolicyTrainingConfig` for off-policy algorithms such as DQN, IQN, SAC, Discrete SAC, DDPG, TD3, and REDQ. Use `OnPolicyTrainingConfig` for PPO, A2C, TRPO, NPG, and Reinforce.

Common fields include:

- `max_epochs`: upper bound on training epochs.
- `epoch_num_steps`: per-epoch environment-step target for online algorithms.
- `num_training_envs` and `num_test_envs`: vector environment counts; `num_training_envs=-1` uses CPU count and is usually too broad for snippets.
- `test_step_num_episodes`: defaults to `num_test_envs` when `-1`.
- `buffer_size`: replay/sample buffer size.
- `collection_step_num_env_steps` versus `collection_step_num_episodes`: exactly one must be set.
- `start_timesteps` and `start_timesteps_random`: optional prefill before training.
- `test_in_training`: allows early test checks during online training when a stop criterion looks satisfied.

Off-policy adds `batch_size` and `update_step_num_gradient_steps_per_sample`. On-policy adds `batch_size` and `update_step_num_repetitions`.

## Algorithm Builder Recipes

### DQN for Discrete Tasks

Use `DQNExperimentBuilder` with `DQNParams` and either `.with_model_factory_default(hidden_sizes=...)` or `.with_model_factory(...)` for custom Q-network factories. DQN requires a discrete action space.

Useful DQN params include `lr`, `gamma`, `n_step_return_horizon`, `target_update_freq`, `eps_training`, `eps_inference`, `is_double`, and `huber_loss_delta`.

### PPO/A2C/TRPO/NPG/Reinforce

Use `OnPolicyTrainingConfig`. Actor-critic builders such as `PPOExperimentBuilder` and `A2CExperimentBuilder` can use `.with_actor_factory_default(...)`, `.with_critic_factory_default(...)`, or `.with_critic_factory_use_actor()` for parameter sharing. PPO-specific params include `eps_clip`, `dual_clip`, `value_clip`, `advantage_normalization`, and `recompute_advantage` on top of actor-critic settings such as `vf_coef`, `ent_coef`, `max_grad_norm`, `gae_lambda`, `gamma`, and `return_scaling`.

### SAC and Discrete SAC

Use `SACExperimentBuilder` for continuous action spaces and `DiscreteSACExperimentBuilder` for discrete action spaces. Use `SACParams` or `DiscreteSACParams` with off-policy training. Continuous SAC commonly configures actor and critic factories; discrete SAC uses actor/critic factories for discrete policies. Key params include `actor_lr`, `critic1_lr`, `critic2_lr`, `tau`, `gamma`, `alpha`, `n_step_return_horizon`, and `deterministic_eval`.

### Multi-Run Collections

Use `builder.build_seeded_collection(num_experiments)` to create experiments whose seeds are incremented from `ExperimentConfig.seed`. Use `builder.build_and_run(num_experiments=..., launcher="sequential")` for explicit multi-run execution. Joblib or other launchers should be used only when dependencies and process constraints are known.

## Persistence, Logging, and Watch Cautions

- `persistence_enabled=True` creates run directories under `persistence_base_dir` and can fail on name collisions unless `Experiment.run(..., raise_error_on_dirname_collision=False)` is used intentionally.
- `log_file_enabled=False` prevents file logging only when persistence is enabled; external loggers may still write elsewhere.
- `watch=True` creates a watch environment and calls rendering after training. Disable it for headless CI, notebooks without display support, and smoke scripts.
- `device` defaults to CUDA on machines where PyTorch sees a GPU. Set `device="cpu"` for portable snippets and for debugging unexpected CUDA memory/device behavior.
- `policy_restore_directory` expects a prior Tianshou high-level persistence directory containing compatible policy parameters.

## Convert Procedural Requests to High-Level

A procedural request can be converted to high-level when it only specifies standard algorithm, environment, network hidden sizes, optimizer LR, basic training counts, and a stop condition. Map these pieces as follows:

- Environment id and Gymnasium kwargs -> `EnvFactoryRegistered`.
- Global seed/device/watch/persistence -> `ExperimentConfig`.
- Epochs, env counts, buffer size, batch size, collect/update cadence -> `OffPolicyTrainingConfig` or `OnPolicyTrainingConfig`.
- Algorithm hyperparameters -> `DQNParams`, `PPOParams`, `SACParams`, or the matching params dataclass.
- Hidden-layer tuple -> `.with_model_factory_default(...)`, `.with_actor_factory_default(...)`, and/or `.with_critic_factory_default(...)`.
- Reward threshold -> `.with_epoch_stop_callback(EpochStopCallbackRewardThreshold(...))`.

Do not convert when the request depends on custom collector hooks, manual replay-buffer fields, nonstandard policy forward behavior, custom trainer loops, or custom algorithm update logic; route to the procedural/data-collection sub-skills instead.
