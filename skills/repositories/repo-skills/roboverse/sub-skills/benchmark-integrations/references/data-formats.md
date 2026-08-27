# Data and Demo Format Invariants

Before loading or converting any benchmark data, record:

- format/version and source project;
- task and robot identity, simulator/backend, control frequency;
- episode id, ordered timestamps, reset and terminal markers;
- observation keys/shapes/dtypes and image camera names/order;
- action key/shape, units, frame, clipping, gripper convention, and joint order;
- optional reward, success, terminated, and truncated semantics;
- asset references, calibration, licenses, and external download requirements.

A valid tiny fixture should contain at least one non-empty episode, one reset,
one bounded action, consistent observation/action shapes, and an explicit terminal
boundary. Also test an empty episode, missing key, inconsistent dimension,
non-finite value, duplicate/out-of-order timestamp, and unsupported task/robot.

Conversion must preserve identity and make unit/frame changes explicit. Never
repair a wrong joint order or image channel order by guessing. Write a new
output file/directory, do not mutate source data, and emit a version/metadata
record alongside the conversion.

For replay, compare the first observation and action before rendering. A replay
that runs but follows the wrong frame, timestep, or camera is not a valid
benchmark result. For policy evaluation, keep normalization/action unscaling
consistent with the training checkpoint and report whether success is native or
translated into a RoboVerse checker.
