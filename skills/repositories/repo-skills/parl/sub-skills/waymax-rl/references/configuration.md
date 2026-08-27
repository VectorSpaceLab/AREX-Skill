# Waymax-RL configuration

The default Waymax-RL config is a Hydra YAML file with a top-level `params` mapping. Training code converts it to a plain container and passes the whole object to rl-games.

## Top-level shape

```yaml
params:
  seed: 1
  algo:
    name: a2c_continuous
  model:
    name: continuous_a2c_logstd
  network:
    ...
  config:
    name: waymax
    env_name: waymax
    multi_gpu: false
    mixed_precision: true
    env_config:
      env_name: waymax
      backend: gpu
      data_cfg:
        data_path: /replace/with/real/file-or-directory
        data_type: tfrecord
```

The names look A2C-oriented because rl-games uses shared continuous actor-critic runners for PPO-like recipes. The training hyperparameters under `params.config` are the practical launch controls.

## Required environment config

| Key | Expected value | Notes |
| --- | --- | --- |
| `params.config.env_name` | `waymax` | Must match the registered rl-games environment configuration. |
| `params.config.env_config.env_name` | `waymax` | Duplicates the inner environment identity. |
| `params.config.env_config.backend` | `gpu` | Passed to `jax.jit(..., backend=...)`; CPU is not an equivalent fallback for this workflow. |
| `params.config.env_config.data_cfg.data_type` | `tfrecord` | This is the only fully evidenced data path in the observed wrapper. |
| `params.config.env_config.data_cfg.data_path` | real file or directory | The default `/your_data_path/...` value is only a placeholder. |
| `params.config.env_config.max_num_objects` | integer, default `128` | Passed to the Waymax dataset/environment config and affects memory. |
| `params.config.env_config.action_space.is_discrete` | `false` | The observed dynamics branch handles continuous control. |
| `params.config.env_config.action_space.steering_acc` | `true` | Enables normalized steering/acceleration bicycle-model actions. |

## Training and batching controls

Important defaults:

- `mixed_precision: true`
- `multi_gpu: false`
- `max_epochs: 1000`
- `horizon_length: 90`
- `num_actors: 512`
- `minibatch_size: 5120`
- `mini_epochs: 5`
- `learning_rate: 3e-4`
- `gamma: 0.99`
- `tau: 0.95`

`num_actors` becomes `env_nums` in the wrapper and also becomes the Waymax dataset batch dimension. With the defaults, one rollout horizon spans `512 * 90 = 46080` actor-steps before minibatching. Reduce `num_actors`, `horizon_length`, or `max_num_objects` first when debugging memory or shape issues.

`minibatch_size` should be chosen with the rollout batch size in mind. A size larger than the collected samples, or a size that interacts poorly with rl-games batching, can fail after the expensive environment setup phase.

## Data path behavior

The environment wrapper checks `data_path` as follows:

1. If it is a directory, list the directory and choose one member at random for the run. For `data_type: pkl`, the wrapper filters to `*.pkl`; for `data_type: tfrecord`, the observed code does not filter names, so keep unrelated files out of the directory.
2. If it is a file, use that single file.
3. Otherwise, raise `OSError(data_path)` during environment construction.

For `data_type: tfrecord`, the wrapper builds a Waymax WOD training dataset config with one selected path, `batch_dims=(num_actors,)`, `max_num_objects`, `num_paths=1`, and `num_points_per_path=200`.

Treat `data_type: pkl` as incomplete unless the user has independently validated it: the observed implementation filters directory names for `.pkl`, but the dataset iterator is only constructed in the `tfrecord` branch.

## Observation, action, and reward implications

- Single observation space is a floating box with shape `(10, 6)`; vectorization adds the actor batch dimension.
- Continuous action space is a normalized two-value box for steering and acceleration when the continuous bicycle-model branch is active.
- The wrapper converts nonzero reward weights from `reward_cfg` into a Waymax linear-combination reward config.
- The observed `step` method returns zero-valued reward tensors while still updating Waymax state and `done`; inspect and test this behavior before assuming the config reward weights affect learner rewards in a production experiment.

## Mixed precision and multi-GPU flags

`mixed_precision: true` is enabled in the default config. Verify that the GPU, JAX version, PyTorch version, and rl-games path support the intended precision mode before long runs.

`multi_gpu: false` is the default. Setting it to true is not a complete distributed-training plan by itself. Confirm both JAX device visibility and rl-games multi-GPU expectations in the actual environment before enabling it.

## Static validation

Use the bundled validator to inspect a candidate Hydra YAML file without importing JAX, Waymax, TensorFlow, Torch, Hydra, or rl-games:

```bash
python ../scripts/validate_waymax_config.py <path-to-hydra-yaml>
```

The validator reports:

- parser used for the YAML;
- whether `env_config.backend` is `gpu`;
- `mixed_precision` and `multi_gpu` values;
- `data_type` and `data_path`;
- whether `data_path` still looks like a placeholder;
- whether a non-placeholder local path currently exists;
- rollout batch scale from `num_actors * horizon_length` when both are present.

A placeholder data path or a non-`gpu` backend is a validation failure because the config is not launch-ready for this workflow.
