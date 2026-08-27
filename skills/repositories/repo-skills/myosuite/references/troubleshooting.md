# MyoSuite cross-cutting troubleshooting

## Import versus runtime asset failures

If `import myosuite` fails, first check the base dependency boundary: a
Gymnasium/legacy-Gym provider must be importable and MuJoCo must be compatible
with the package. If import succeeds but `gym.make(...)` raises an XML include
or asset-file error, the package is present but model data is incomplete. Repair
the explicit source asset setup or use a complete release package; do not
reinterpret the error as an unknown task ID.

## Registry and task selection

Registration occurs when `myosuite` imports. Query the registered IDs after that
side effect, use `gym.spec` before `gym.make`, and use the exact task/version
suffix. Fixed/random names and `Sarc`, `Fati`, and `Reaf` variants are not
interchangeable. A valid registry key proves only registration; `gym.make` plus
`reset` proves that the model can load in the current install.

## API-version mismatch

The verified base path uses Gymnasium 1.2.x: `reset(seed=...)` returns
`(observation, info)`, while `step(action)` returns
`(observation, reward, terminated, truncated, info)`. Code written for an old
Gym return signature may fail or discard truncation. Inspect the installed
provider and keep compatibility branches explicit.

## Rendering and headless execution

Use `render none` for automated checks. Window errors, EGL/GLFW failures,
macOS `mjpython` requirements, camera names, and offscreen frame output belong
to `simulation-rendering`; they do not invalidate a base reset/step result.
Avoid opening a viewer in a headless session and bound frame/output counts.

## Optional dependencies and backends

Treat MJX/JAX/CUDA, Stable-Baselines3, MJRL, DEP-RL, TorchRL, Mink, visual
encoders, and tutorial packages as selected extras. If an optional import fails,
run the relevant dependency probe, install the documented extra in a separate
compatible environment, or fall back to the CPU route when the requested
behavior permits it. Do not claim CUDA/MJX support from a CPU import, and do not
silently run long training as a dependency check.

## Data, config, and policy boundaries

For reference motions, validate `time`, array rank, dimensions, frame order, and
robot/object joint order before connecting data to an environment. For training,
validate config and checkpoint paths without deserializing untrusted artifacts;
make sure the policy's observation/action spaces match the target task. Use the
bundled safe helpers for bounded diagnostics and keep generated files in an
explicit user-selected output directory.

## Reproducibility and cleanup

Seed both `reset` and the action space when comparing sampled rollouts. Copy
arrays taken from `info` before storing them. Always close environments and
remove only temporary files created by a bounded helper. Do not use package
asset setup/cleanup commands implicitly because they can download or mutate
model data.
