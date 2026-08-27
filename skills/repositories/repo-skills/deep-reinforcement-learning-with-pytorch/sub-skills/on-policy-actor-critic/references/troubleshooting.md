# Troubleshooting

## `env.seed` and old Gym API deprecations

**Symptoms**
- `AttributeError` or deprecation warnings around `env.seed(...)`.
- Code that expects `state, reward, done, info = env.step(action)` breaks on a newer Gym or Gymnasium install.

**Likely cause**
- The source scripts were written against old Gym APIs.
- The inspection env verified Gym 0.23.1, which still matches the repo's 4-value step style, but newer installs may not.

**Recovery**
- Keep the classic-control workflows on Gym 0.23.x if you want a near-drop-in match.
- If you must port forward, replace `env.seed(seed)` with `env.reset(seed=seed)` and handle the 5-value step signature (`terminated`, `truncated`).
- For Pendulum, use `Pendulum-v1` in the inspected environment instead of the legacy `Pendulum-v0` name.

## Multiprocessing and `SubprocVecEnv`

**Symptoms**
- Child processes never start, hang at import, or die with `BrokenPipeError`.
- `Can't pickle local object` or similar errors when building env factories.
- The A2C helper works on Linux but fails on a spawn-based platform.

**Likely cause**
- The env factory is a closure or lambda that cannot be pickled.
- The process start method is incompatible with how the env factories are defined.
- The main entry point is missing a `if __name__ == "__main__":` guard in a standalone driver.

**Recovery**
- Keep each env factory as a top-level function or use the bundled `scripts/multiprocessing_env.py` helper.
- Reuse the bundled helper's `CloudpickleWrapper` when you need to serialize env factories.
- Close the vector env explicitly after use; otherwise subprocesses can linger.
- If a platform requires a specific start method, pass it into the bundled helper rather than editing the source script inline.

## Saved policy and checkpoint loading

**Symptoms**
- `FileNotFoundError` for `policyNet.pkl` or a `ModelTraing*.pkl` file.
- `AttributeError: Can't get attribute 'Policy'` or `'Module'` during `torch.load`.
- A file loads, but action selection immediately fails because the object looks like a value network instead of a policy.

**Likely cause**
- The checkpoint path is relative to the current working directory.
- The pickle was created from a script-local class name and the loader does not provide the same class definition.
- The checkpoint is a value head or bare `state_dict`, not a full pickled policy module.

**Recovery**
- Confirm the checkpoint path relative to the current working directory before loading.
- Use the bundled `scripts/playback_saved_policy.py` for full-model pickles from REINFORCE and actor-critic scripts.
- If you saved a `state_dict`, recreate the matching architecture and load weights manually instead of using the playback helper.
- For PPO Pendulum checkpoints, load the actor and critic classes explicitly; they are not full-model pickles.

## PPO buffer and update cadence confusion

**Symptoms**
- The policy appears to collect transitions but never updates.
- PPO logs move in bursts or not at all.
- The clipping ratio is hard to interpret because the source scripts mix action probabilities and log-probabilities.

**Likely cause**
- The source scripts gate updates on different conditions: buffer fullness, episode end, or both.
- `PPO2.py`, `PPO_CartPole_v0.py`, `PPO_MountainCar-v0.py`, and `PPO_pendulum.py` do not share the same cadence.
- The discrete scripts store action probabilities, while the continuous Pendulum script stores true log-probabilities from `Normal.log_prob`.

**Recovery**
- Check `buffer_capacity`, `batch_size`, and `ppo_epoch` or `ppo_update_time` before assuming PPO is broken.
- For `PPO2.py`, confirm the buffer ever reaches the update gate before expecting optimizer steps.
- For `PPO_CartPole_v0.py`, remember that the update is often triggered when the episode ends and the buffer is large enough.
- For `PPO_pendulum.py`, remember that the sampled action is clamped to `[-2, 2]` before the environment step.
- Read `references/workflows.md` for the exact source-script differences before changing the objective.

## TensorBoard, plotting windows, and relative output paths

**Symptoms**
- No TensorBoard data appears.
- `plt.show()` or interactive plotting blocks the session.
- Figures or logs appear under an unexpected directory.

**Likely cause**
- The source uses relative paths such as `../exp`, `./AC_CartPole-v0`, or `./AC_MountainCar-v0`.
- The scripts were written for interactive sessions and assume a display.

**Recovery**
- Check the current working directory before reading or writing logs.
- Disable rendering and plotting in headless sessions, or set a non-interactive Matplotlib backend such as `Agg`.
- Prefer the bundled playback helper when you only need evaluation and not the training plot loop.
- Remember that this sub-skill does not own standalone plotting workflows; those belong elsewhere.

## Legacy environment IDs and compatibility drift

**Symptoms**
- `gym.make('Pendulum-v0')` or other legacy IDs fail after an upgrade.
- A script that used to run on classic-control envs now fails before training starts.

**Likely cause**
- The source repository is pinned to older Gym-style IDs.
- The current environment is newer than the one the scripts expected.

**Recovery**
- For inspection in this project, keep the classic-control tasks on Gym 0.23.1 or use the verified modern substitutes documented in `references/workflows.md`.
- Treat env ID changes as compatibility notes, not algorithm changes.
- Do not reroute a PPO Pendulum issue into the off-policy continuous-control workflows; this sub-skill still owns the on-policy Pendulum variant.
