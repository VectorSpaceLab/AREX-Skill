# Gymnasium Cross-cutting Troubleshooting

Use this page when the failure spans multiple Gymnasium areas. For deeper workflow-specific guidance, follow the route to the nearest sub-skill troubleshooting file.

## Import or Package Confusion

Symptom: code imports `gym`, examples use old Gym APIs, or `gymnasium` is not found.

Likely causes:
- The environment has OpenAI Gym installed but not Gymnasium.
- Code was written for Gym v0.21 or older.
- The active Python environment differs from the one used for installation.

Fix:
1. Install `gymnasium` in the Python environment that runs the code.
2. Change imports to `import gymnasium as gym`.
3. Update `reset`, `step`, seeding, and render-mode usage with [sub-skills/environment-api/references/migration-and-validation.md](../sub-skills/environment-api/references/migration-and-validation.md).

## Reset and Step API Mismatch

Symptom: `ValueError: too many values to unpack`, code expects `done`, or training logic treats time limits as terminal failures.

Fix:
- Use `obs, info = env.reset(seed=...)`.
- Use `obs, reward, terminated, truncated, info = env.step(action)`.
- End rollout loops with `done = terminated or truncated`.
- Use `terminated`, not `done`, when deciding whether to bootstrap value estimates after a time limit.

## Invalid Environment IDs

Symptom: `NameNotFound`, `VersionNotFound`, namespace errors, or surprising environment versions.

Fix:
1. Inspect `gym.registry`, `gym.spec("Exact-vN")`, or `gym.pprint_registry()`.
2. Use versioned IDs such as `CartPole-v1`, `Taxi-v4`, `LunarLander-v3`, or `Ant-v5`.
3. For custom envs, register with a stable ID and inspect the returned `EnvSpec`; see [sub-skills/environment-api/SKILL.md](../sub-skills/environment-api/SKILL.md).
4. For Atari, plugin, or third-party namespaces, install/register the plugin first; see [sub-skills/builtin-envs/references/troubleshooting.md](../sub-skills/builtin-envs/references/troubleshooting.md).

## Missing Optional Dependencies

Symptom examples:
- `moviepy is not installed, run pip install "gymnasium[other]"`.
- Box2D, MuJoCo, PyGame, ALE, JAX, Torch, or `array_api_compat` import errors.
- Human rendering or video recording fails even though base `gymnasium` imports.

Fix:
- Install the smallest matching extra from [installation-and-extras.md](installation-and-extras.md).
- Use [sub-skills/builtin-envs/references/optional-dependencies.md](../sub-skills/builtin-envs/references/optional-dependencies.md) for built-in families.
- Use [sub-skills/wrappers-recording/references/troubleshooting.md](../sub-skills/wrappers-recording/references/troubleshooting.md) for media, render, and array-conversion wrappers.

## Spaces, Wrappers, and Checkers Disagree

Symptom: `contains` fails, `check_env` warns, a wrapper returns observations outside the declared space, or actions are clipped/transformed unexpectedly.

Fix:
1. Validate raw spaces and samples with [sub-skills/spaces-data/SKILL.md](../sub-skills/spaces-data/SKILL.md).
2. If a wrapper transforms observations or actions, update the wrapper's declared `observation_space` or `action_space` as needed.
3. Re-run a small reset/step smoke before starting training.
4. Use [sub-skills/wrappers-recording/references/troubleshooting.md](../sub-skills/wrappers-recording/references/troubleshooting.md) for wrapper order and changed-space issues.

## Vectorization Mistakes

Symptom: scalar boolean errors, wrong action shape, confusing `infos`, child-process failures, or unexpected post-terminal observations.

Fix:
- Sample from `envs.action_space` for batched actions.
- Treat `rewards`, `terminations`, and `truncations` as arrays.
- Check `envs.metadata["autoreset_mode"]` before interpreting final observations.
- Use top-level factory functions for `AsyncVectorEnv` when closures or lambdas fail to pickle.
- Read [sub-skills/vectorization/references/troubleshooting.md](../sub-skills/vectorization/references/troubleshooting.md).

## Recording and Rendering Failures

Symptom: video files are not produced, `RecordVideo` errors, human windows do not appear, or render frames have unexpected shapes.

Fix:
- Create the environment with `render_mode="rgb_array"` for video recording.
- Install `gymnasium[other]` for `moviepy` when using video helpers.
- Use `render_mode="human"` for live display, not old `env.render(mode="human")` calls.
- Confirm the selected environment family supports the requested render mode.
- Read [sub-skills/wrappers-recording/references/recording-and-rendering.md](../sub-skills/wrappers-recording/references/recording-and-rendering.md).

## Fast Local Sanity Checks

Run root and focused scripts before deeper debugging:

```bash
python scripts/gymnasium_smoke.py
python sub-skills/environment-api/scripts/check_custom_env.py
python sub-skills/spaces-data/scripts/space_contract_smoke.py
python sub-skills/wrappers-recording/scripts/wrapper_smoke.py
python sub-skills/vectorization/scripts/vector_env_smoke.py
python sub-skills/builtin-envs/scripts/action_mask_smoke.py
```

These helpers are intentionally small and do not replace full native repository tests.
