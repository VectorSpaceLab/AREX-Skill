# Troubleshooting

Use this file for cross-cutting issues that affect more than one route. For route-specific fixes, read the nearest sub-skill troubleshooting page.

## `ModuleNotFoundError: gym` or `roboschool`

**Symptoms**

- `train.py`, `test.py`, or `make_gif.py` fail during import.
- The helper reports that a pretrained preset is available but the environment package is missing.

**Likely cause**

The native scripts import `gym` and `roboschool` at module import time. Legacy Roboschool presets also need the Roboschool package or a compatible replacement path.

**Next step**

- Install the route-specific environment package.
- If you only need plotting or checkpoint-path checks, stay on the visualization or evaluation helper path that avoids a rollout.

## Checkpoint load mismatch

**Symptoms**

- `RuntimeError: size mismatch`
- `FileNotFoundError` during `torch.load`
- A checkpoint loads but performs badly immediately

**Likely cause**

The checkpoint, environment name, action-space class, or `action_std` does not match the saved model.

**Next step**

- Confirm the environment name in the checkpoint path.
- Confirm whether the policy is discrete or continuous.
- For continuous policies, use the saved-run `action_std` assumption from the evaluation reference.

## Gym API drift

**Symptoms**

- `ValueError` while unpacking `reset()` or `step()` results.
- A tuple is passed into `select_action`.

**Likely cause**

The native scripts use the older Gym return style, while newer Gymnasium environments often return `(obs, info)` from `reset()` and `(obs, reward, terminated, truncated, info)` from `step()`.

**Next step**

Use the adaptation pattern in the evaluation reference when you need to port the scripts to newer APIs.

## Rendering fails in a headless session

**Symptoms**

- `DISPLAY` / OpenGL / GLFW errors
- Blank windows or no frames
- `env.render()` fails but reward-only evaluation works

**Likely cause**

The process has no usable display or render mode.

**Next step**

- Disable rendering for reward-only checks.
- Use visualization for GIF composition from already saved frames.
- Only add a headless display stack when the route truly needs frame capture.

## Plotting or GIF creation fails

**Symptoms**

- Missing `pandas`, `matplotlib`, or `Pillow`
- Plotting scripts cannot find CSV logs or frame images
- GIF composition reads no frames

**Next step**

Read the visualization sub-skill troubleshooting page and verify the expected output layout first.

## When to stop

Stop and narrow the scope if the task needs a backend or legacy dependency that is not available yet. Do not treat a partial CPU-only smoke check as proof that a rollout-heavy workflow is ready.
