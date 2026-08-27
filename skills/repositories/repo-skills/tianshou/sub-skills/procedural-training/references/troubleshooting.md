# Procedural Training Troubleshooting

Use this checklist when a low-level Tianshou pipeline imports successfully but fails during construction, collection, or the first update.

## Install And Import Failures

Symptoms:

- `ModuleNotFoundError: No module named 'tianshou'`.
- `ModuleNotFoundError` for `gymnasium`, `torch`, `tensorboard`, MuJoCo, Atari, Box2D, VizDoom, EnvPool, robotics, or Ray packages.
- `pip check` or resolver errors after installing extras.

Fixes:

- Verify the installed distribution is `tianshou` and the import is `import tianshou`.
- Keep CPU smoke tests on classic Gymnasium tasks such as `CartPole-v1` unless optional extras are explicitly installed.
- Treat MuJoCo, Atari, Box2D, VizDoom, EnvPool, robotics, and Ray as optional task dependencies, not base procedural requirements.
- If TensorBoard is unavailable, omit `TensorboardLogger`/`SummaryWriter` for construction smoke tests.

## Action-Space Mismatches

Symptoms:

- DQN construction or collection fails on a continuous `Box` action space.
- SAC reports it only supports `gym.spaces.Box`.
- Discrete categorical policy returns values that the environment rejects.
- `env.step` errors with shape or dtype mismatches.

Fixes:

- Use `DiscreteQLearningPolicy` + `DQN` only with `gym.spaces.Discrete` action spaces.
- Use `SACPolicy`, `ContinuousDeterministicPolicy`, `ContinuousActor`, `ContinuousActorProbabilistic`, and `ContinuousCritic` for continuous `Box` action spaces.
- For discrete actor-critic methods, pair `DiscreteActor` or a logits-producing `Net` with a categorical `dist_fn`.
- Assert the action space immediately after creating the probe env, then choose the algorithm family.
- Run a one-observation `policy.compute_action(...)` or forward-pass smoke before constructing long-running trainers.

## Action Scaling And Bounding

Symptoms:

- Continuous actions are outside `env.action_space.low/high`.
- Actions saturate at boundaries and learning is unstable.
- Warnings mention `action_scaling`, `action_bound_method`, or `max_action`.
- Performance differs wildly between environments with different action ranges.

Fixes:

- `action_scaling=True` means policy outputs are expected in normalized `[-1, 1]` and then scaled to the Gymnasium `Box` range.
- Use `action_bound_method='clip'` or `'tanh'` when the policy should bound unscaled actor outputs before scaling.
- SAC actor outputs are already tanh-squashed; `SACPolicy` uses `action_bound_method=None` internally and can scale actions.
- If a custom actor already emits environment-scale actions, set `action_scaling=False` and `action_bound_method=None`.
- Do not enable action scaling for discrete spaces; base `Policy` rejects `action_scaling=True` when the action space is not `Box`.

## Optimizer And Model Wiring

Symptoms:

- Algorithm constructor rejects an optimizer object.
- Loss stays zero because a critic/actor is not registered under the algorithm optimizer.
- Shape errors occur inside `Net`, `ContinuousCritic`, or actor forward calls.

Fixes:

- Pass optimizer factories such as `AdamOptimizerFactory(lr=...)`, not prebuilt `torch.optim.Adam(...)` instances.
- For DQN, ensure `Net(state_shape=..., action_shape=...)` outputs one Q-value per discrete action.
- For continuous Q critics, build `Net(state_shape=..., action_shape=..., concat=True)` so the critic can process observation-action pairs.
- For PPO/A2C/TRPO/NPG/Reinforce, use an actor whose output matches the `dist_fn` and a critic that returns scalar values.
- Move modules to the target device before algorithm construction when using `.to(device)` manually.

## Trainer Count Settings

Symptoms:

- `ValueError: Exactly one of {collection_step_num_env_steps, collection_step_num_episodes} must be set`.
- `test_in_training requires test_collector and stop_fn to be set`.
- Training collects more steps than requested with vectorized envs.
- Off-policy updates are too frequent or never happen.

Fixes:

- Set exactly one online collection count: `collection_step_num_env_steps` or `collection_step_num_episodes`.
- When `test_in_training=True`, also pass `test_collector` and `stop_fn`.
- With vector envs, collection by env steps rounds up to a multiple of `len(training_envs)`.
- Use `update_step_num_gradient_steps_per_sample` only for off-policy trainer params.
- Use `update_step_num_repetitions` only for on-policy trainer params.
- For initial smoke tests, keep counts tiny and avoid `algorithm.run_training(...)`; construct params only after collector and policy checks pass.

## Collector And Buffer Failures

Symptoms:

- Collector fails when no buffer is supplied.
- Vectorized env collection stores transitions incorrectly.
- Replay buffer sampling fails before enough data exists.
- Dict observations or masks disappear after wrappers.

Fixes:

- Off-policy training collectors need a replay buffer; use `VectorReplayBuffer(buffer_size, len(training_envs))` for vectorized training envs.
- Test collectors usually do not need a replay buffer unless test transitions must be stored.
- Collect at least `batch_size` transitions before expecting off-policy updates to sample a full batch.
- For dict observations, verify the model receives the same nested structure emitted by the env reset/step API.
- For action masks, preserve `obs.mask` through wrappers and inspect a policy forward pass before training.

## NaN And Loss Issues

Symptoms:

- Collector reports NaNs in buffer.
- Loss becomes `nan` or explodes after first updates.
- PPO/SAC entropy or log-prob values are invalid.
- DQN targets become unstable.

Fixes:

- Enable `raise_on_nan_in_buffer=True` in `Collector` while debugging data sources.
- Check environment rewards, observations, and `info` fields for NaN/Inf before blaming the algorithm.
- Lower learning rates, reduce `update_step_num_gradient_steps_per_sample`, or add `max_grad_norm` for actor-critic methods.
- For DQN, consider a positive `target_update_freq`, smaller `gamma`, and `huber_loss_delta` when rewards have outliers.
- For PPO, verify `dist_fn` receives valid standard deviations and use `advantage_normalization=True` unless there is a reason not to.
- For SAC, verify actor scale outputs are positive and avoid manually applying extra tanh/scaling outside `SACPolicy`.

## CLI/API Misuse

Symptoms:

- Code copied from examples tries to render or run long training during a smoke test.
- Example imports local helper modules not available outside the source tree.
- Procedural code uses high-level builder config objects and low-level trainer params together.

Fixes:

- Strip rendering, logging side effects, and long loops from construction checks.
- Replace source-tree helper imports with installed-package APIs or small local helper functions.
- Do not mix high-level `ExperimentBuilder` workflows with manual `algorithm.run_training(...)` unless intentionally comparing APIs; route builder requests to `../highlevel-experiments/SKILL.md`.
- Keep scripts bounded with `--help`, explicit counts, and no dependency on the original repository checkout.

## Optional Dependency Decisions

- **Classic control / CartPole**: good for base install smoke tests.
- **MuJoCo**: use only when `mujoco` and compatible Gymnasium MuJoCo support are installed; otherwise keep PPO/SAC examples as reference patterns.
- **Atari / ALE**: requires Atari extras and ROM handling; use data-collection and preprocessing references before training.
- **Box2D / robotics / VizDoom / EnvPool / Ray**: install and validate separately before procedural pipeline debugging.
