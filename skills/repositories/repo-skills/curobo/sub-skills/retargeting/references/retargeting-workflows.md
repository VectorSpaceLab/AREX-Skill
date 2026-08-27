# Retargeting workflows

## Frame solving

Define criteria for one or more tool frames, construct the retargeter on CUDA,
then solve a single frame from the default or measured joint state. Validate
all requested frame poses with FK and check that locked joints remain fixed.

## Sequence solving

Normalize source motion into the target frame convention and wxyz quaternion
format. Preserve sequence order, environment/batch dimensions, and target
frame ordering. Solve a short prefix first; inspect per-frame success, joint
velocity/acceleration, and collision clearance before full playback.

## Humanoid/high-DoF

Use the bundled high-DoF robot configuration as a schema reference, not as a
promise that every source motion is compatible. Set control points, seeds,
steps, and environment count to fit GPU memory. External retargeter packages,
large motion datasets, and Viser playback are optional application layers.
