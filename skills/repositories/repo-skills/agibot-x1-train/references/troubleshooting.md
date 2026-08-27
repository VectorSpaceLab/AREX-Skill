# Shared troubleshooting

Read this reference for failures that cross training, playback, export, and
sim2sim routes. Then switch to the nearest sub-skill troubleshooting reference
for workflow-specific recovery.

## Missing Isaac Gym

**Symptoms:** `ModuleNotFoundError: No module named 'isaacgym'`, failure while
importing `humanoid.envs`, or a task registry that never registers
`x1_dh_stand`.

**Cause:** Isaac Gym Preview 4 is a separately distributed legacy dependency;
it is not a normal public pip package. The repository imports it through
`base_task`, `legged_robot`, terrain, helpers, and the X1 task.

**Recovery:** use the documented Python 3.8/PyTorch 1.13.1 + CUDA 11.7
compatibility stack, install a compatible vendor Isaac Gym Preview 4 archive,
verify its own example, then install this package. Do not create an `isaacgym`
stub, silently switch to a modern simulator, or treat a CPU import as proof of
runtime readiness. Until the import and a minimal task construction pass, mark
native CUDA/PhysX cases `BLOCKED_REQUIRED_BACKEND`.

## Version or backend mismatch

**Symptoms:** Torch CUDA is unavailable, PhysX initialization fails, a shared
library cannot load, or a GPU task crashes during construction.

**Recovery:** record Python, Torch, CUDA build, NVIDIA driver, GPU, and Isaac
Gym versions separately. Use one compatible environment rather than mixing a
modern Torch wheel with the legacy Preview 4 bindings. Check `torch.cuda.is_available()`
and a minimal device allocation before constructing the task. A visible GPU
alone is not sufficient.

## Package or asset root failure

**Symptoms:** X1 URDF/MJCF/mesh files are not found, or paths still contain a
literal `{LEGGED_GYM_ROOT_DIR}`.

**Recovery:** install the package from a complete checkout including the X1
resource tree, ensure the package root used by `LEGGED_GYM_ROOT_DIR` is the
actual distribution root, and run the `sim2sim` asset preflight. Do not copy
only Python files while omitting XML includes or meshes.

## Wrong artifact type or run path

**Symptoms:** playback/export expects `model_<N>.pt` but receives `policy_dh.jit`
or ONNX; a latest-run lookup selects an unexpected directory; the output path
uses `log/` instead of `logs/`.

**Recovery:** use the handoff chain in the root router. Training checkpoints
live under `logs/<experiment>/exported_data/<run>/`; JIT artifacts live under
`logs/<experiment>/exported_policies/<timestamp>/`; ONNX artifacts live under
`logs/<experiment>/exported_onnx/<timestamp>/`. Use explicit run names and
checkpoint numbers when reproducibility matters. Validate the artifact with
the export helper before handing it to playback or sim2sim.

## Observation/action contract failure

**Symptoms:** linear-layer shape mismatch, CNN reshape failure, wrong policy
output width, or a sim2sim policy that accepts a different input width.

**Recovery:** stop and compare all dependent fields with the X1 contract:
`num_single_obs=47`, `frame_stack=66`, `short_frame_stack=5`,
`num_observations=3102`, `num_privileged_obs=219`, and `num_actions=12`. Do not
reshape or pad a checkpoint to make it load. Route configuration changes back
to `training`, then regenerate and revalidate downstream artifacts.

## Interactive display or controller failure

**Symptoms:** viewer cannot create a graphics context, pygame finds no device,
controller axes drift, or the robot moves immediately at startup.

**Recovery:** perform static preflight first, use one environment, confirm the
GPU/display and controller, center all axes, and start with small commands.
The README describes a button-4 gate, but the current playback/sim2sim input
threads do not implement it as a software interlock. Treat it as an operator
procedure, not a safety guarantee. Stop on unexpected motion.

## Optional export validation packages

**Symptoms:** JIT checks work but ONNX graph/runtime validation reports `SKIP`.

**Recovery:** distinguish missing optional `onnx` or `onnxruntime` from a bad
artifact. Install a version compatible with the selected legacy Torch stack
only with explicit authorization, then rerun the bundled export preflight.
Never report an optional checker skip as a valid ONNX graph or deployment
result.

## Reproducibility and safety stop conditions

Record task, run, checkpoint/JIT timestamp, source revision, package versions,
GPU/device, and configuration changes. Stop rather than guessing when a
required backend, model artifact, asset tree, observation contract, or viewer
safety precondition is missing. Full training, interactive control, model
loading from untrusted pickle files, and network dependency installation are
not safe smoke checks.
