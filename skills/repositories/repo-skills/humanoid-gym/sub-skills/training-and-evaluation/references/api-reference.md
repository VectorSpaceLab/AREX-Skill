# API reference

## Package facts

- Distribution name: `humanoid`
- Version: `1.0.0`
- `setup.py` install requirements include `isaacgym`, `wandb`, `DateTime`, `tensorboard`, `tqdm`, `numpy==1.23.5`, `opencv-python`, `mujoco==2.3.6`, `mujoco-python-viewer`, and `matplotlib`.
- `isaacgym` is a manual external dependency; `pip check` fails until it is installed.

## Helper layer (`humanoid/utils/helpers.py`)

| Symbol | Behavior | Notes |
|---|---|---|
| `class_to_dict(obj)` | Recursively converts config objects to dictionaries. | Used before passing nested config objects into the runner and simulator setup. |
| `update_class_from_dict(obj, dict)` | Writes dictionary values back into nested config classes. | Utility for config mutation. |
| `set_seed(seed)` | Seeds Python, NumPy, Torch, and CUDA. | `-1` picks a random seed. |
| `parse_sim_params(args, cfg)` | Builds Isaac Gym `SimParams` from CLI args and config. | Uses `args.physics_engine`, `args.use_gpu`, `args.use_gpu_pipeline`, `args.subscenes`, and `args.num_threads`. |
| `get_load_path(root, load_run=-1, checkpoint=-1)` | Resolves a checkpoint file path from a logs root. | Sorts timestamped run folders, ignores `exported/`, selects latest run/model when values are `-1`. |
| `update_cfg_from_args(env_cfg, cfg_train, args)` | Applies CLI overrides to env/train config. | Updates `num_envs`, `seed`, `max_iterations`, `resume`, `experiment_name`, `run_name`, `load_run`, and `checkpoint`. |
| `get_args()` | Parses Isaac Gym + repo-specific CLI args. | Public source default task is `XBotL_free`, but the registered task in this checkout is `humanoid_ppo`. After parse it normalizes `args.sim_device` and `args.sim_device_id`. |
| `export_policy_as_jit(actor_critic, path)` | Scripts and saves the policy actor only. | Always saves `policy_1.pt` under the target directory. |

## Task registry (`humanoid/utils/task_registry.py`)

| Symbol | Behavior | Notes |
|---|---|---|
| `TaskRegistry.register(name, task_class, env_cfg, train_cfg)` | Registers a task, env config, and training config. | Public task registration happens in `humanoid/envs/__init__.py`. |
| `TaskRegistry.get_cfgs(name)` | Returns registered env/train configs. | Copies the training seed into `env_cfg.seed`. |
| `TaskRegistry.make_env(name, args=None, env_cfg=None)` | Instantiates the Isaac Gym environment. | Applies CLI config overrides, seeds, sim params, `sim_device`, and `headless`. |
| `TaskRegistry.make_alg_runner(env, name=None, args=None, train_cfg=None, log_root="default")` | Instantiates the PPO runner and optional resume path. | Builds `logs/<experiment_name>/<date_time>_<run_name>/` when `log_root="default"`; resolves the runner class with `eval(...)`; resumes only when `train_cfg.runner.resume` is true. |

## PPO stack (`humanoid/algo/ppo/`)

### `ActorCritic`

```python
ActorCritic(
    num_actor_obs,
    num_critic_obs,
    num_actions,
    actor_hidden_dims=[256, 256, 256],
    critic_hidden_dims=[256, 256, 256],
    init_noise_std=1.0,
    activation=nn.ELU(),
)
```

- Builds separate actor and critic MLPs.
- `act_inference(observations)` returns deterministic mean actions.
- `act(observations)` samples from a Normal policy.
- `evaluate(critic_observations)` returns value predictions.
- Confirmed shape smoke: `ActorCritic(705, 219, 12)` works, and zero-input inference returns shape `(1, 12)`.

### `PPO`

```python
PPO(
    actor_critic,
    num_learning_epochs=1,
    num_mini_batches=1,
    clip_param=0.2,
    gamma=0.998,
    lam=0.95,
    value_loss_coef=1.0,
    entropy_coef=0.0,
    learning_rate=1e-3,
    max_grad_norm=1.0,
    use_clipped_value_loss=True,
    schedule="fixed",
    desired_kl=0.01,
    device="cpu",
)
```

- `init_storage(...)` allocates rollout storage.
- `act(obs, critic_obs)` records the transition and returns actions.
- `process_env_step(rewards, dones, infos)` stores step data and handles time-out bootstrapping.
- `compute_returns(last_critic_obs)` computes GAE-style returns.
- `update()` runs minibatch optimization and optional adaptive LR updates when `schedule="adaptive"`.
- `load(path, load_optimizer=True)` restores model and optional optimizer state.
- `save(path, infos=None)` writes model state, optimizer state, and iteration metadata.

### `RolloutStorage`

- Stores observations, privileged observations, actions, rewards, dones, values, returns, advantages, means, and sigmas.
- `mini_batch_generator(...)` yields feed-forward minibatches with hidden states and masks as `None` in this code path.
- `compute_returns(last_values, gamma, lam)` performs reverse-time advantage accumulation.

### `OnPolicyRunner`

```python
OnPolicyRunner(env, train_cfg, log_dir=None, device="cpu")
```

- Constructs `ActorCritic` and `PPO` from config strings.
- Resolves `policy_class_name` and `algorithm_class_name` with `eval(...)`, so custom class names must be imported into scope.
- Uses `wandb.init(project="XBot", sync_tensorboard=True, ...)` when logging is enabled.
- `learn(num_learning_iterations, init_at_random_ep_len=False)` collects rollouts, updates PPO, and saves checkpoints.
- `save(path, infos=None)` writes `model_state_dict`, `optimizer_state_dict`, and iteration counters.
- `get_inference_policy(device=None)` returns `actor_critic.act_inference` in eval mode.

## Confirmed XBot-L config facts

From the bundled `XBotLCfg` and `XBotLCfgPPO`:

- `frame_stack = 15`
- `num_single_obs = 47`
- `num_observations = 705`
- `c_frame_stack = 3`
- `single_num_privileged_obs = 73`
- `num_privileged_obs = 219`
- `num_actions = 12`
- `num_envs = 4096`
- `experiment_name = "XBot_ppo"`
- `num_steps_per_env = 60`
- `max_iterations = 3001`
- `save_interval = 100`
- Actor hidden dims: `[512, 256, 128]`
- Critic hidden dims: `[768, 256, 128]`

## Practical interpretation

- Training checkpoints live under `logs/<experiment_name>/<date_time>_<run_name>/model_<iteration>.pt`.
- Exported policies live under `logs/<experiment_name>/exported/policies/policy_1.pt`.
- `play.py` exports the actor only; it does not export the critic.
- The runner logs with both W&B and TensorBoard unless the logging path is bypassed.
