# Reference-motion workflows

## Build a deterministic synthetic motion

Use a tiny in-memory mapping when checking code paths or debugging shape
contracts. A tracked reference uses equal-length time and trajectory rows:

```python
import numpy as np
from myosuite.logger.reference_motion import ReferenceMotion

motion = ReferenceMotion({
    "time": np.array([0.0, 1.0, 2.0]),
    "robot": np.array([[0.0], [1.0], [2.0]]),
    "robot_vel": np.ones((3, 1)),
    "object": np.zeros((3, 7)),
})
assert motion.type.name == "TRACK"
assert motion.find_timeslot_in_reference(1.0) == (1, 1)
mid = motion.get_reference(1.5)
assert np.allclose(mid.robot, [1.5])
motion.reset()
```

For a fixed target use one robot/object row. For a randomized target use two
rows interpreted as low/high limits; provide a seeded NumPy generator when
repeatability matters. Missing init fields are deliberate and are inferred by
the implementation, but explicit init arrays are safer when the starting pose
differs from frame zero.

## Attach to playback

The repository's `examine_reference` Click command accepts an environment name,
`--horizon`, `--num_playback`, and `--render [onscreen|none]`. Use trusted task
IDs and a small playback count. Start with `--render none` to verify that the
reference loads and the environment can consume it; route actual video/window
work to `simulation-rendering`. If the command needs a source motion file,
validate it as an `.npz`/pickle data contract before launching playback.

Reference motions are also used by MyoDM tasks. Keep their robot/object joint
order aligned with the target environment's `qpos` and object coordinates; a
shape-valid file can still be semantically wrong if joint ordering differs.

## Interpolation and replay

Call `reset()` when beginning a second pass because tracked lookup uses an
index cache optimized for forward time. Query exact stored timestamps when
possible. Between two frames, `get_reference` performs a linear blend. Before
asking for a later time, choose one explicit policy: reject beyond-horizon
queries (default) or enable final-frame hold with `motion_extrapolation=True`.
Record that policy in experiment configuration rather than silently changing
it.
