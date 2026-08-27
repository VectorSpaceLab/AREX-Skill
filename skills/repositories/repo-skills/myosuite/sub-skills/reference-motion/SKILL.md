---
name: "reference-motion"
description: "Load, classify, interpolate, validate, and safely inspect MyoSuite
  fixed, randomized, and tracked reference motions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MyoSuite reference motion

Use this route when a task involves reference trajectories, motion playback,
fixed/random/track targets, interpolation, initialization states, reference
logs, or `examine_reference` diagnostics.

## Route the request

- Core task IDs, reset/step, and action/observation contracts: `environments`.
- Window/offscreen rendering and MuJoCo camera behavior: `simulation-rendering`.
- JAX parity or accelerated MJX reference handling: `mjx-acceleration`.
- Long-running policy training or learner configuration: `training-integration`.

Read [the API reference](references/api-reference.md) for the data contract,
[workflows](references/workflows.md) for bounded recipes, and
[troubleshooting](references/troubleshooting.md) before diagnosing malformed
files or out-of-range times. The bundled
`scripts/reference_motion_smoke.py` is a safe in-memory check and does not need
original repository data.

## Fast path

1. Choose NumPy `ReferenceMotion` for a normal CPU environment.
2. Supply either a dict or a `.npz`/`.pkl`/`.pickle` path containing `time` and
   the relevant `robot`, `robot_vel`, and `object` arrays.
3. Let the class infer `FIXED` (one frame), `RANDOM` (two low/high frames), or
   `TRACK` (more than two frames).
4. Call `get_init()`, then `get_reference(time)` at bounded times; call `reset()`
   before replaying a trajectory from its beginning.
5. Use `--render none` for CLI playback in headless verification. Rendering is a
   separate route, not a prerequisite for checking interpolation.

```python
import numpy as np
from myosuite.logger.reference_motion import ReferenceMotion

reference = {
    "time": np.array([0.0, 1.0, 2.0]),
    "robot": np.zeros((3, 2)),
    "robot_vel": np.zeros((3, 2)),
    "object": np.zeros((3, 7)),
}
motion = ReferenceMotion(reference)
robot_init, object_init = motion.get_init()
frame = motion.get_reference(0.5)  # linearly interpolated TRACK frame
```

Validate dimensions and time bounds before coupling a motion to a task. Keep
reference arrays and returned structures copied when storing them beyond one
simulation step.

## Verification boundary

Core NumPy reference handling and bounded synthetic fixed/random/track behavior
are suitable for CPU verification. JAX parity, large `.npz` corpora, and full
playback remain optional or data-dependent; never claim they pass from a CPU
import alone. The source-native candidate is the reference-motion test family,
run only when its data and optional dependencies are available.
