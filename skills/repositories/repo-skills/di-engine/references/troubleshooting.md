# Troubleshooting

This page collects cross-cutting DI-engine issues that affect more than one
sub-skill.

## Install and import problems

### `ModuleNotFoundError` for `ding`, `dizoo`, `torch`, or `treetensor`
- Reinstall the package in the target environment and re-run `python -m pip check`.
- Make sure you are using the same Python that owns the install, not the shell
  `python` from another environment.
- If you used editable mode, verify that the environment still points at the
  intended checkout.

### `ding --help` or `ditask --help` fails
- The entry points usually are not on `PATH` because the environment is not
  active or the editable install was done in a different prefix.
- Re-run the install checks from the same environment that should own the skill.

### `pip check` reports broken requirements
- Reinstall DI-engine in a clean private prefix.
- Prefer the bundled check script or a fresh editable install over patching the
  base environment.

## Expected warnings

### `Gym has been unmaintained ...`
- This is a known warning from `gym==0.25.1` and does not by itself mean the
  install is broken.
- Use `gymnasium`-based envs when the selected workflow already supports them.

### `Please install pyecharts first ...`
- This warning is harmless unless you specifically need visualization helpers
  that rely on `pyecharts`.

### `If you want to use numba to speed up segment tree ...`
- This is optional performance guidance, not a blocking install failure.

## Config and launch problems

### `main_config` / `create_config` missing
- The config file does not follow the DI-engine experiment pattern.
- Use the sub-skill that owns `ding.config` and make sure both objects are
  declared.

### `platform_spec is not a valid json!`
- `ditask` expects valid JSON in the `--platform-spec` argument or a JSON file.
- Remove shell quoting mistakes and re-run with a minimal payload first.

### `Please indicate at least one argument.`
- `ding` was launched without a mode or without enough configuration to infer
  a predefined environment/policy pair.

## Parallel/runtime problems

### `Parallel.runner` hangs or cannot connect
- Check that all workers use compatible `protocol`, `topology`, `ports`, and
  `node_ids`.
- Make sure the run has a proper `__main__` entry point when the helper is used
  from a standalone script.

### `task.wait_for` timeouts or message routing errors
- The task graph likely emits the wrong event name or the downstream step is
  not registered in the right order.
- Use the framework-runtime sub-skill and its smoke script to isolate the event
  path.

## Environment problems

### Observation or action shape mismatch
- The wrapper or env config does not match the algorithm config.
- Read the env-integration sub-skill and compare the wrapper's shapes against
  the policy model's expected input and action dimensions.

### Missing optional environment packages
- External env families such as Mujoco, PettingZoo, SMAC, D4RL, and similar
  are intentionally outside the default CPU-friendly scope.
- Either install the matching extra or use a representative included env family
  such as CartPole, Pendulum, BitFlip, FrozenLake, or the league demo.
