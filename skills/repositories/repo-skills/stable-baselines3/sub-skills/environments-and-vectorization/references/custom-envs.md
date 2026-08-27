# Custom Gymnasium Environments For SB3

Stable-Baselines3 expects custom environments to inherit from `gymnasium.Env`, expose Gymnasium `spaces` objects, and implement the Gymnasium step/reset API. Validate the env with `stable_baselines3.common.env_checker.check_env` before training.

## Minimal Contract

A custom env should provide:

- `observation_space`: a supported Gymnasium space describing one unbatched observation.
- `action_space`: a supported Gymnasium space describing one unbatched action.
- `reset(self, *, seed=None, options=None) -> (observation, info)`; call `super().reset(seed=seed)` when using Gymnasium RNG helpers.
- `step(self, action) -> (observation, reward, terminated, truncated, info)`.
- `metadata`, `render()`, and `close()` when rendering or external resources are involved.

SB3 still wraps Gymnasium envs into its own VecEnv API during training, but the base env should use Gymnasium's five-value `step()` return and two-value `reset()` return.

## Validation Checklist

Before connecting the env to an algorithm:

1. Instantiate a fresh env instance, not a reused env hidden in a lambda.
2. Run `check_env(env, warn=True, skip_render_check=True)`.
3. Confirm `reset(seed=0)` accepts `seed` and returns `(obs, info)`.
4. Confirm `step(action)` returns exactly five values: `obs, reward, terminated, truncated, info`.
5. Confirm all returned observations are inside `observation_space`: correct dtype, shape, bounds, and dict keys.
6. Confirm rewards are scalar numbers and `terminated`/`truncated` are booleans.
7. Confirm `info` is a dict, and final-step diagnostic values are serializable if Monitor logging will use them.
8. Wrap with `VecCheckNan(DummyVecEnv([lambda: env_factory()]), raise_exception=True)` when debugging NaNs or infinities.

`check_env` raises hard assertions for invalid return signatures, wrong observation shapes/dtypes/bounds, invalid spaces metadata, and non-finite continuous action bounds. With `warn=True`, it also emits SB3-specific compatibility warnings for spaces that Gymnasium may accept but SB3 algorithms cannot use reliably.

## Observation And Action Spaces

Preferred spaces:

- `spaces.Box` with finite bounds for continuous actions; SB3 recommends symmetric normalized continuous actions in `[-1, 1]` and dtype `np.float32`.
- `spaces.Discrete`, `spaces.MultiDiscrete`, and `spaces.MultiBinary` for supported discrete action/observation cases when starts and shapes are compatible.
- `spaces.Dict` for multi-input observations, as long as the dict is one level deep and keys map to supported leaf spaces.

Avoid or wrap before training:

- `Tuple` observations: convert to a one-level `Dict` or flat `Box`.
- Nested `Dict` observations: flatten to one level.
- `Graph`, `Sequence`, and `OneOf` observations: SB3 checker warns and skips deeper return-value checks for some of these spaces.
- `Dict` or `Tuple` action spaces: flatten or map them to a supported array-like action space.
- `Discrete` or `MultiDiscrete` with `start != 0`: shift actions/observations so SB3 sees zero-start spaces.
- `MultiDiscrete` with multidimensional `nvec`: reshape to a one-dimensional `MultiDiscrete` in the exposed space and reshape actions internally.

## Image Observations

For image-like `Box` observations, SB3's checker expects conventions compatible with CNN policies:

- Use `dtype=np.uint8` for raw images.
- Use bounds `[0, 255]`; SB3 CNN preprocessing normalizes raw images by dividing by 255.
- Use channel-first `(C, H, W)` when possible; channel-last can work because SB3 may insert a vectorized transpose wrapper.
- Keep default-CNN images at least `36x36`; smaller image inputs usually need a custom feature extractor.
- If image values are already normalized floats, use policy-level `normalize_images=False` and channel-first images; route custom extractor details to `policies-and-customization`.

For dict observations containing an image and a vector, use `MultiInputPolicy` when training. The env checker validates the dict-space structure; policy internals are handled elsewhere.

## Goal-Conditioned Dict Envs

If an env exposes `compute_reward`, SB3 treats it as goal-conditioned and expects dict observations with at least:

- `observation`
- `achieved_goal`
- `desired_goal`

`check_env` verifies that single-sample and vectorized `compute_reward` outputs are consistent, including a batch shape of `(2,)` for two test goals.

## Wrapping Compatibility Fixes

Use wrappers rather than changing algorithm code when the env has incompatible exposed spaces:

- Shift non-zero-start `Discrete` actions by exposing `spaces.Discrete(n, start=0)` and adding the original start offset inside `step()`.
- Flatten multidimensional `MultiDiscrete.nvec` in the exposed action space and reshape the action back inside `step()`.
- Convert nested dict observations into one-level keys such as `camera`, `state`, and `task_id`.
- Convert tuple observations into dict keys or concatenate compatible vector leaves into a `Box`.

