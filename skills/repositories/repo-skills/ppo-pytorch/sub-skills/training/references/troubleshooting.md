# Training Troubleshooting

Use this page when the training route cannot even be configured cleanly or when a long run starts from the wrong environment or output layout.

## Missing Gym, Roboschool, or Box2D

**Symptoms**

- `ModuleNotFoundError: No module named 'gym'`
- `ModuleNotFoundError: No module named 'roboschool'`
- Box2D environments fail to register or step

**Likely cause**

The native training loop imports `gym` and `roboschool` directly. Box2D environments such as `CartPole-v1` do not need Box2D, but `LunarLander-v2` and `BipedalWalker-v2` do.

**Next step**

Use the helper to confirm the preset first, then install the missing environment family before starting the long run.

## Wrong environment name

**Symptoms**

- `gym.make` cannot find the environment.
- The output directories are created for the wrong preset.

**Likely cause**

The environment string must match the repo's naming exactly.

**Next step**

Use `training_config_helper.py --list-presets` and choose a preset that exists in the repository's README and pretrained notes.

## Action-space mismatch

**Symptoms**

- Discrete tasks are configured with `action_std`.
- Continuous tasks fail because `action_std` is missing or `None`.
- `set_action_std` is called on a discrete policy.

**Likely cause**

The `has_continuous_action_space` flag does not match the environment.

**Next step**

Check the preset table and the action-space class before constructing the PPO agent.

## Output directory or file problems

**Symptoms**

- Log files are overwritten unexpectedly.
- Checkpoints are saved to the wrong folder.
- The code cannot create `PPO_logs/...` or `PPO_preTrained/...`.

**Likely cause**

The output root or run number is wrong, or the process lacks write permission.

**Next step**

Use the helper with `--create-dirs` and verify the resolved log and checkpoint filenames before launching the long run.

## Old Gym API vs newer Gymnasium API

**Symptoms**

- Unpacking errors around `reset()` or `step()`
- `done` handling no longer matches the environment's return values

**Next step**

Adapt the environment wrapper to the older/newer API boundary before you let a long training run proceed.

## Long run expectations

Training is intentionally expensive. If the configuration is correct but the run is simply long, that is not a failure of the helper. Do not treat a safe config-only check as proof that a long training run has completed.
