# Evaluation Troubleshooting

Use this page when checkpoint evaluation or rendering fails. For reward-log plotting and GIF composition issues, switch to the [visualization sub-skill](../../visualization/SKILL.md).

## Missing Gym, Roboschool, Box2D, or PyBullet

Symptoms:

- `ModuleNotFoundError: No module named 'gym'`
- `ModuleNotFoundError: No module named 'roboschool'`
- `gym.error.Error: Environment ... doesn't exist`
- Box2D environments fail to import or register.

What to check:

1. The native `test.py` imports both `gym` and `roboschool` at module import time, even if you evaluate a non-Roboschool environment. A safer adapted script should import only the package needed by the selected environment.
2. Roboschool environments such as `RoboschoolWalker2d-v1` are legacy Gym environments. The notebook notes a historical pairing of `roboschool==1.0.7` and `gym==0.15.4`, but compatibility depends on the Python and system environment.
3. Box2D tasks such as `LunarLander-v2` and `BipedalWalker-v2` need a Box2D-capable install, for example a compatible `gym[box2d]`, `box2d-py`, or `Box2D` setup.
4. The notebook also shows `pybullet` / `pybullet_envs` as an optional dependency variant, but the shipped pretrained path names in this repository are Gym/Roboschool/Box2D names.

If the current environment lacks these optional packages, you can still use `scripts/evaluation_config_helper.py` for checkpoint-path and config validation. Do not claim a full rollout was verified until the chosen environment can be created.

## Checkpoint path not found

Symptoms:

- `FileNotFoundError` from `torch.load`.
- The helper reports `checkpoint_exists: false`.

Fixes:

1. Confirm the root directory is the directory containing environment subfolders, usually `PPO_preTrained`.
2. Confirm the path format: `PPO_preTrained/<env_name>/PPO_<env_name>_<random_seed>_<run_num>.pth`.
3. Check environment-name case and spelling. The same string should appear in `gym.make`, the folder name, and the checkpoint filename.
4. If using a custom checkpoint, pass `--checkpoint-path` directly rather than trying to force it into the built-in layout.

## Checkpoint/environment mismatch

Symptoms:

- `RuntimeError` with `size mismatch` while loading the state dict.
- The actor or critic layer shapes do not match.
- A discrete task was configured as continuous or vice versa.

Likely causes:

- The checkpoint filename names one environment but `gym.make` creates another.
- `has_continuous_action_space` is wrong for the environment.
- The live environment version changed observation or action dimensions.
- The model architecture was edited after the checkpoint was saved.

Use the helper with a trusted checkpoint and `--inspect-checkpoint` to infer the state/action widths saved in the actor and critic weights, then compare them with the live environment spaces before constructing `PPO`.

## Continuous `action_std` problems

Symptoms:

- Continuous-policy construction fails because `action_std` is `None`.
- Loading succeeds but reward is much worse than expected.
- The action distribution is too noisy or too deterministic.

Facts:

- Continuous `action_std` is a constructor/runtime value in this implementation, not a trained parameter in the saved checkpoint.
- The pretrained continuous runs in this repository decayed from `0.6` to `0.1`; the native test and GIF scripts use `action_std=0.1` for continuous pretrained policies.
- Discrete policies should use `action_std=None` and should not call `set_action_std`.

Fix: set `action_std=0.1` for the shipped continuous pretrained checkpoints unless you know the checkpoint came from a different training schedule.

## Headless or display-free rendering

Symptoms:

- Numeric evaluation works, but `env.render()` fails.
- Errors mention `DISPLAY`, OpenGL, GLFW, X server, or unsupported render mode.
- Notebook/remote sessions show blank windows or no frames.

Fixes:

1. Disable rendering for reward-only evaluation.
2. For local interactive rendering, ensure a display is available and use the render call supported by your Gym version.
3. For newer Gym/Gymnasium, create the environment with an explicit render mode such as `render_mode="human"` or `render_mode="rgb_array"` if the environment supports it.
4. For remote or notebook frame capture, the notebook used `xvfb`, `python-opengl`, and `pyvirtualdisplay`. Keep that setup outside the default evaluation helper and use visualization workflows for frame/GIF outputs.

## Old Gym API vs newer Gymnasium API

The native script assumes old Gym returns:

```python
state = env.reset()
state, reward, done, info = env.step(action)
```

Newer Gym/Gymnasium commonly returns:

```python
state, info = env.reset()
state, reward, terminated, truncated, info = env.step(action)
done = terminated or truncated
```

If a rollout fails with unpacking errors or passes a tuple into `select_action`, adapt reset/step handling as shown in [evaluation-workflow.md](evaluation-workflow.md).

## PyTorch load compatibility and safety

- This repo's `PPO.load` uses `torch.load` with `map_location`, which allows CPU-side loading of tensors saved on another device.
- Recent PyTorch versions may warn about pickle safety or `weights_only` defaults. Treat `.pth` files as trusted code/data unless your loader explicitly restricts pickle behavior.
- If a CUDA-related load error appears, load on CPU first and then construct/move the PPO policy consistently with the root PPO module's device behavior.

## Do not misclassify these as evaluation failures

- Plot PNG or GIF generation problems: use visualization.
- Long training reward instability: use training.
- Missing optional environment packages in a documentation/helper-only smoke check: record as an optional runtime limitation, not as a sub-skill drafting failure.
