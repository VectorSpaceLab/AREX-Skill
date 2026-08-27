# Workflows: Environment Integration

## Validate a Custom Gymnasium Env

1. Ensure the env implements Gymnasium reset and step signatures: `reset(seed=None, options=None)` returns `(obs, info)` and `step(action)` returns `(obs, reward, terminated, truncated, info)`.
2. Define `action_space` and `observation_space` before vectorization; Tianshou workers read them during initialization.
3. Avoid tuple observations; use arrays or dictionaries. Tianshou vector env reset rejects tuple observations.
4. Check that batched observations can be `np.stack`ed; variable-length observations become `dtype=object` arrays and may break model code later.
5. Smoke with `DummyVectorEnv([make_env for _ in range(n)])`, call `reset()`, sample one action per env, call `step()`, then `close()`.
6. Only after the dummy smoke passes, try subprocess or shared-memory vectorization.

## Choose a Vectorization Backend

- Use `DummyVectorEnv` for correctness checks, examples, unit tests, notebooks, and environments whose step time is tiny.
- Use `SubprocVectorEnv` when env stepping is expensive enough to amortize process overhead or when env state should be isolated.
- Use `ShmemVectorEnv` when subprocess envs return fixed-shape array/dict/tuple observations and copying observations through pipes is a bottleneck.
- Use async `wait_num` or `timeout` only when env step durations vary significantly; then drive future actions with the `info.env_id` values returned by `step`.
- Use `RayVectorEnv` for cluster/distributed env execution only when `ray` is installed and configured.
- Use EnvPool directly through its Gymnasium API when installed; Tianshou wrappers such as collectors and `VectorEnvNormObs` can consume EnvPool-like vector envs, but EnvPool is an optional backend rather than a Tianshou constructor.

## Write Robust Env Factories

Prefer top-level factory functions for subprocess-compatible code:

```python
def make_cartpole():
    import gymnasium as gym
    return gym.make("CartPole-v1")

env_fns = [make_cartpole for _ in range(4)]
```

When factories need parameters, bind serializable values with default arguments or `functools.partial`. Avoid open files, sockets, loggers, local classes, lambdas closing over large mutable objects, and objects created in `__main__` when using `spawn`.

## Seed, Reset, Step, and Close

1. Call `envs.seed(seed)` for action-space and env seeding support.
2. Call `obs, infos = envs.reset(seed=seed)` when the env uses Gymnasium reset seeding.
3. Sample or compute a batch of actions with length equal to the selected env ids.
4. Call `obs, rew, terminated, truncated, infos = envs.step(actions, id=ids)`.
5. Compute `done = np.logical_or(terminated, truncated)` and call `envs.reset(done_ids)` for finished envs before continuing.
6. Call `envs.close()` in a `finally` block or context cleanup path.

## PettingZoo and Action Masks

1. Build the PettingZoo AEC env, applying SuperSuit padding if observation or action spaces differ across agents.
2. Wrap with `PettingZooEnv(raw_env)` before passing into Tianshou collectors or vector env factories.
3. Read `obs["agent_id"]` to know whose turn it is and `obs["obs"]` for model input.
4. For discrete legal actions, read `obs["mask"]`; Tianshou converts source `action_mask` values to booleans and supplies all-true masks for unmasked discrete spaces.
5. Keep mask handling near the policy/action-selection layer. Environment code should expose masks; policies and collectors decide how to avoid illegal actions.
6. Route multi-agent training algorithm design to `../offline-and-specialized-rl/SKILL.md` once wrapper behavior is confirmed.

## Optional Environment Engines

- Atari requires optional Atari dependencies and usually ROM handling through ALE/AutoROM-compatible tooling.
- MuJoCo requires the MuJoCo optional dependency and a platform-compatible native runtime.
- VizDoom requires the `vizdoom` optional dependency and game assets/configs; do not assume assets are present.
- Box2D requires Box2D, pygame, swig/build dependencies, and platform-specific wheels or compilers.
- Robotics requires `gymnasium-robotics` and compatible Gymnasium registrations.
- EnvPool requires `envpool` and is unavailable on some platforms.
- Ray is not part of Tianshou's default install; install and initialize it deliberately before `RayVectorEnv` work.

Treat optional engines as explicit user/runtime choices. Keep default validation on Gymnasium classic-control tasks such as `CartPole-v1`.
