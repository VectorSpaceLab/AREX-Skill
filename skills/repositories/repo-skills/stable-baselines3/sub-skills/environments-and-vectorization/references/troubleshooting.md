# Environment Troubleshooting

Use this guide when `check_env`, vectorized env construction, or wrapper behavior fails in Stable-Baselines3.

## `reset()` Signature Or Return Errors

Symptoms:

- `TypeError: The reset() method must accept a seed parameter`.
- `check_env` reports that `reset()` did not return a tuple.
- VecEnv `reset()` users expect `(obs, info)` but receive only `obs`.

Fixes:

- Base Gymnasium envs should implement `reset(self, *, seed=None, options=None)` and return `(obs, info)`.
- Call `super().reset(seed=seed)` in custom envs that use Gymnasium RNG behavior.
- SB3 VecEnv `reset()` is different: it returns only `obs`; read reset metadata from `vec_env.reset_infos`.
- For VecEnv seeding/options, call `vec_env.seed(seed)` or `vec_env.set_options(options)` before `vec_env.reset()`.

## `step()` Return Shape Or API Errors

Symptoms:

- `not enough values to unpack` or too many/few step values.
- Confusion between `terminated`, `truncated`, and `done`.
- Training reads the first observation of the next episode as the final observation.

Fixes:

- Base Gymnasium envs must return `obs, reward, terminated, truncated, info`.
- SB3 VecEnv returns `obs, rewards, dones, infos`, where `dones = terminated or truncated`.
- At a VecEnv done, `obs[i]` is already the next episode's first observation.
- Use `infos[i]["terminal_observation"]` for the final observation of the episode that ended.
- Use `infos[i]["TimeLimit.truncated"]` to distinguish timeout-style truncation from true termination.

## Observation Shape, Dtype, Bounds, Or Dict-Key Errors

Symptoms:

- `Expected: (3,), actual shape: (2, 3)`.
- `Expected: float32, actual dtype: float64`.
- `Error while checking key=...` for dict observations.
- Box values outside declared low/high bounds.

Fixes:

- Return a single unbatched observation from a base env, not a vectorized batch.
- Make `observation_space.shape`, dtype, and bounds match every `reset()` and `step()` observation exactly.
- For `spaces.Dict`, return exactly the declared keys, with each leaf matching its own space.
- Keep preprocessing wrappers responsible for batching/stacking; do not bake SB3's leading `n_envs` dimension into the base env.

## Unsupported Spaces

Symptoms:

- Warnings for `Tuple`, nested `Dict`, `Graph`, `Sequence`, or `OneOf` observation spaces.
- Warnings for `Dict`/`Tuple` action spaces.
- Algorithms fail later despite `check_env` only warning.

Fixes:

- Convert tuple observations into a one-level dict or flat Box.
- Flatten nested dict observations to one level.
- Pad variable-length sequence observations into fixed-size Box observations with masks if needed.
- Replace graph observations with fixed-size tensors or route to custom feature extraction only after making the SB3 env interface compatible.
- Flatten dict/tuple actions into supported `Box`, `Discrete`, `MultiDiscrete`, or `MultiBinary` spaces.

## Image Warnings

Symptoms:

- Image dtype warning: expected `np.uint8`.
- Image bounds warning: expected `[0, 255]`.
- Minimum resolution warning for default `CnnPolicy`.
- Channel-order surprises with dict image observations.

Fixes:

- Use `spaces.Box(low=0, high=255, shape=(C, H, W), dtype=np.uint8)` for raw channel-first images when possible.
- Keep H and W at least `36` for default CNN policies.
- For channel-last images, expect SB3 to transpose under vectorized preprocessing when compatible.
- For already-normalized images, use channel-first float images and route policy-level `normalize_images=False` details to `policies-and-customization`.
- For dict image plus vector observations, use `MultiInputPolicy` and validate each dict key separately.

## Non-Zero-Start And Multidimensional Discrete Spaces

Symptoms:

- Warning that `Discrete` or `MultiDiscrete` start is non-zero.
- Warning that multidimensional `MultiDiscrete.nvec` is unsupported.

Fixes:

- Expose zero-start `Discrete`/`MultiDiscrete` spaces to SB3.
- Add the original start offset inside `step()` or unwrap it inside an action wrapper.
- Flatten multidimensional `MultiDiscrete.nvec` in the exposed space, then reshape the incoming action back to the env's internal shape.

## NaNs And Infs

Symptoms:

- `VecCheckNan` reports `found nan` or `found inf` in actions, observations, rewards, or dones.
- Training diverges without a clear env checker assertion.

Fixes:

- Wrap early with `VecCheckNan(venv, raise_exception=True, check_inf=True)` to fail at the first bad value.
- If the message originates from `step_async`, inspect model actions and action scaling.
- If the message originates from `reset` or `step_wait`, inspect env observations, rewards, and terminal transitions.
- Check divisions, square roots, normalization denominators, and invalid physics states inside the env.

## SubprocVecEnv Start-Method Failures

Symptoms:

- Hanging subprocesses, pickling errors, recursive process spawning, or failures on Windows/macOS/notebooks.
- Illegal start method errors.

Fixes:

- Put `SubprocVecEnv` or `make_vec_env(..., vec_env_cls=SubprocVecEnv)` construction under `if __name__ == "__main__":`.
- Use env factory functions/classes defined at importable module scope.
- Avoid closing over file handles, live simulator clients, local classes, or notebook-only objects.
- Use `DummyVecEnv` while debugging env logic, then switch to subprocesses only when env stepping is expensive.
- If passing `start_method`, choose one returned by Python multiprocessing on the target machine.

## Wrapper Ordering Problems

Symptoms:

- Episode info missing from `infos`.
- Normalization applies to an image key that should remain raw.
- A callback cannot mutate a wrapped env attribute.

Fixes:

- Prefer `make_vec_env` so `Monitor` is applied consistently.
- Pass `norm_obs_keys` to `VecNormalize` for dict observations.
- Expose setter methods on the base env and call them through `vec_env.env_method("set_name", value)`.
- Use `get_attr`, `set_attr`, and `env_method` instead of direct access through nested wrappers.

