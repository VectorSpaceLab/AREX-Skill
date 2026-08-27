# Motion data and retargeting troubleshooting

## Body count mismatch

If conversion reports that motion data has a different number of bodies than kinematic info, verify:

- source skeleton format (`smpl`, `soma`, `smplx`, robot);
- target `robot_type`;
- MJCF body order used during packaging;
- whether a MotionLib from another robot was accidentally reused.

## Contact label mismatch

If contact length does not match motion length:

1. compare source FPS, output FPS, and downsample factor;
2. confirm contact files use the same base filename as retargeted motion files;
3. remove stale partial outputs when changing FPS or skip settings;
4. verify contacts are binary or expected smoothed probabilities before smoothing.

## Retargeting output filtered out

If no `.motion` file appears after conversion, a filter may have rejected it. Inspect min-height, max velocity, max DOF velocity, duration-height threshold, ignored first frames, and whether root/joint units were decoded correctly.

## PyRoki failures

Common causes:

- PyRoki environment missing JAX/CUDA dependencies.
- ProtoMotions environment used to run PyRoki scripts.
- Input keypoint folder has stale/incomplete files.
- Visualization not disabled on a headless server.
- Full AMASS batch too large for the first smoke.

Use a single-motion or high-skip-frequency subset first.

## Git LFS pointers

If example motions, checkpoints, meshes, or USD files behave like small text files, they may be Git LFS pointers. Fetch the real LFS objects before conversion or visualization.

## Full dataset scale

Full AMASS/SEED conversion is expensive. Always confirm:

- enough disk for intermediate keypoints, contacts, retargeted trajectories, and final `.pt`;
- stable output directories for resume/skip-existing;
- small-subset visual quality;
- backend environment for later training.
