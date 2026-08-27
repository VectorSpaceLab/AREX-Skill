# Procedural Training Workflows

This reference is for Tianshou 2.0.1 low-level training code. The procedural API exposes the same algorithm implementations as the high-level API, but you are responsible for every object boundary.

## Construction Order

1. **Define task and counts**: choose the Gymnasium task, seeds, `num_training_envs`, `num_test_envs`, `buffer_size`, `batch_size`, `epoch_num_steps`, and collection/update counts.
2. **Create environments**: use a single probe environment for shapes and `DummyVectorEnv([lambda: gym.make(task) ...])` or `SubprocVectorEnv(...)` for train/test environments.
3. **Validate spaces**: DQN-style policies require `gym.spaces.Discrete`; SAC/DDPG/TD3 and many MuJoCo examples require `gym.spaces.Box`; dict observations require a model that knows how to unpack the dict or a wrapper that flattens it safely.
4. **Build networks**: use `SpaceInfo.from_env(env)` for `state_shape` and `action_shape`, then choose `Net`, `MLP`, `DiscreteActor`, `DiscreteCritic`, `ContinuousActor`, `ContinuousActorProbabilistic`, and `ContinuousCritic` as appropriate.
5. **Create optimizer factories**: pass `AdamOptimizerFactory(...)`, `RMSpropOptimizerFactory(...)`, or `TorchOptimizerFactory(...)` to algorithms. Tianshou creates optimizer instances from the modules internally.
6. **Create policy**: policies map observations to actions or distributions and own action mapping/scaling semantics.
7. **Create algorithm**: algorithms own update logic, target networks, critics, optimizers, and `run_training(params)`.
8. **Create buffers and collectors**: off-policy collectors need a replay buffer; on-policy collectors still collect rollout data but the trainer clears/uses it as fresh data.
9. **Create trainer params**: choose `OffPolicyTrainerParams`, `OnPolicyTrainerParams`, or `OfflineTrainerParams` and ensure exactly one online collection count is set.
10. **Smoke before training**: reset collectors, collect a tiny number of steps, run one policy forward or `compute_action`, and inspect tensor/action shapes before launching long training.

## Off-Policy Loop

Use off-policy trainer params for algorithms that can learn from replayed experience, including DQN, SAC, DDPG, TD3, REDQ, and many Q-learning variants.

Minimal flow:

```python
training_collector = Collector(algorithm, training_envs, VectorReplayBuffer(buffer_size, len(training_envs)), exploration_noise=True)
test_collector = Collector(algorithm, test_envs, exploration_noise=True)
result = algorithm.run_training(
    OffPolicyTrainerParams(
        training_collector=training_collector,
        test_collector=test_collector,
        max_epochs=epoch,
        epoch_num_steps=epoch_num_steps,
        collection_step_num_env_steps=collection_step_num_env_steps,
        test_step_num_episodes=num_test_envs,
        batch_size=batch_size,
        update_step_num_gradient_steps_per_sample=update_per_step,
    )
)
```

Operational checks:

- Use `VectorReplayBuffer(buffer_size, len(training_envs))` when collecting from vectorized training environments.
- `collection_step_num_env_steps` counts transitions, but with vectorized envs the actual count rounds up to a multiple of the number of training envs.
- `update_step_num_gradient_steps_per_sample` multiplies the number of newly collected samples to determine gradient steps.
- For DQN, set `exploration_noise=True` on collectors so epsilon-greedy behavior is active during collection.
- For SAC/DDPG/TD3, seed the buffer with random or exploratory steps if the algorithm needs warm-up before updates.

## On-Policy Loop

Use on-policy trainer params for PPO, A2C, NPG, TRPO, and Reinforce-style algorithms that update from freshly collected rollouts.

Minimal flow:

```python
training_collector = Collector(algorithm, training_envs, buffer, exploration_noise=True)
test_collector = Collector(algorithm, test_envs)
result = algorithm.run_training(
    OnPolicyTrainerParams(
        training_collector=training_collector,
        test_collector=test_collector,
        max_epochs=epoch,
        epoch_num_steps=epoch_num_steps,
        collection_step_num_env_steps=collection_step_num_env_steps,
        update_step_num_repetitions=repeat_per_rollout,
        test_step_num_episodes=num_test_envs,
        batch_size=batch_size,
    )
)
```

