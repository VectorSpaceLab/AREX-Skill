# Repo-Wide Troubleshooting

This page covers failures that cut across several algorithm families. For family-specific issues, use the matching sub-skill's troubleshooting reference first.

## Legacy Gym API and env names

Symptoms:
- `env.seed(...)` warnings or attribute errors.
- `env.step(action)` returning a 5-value tuple instead of the repo's expected 4-value tuple.
- `gym.error.DeprecatedEnv` when a legacy env ID is used.

What to do:
- Keep the repository's classic-control examples on a Gym version that still behaves like the inspected stack, or modernize reset/step handling together.
- Prefer `Pendulum-v1` and `BipedalWalker-v3` when you need to run the modern substitutes in this skill tree.
- Do not assume one env ID can be swapped for another without also updating checkpoint paths and action-space dimensions.

## Missing optional extras

Symptoms:
- `pygame` or Box2D import errors.
- `gym.error.DependencyNotInstalled` or a missing Box2D backend for BipedalWalker.
- Torch or Gym imports work, but a continuous-control script fails when the environment is created.

What to do:
- Install optional extras only when the selected workflow needs them.
- For BipedalWalker, check the root compatibility probe or the off-policy sub-skill helper before launching a long training job.
- Prefer non-rendered checks first.

## Headless plotting and TensorBoard paths

Symptoms:
- `plt.show()` hangs or fails.
- TensorBoard logs appear in an unexpected directory.
- Plotting windows or render calls block a shell session.

What to do:
- Use the bundled root plotting helper for curve aggregation instead of the raw source plotting workflow.
- Keep plotting non-interactive in headless sessions.
- Make the current working directory explicit before diagnosing relative log paths.

## Checkpoint and pickle loading

Symptoms:
- `FileNotFoundError` for `.pth` or `.pkl` files.
- `AttributeError` when loading a pickled policy object.
- A checkpoint loads but the architecture or env dimensions do not match.

What to do:
- Check the algorithm family first, then check the env ID and the current working directory.
- Use the on-policy or off-policy playback helpers when the task is evaluation, not training.
- Recreate the matching model class before loading a bare `state_dict`.

## `np.float` and other NumPy alias removals

Some legacy TD3 and DDPG source loops use deprecated NumPy aliases. If a script fails on newer NumPy, replace deprecated aliases with built-in `float` or explicit NumPy scalar types.

## When to stop and route elsewhere

- If the user only wants curve aggregation, stay at the root plotting helper.
- If the task is clearly about one algorithm family, route to the relevant sub-skill instead of trying to fix everything at the root.
- If the issue is specific to DQN replay logic, actor-critic playback, or Box2D playback, open the family-specific troubleshooting file rather than patching the root guidance.