Operational checks:

- Set `collection_step_num_env_steps` large enough for a useful rollout batch; PPO examples often collect thousands of env steps per update.
- Use `update_step_num_repetitions` for repeated passes over the fresh rollout; do not use the off-policy `update_step_num_gradient_steps_per_sample` field.
- On-policy buffers are consumed as current rollout data; do not rely on old replay data for PPO/A2C/TRPO/NPG/Reinforce.
- For continuous stochastic actors, pair actor output with a compatible distribution function such as `Independent(Normal(loc, scale), 1)`.

## Offline Trainer Expectations

`OfflineTrainerParams` is for algorithms that train from a fixed `ReplayBuffer` and do not collect online environment interaction during training. It requires `buffer` and `batch_size`; do not pass online collectors. Route offline and imitation specializations to `../offline-and-specialized-rl/SKILL.md` unless the user only needs the trainer distinction.

## Custom Policy Extension

Subclass `Policy` or a concrete policy when built-ins do not express the action selection semantics.

Required responsibilities:

- Implement `forward(batch, state=None, **kwargs)` and return a `Batch` with at least `act`; include `state`, `logits`, `dist`, `log_prob`, or `policy` fields when the algorithm expects them.
- Preserve action masks for discrete masked environments by keeping `batch.obs.mask` available to the policy/model and applying it before action selection.
- Implement or rely on `map_action`/`map_action_inverse` consistently for continuous `Box` spaces.
- Ensure the action type returned by `forward` matches the Gymnasium action space and the collector can pass it directly to `env.step` after mapping.

Dict-observation DQN pattern:

- Keep env observations as a mapping such as `{"obs": features, "mask": action_mask}` when masks are needed.
- Build a preprocessing module that extracts the feature tensor from the `Batch`/dict and leaves the mask for `DiscreteQLearningPolicy.forward`.
- Validate with a one-sample `Batch(obs=Batch(obs=..., mask=...), info={})` before creating collectors.

## Custom Algorithm Extension

Subclass `OnPolicyAlgorithm`, `OffPolicyAlgorithm`, or `OfflineAlgorithm` when changing update rules.

Typical responsibilities:

- Implement `_preprocess_batch` only when returns, advantages, target Q values, or sequence fields must be computed before update.
- Implement `_update_with_batch` to run gradients and return a `TrainingStats`-compatible object.
- Use lagged target-network mixins for DQN/DDPG/TD3/SAC-like target networks instead of hand-rolling target copies.
- Override `create_trainer` only when the default trainer class does not match the training mode.

## Trainer Param Validation

For online trainers:

- Exactly one of `collection_step_num_env_steps` and `collection_step_num_episodes` must be set.
- `test_in_training=True` requires both `test_collector` and `stop_fn`.
- `test_step_num_episodes` should be at least the number of test environments when using vectorized test envs for one full episode per env.
- Match trainer param class to algorithm mode; off-policy algorithms expect `OffPolicyTrainerParams`, on-policy algorithms expect `OnPolicyTrainerParams`.

For off-policy trainers:

- `batch_size` samples transitions from the replay buffer per gradient step.
- `update_step_num_gradient_steps_per_sample` is a float; e.g. `0.1` with 10 collected transitions gives about one gradient step.

For on-policy trainers:

- `batch_size=None` means use the full rollout for each update pass.
- `update_step_num_repetitions` controls how many times the fresh rollout is reused.

## Pre-Training Validation Checklist

- `import tianshou`, `import gymnasium`, and `import torch` succeed.
- Environment optional dependencies are installed for the selected task.
- Probe env reset returns observations matching the model input contract.
- `env.action_space` type matches policy/algorithm family.
- Continuous policies use `action_scaling` only with `gym.spaces.Box` and actor output range assumptions are clear.
- Optimizer factories are passed, not already-created `torch.optim.Optimizer` instances.
- Replay buffer type matches vectorization: single env uses `ReplayBuffer`; vectorized envs use `VectorReplayBuffer` or a prioritized vector variant.
- Collector tiny `collect(n_step=...)` succeeds before long training.
- Training/test collectors use the same algorithm object and compatible environment spaces.
