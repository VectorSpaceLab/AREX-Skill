# Conversion and data utility surfaces

## Keypoint extraction

Keypoint extraction reads a packaged MotionLib and emits NumPy dictionaries with positions, orientations, and contact labels. Evidence-backed options include skeleton format (`smpl` or `soma`), output path, start/end indices, skip frequency, and force-remake.

Use it when the source is a packaged SMPL/SOMA MotionLib and PyRoki needs simplified trajectory keypoints.

## Robot trajectory conversion

Robot conversion utilities read retargeted `.npz` or CSV trajectories with root position, root orientation, joint angles, FPS, and optional contact labels. They build ProtoMotions `.motion` files and can apply motion-quality filters.

Important conventions:

- Some G1 CSVs use centimetres and Euler degrees with a frame column.
- Generator-native CSVs may use metres, `wxyz` quaternions, and radians.
- Generic retargeted `.npz` expects `base_frame_pos`, `base_frame_wxyz`, and `joint_angles`.

## Contact utilities

Source-contact extraction and contact recomputation utilities exist because contact quality affects mimic rewards. Prefer source contacts when retargeting from SMPL to robot. Recompute contacts only when source contacts are unavailable and thresholds have been validated.

## Motion filters

Motion filters can exclude motions with low root height, excessive Cartesian velocity, excessive DOF velocity, or duration-based height problems. If conversion silently yields few outputs, check filter logs and thresholds.

## Packaging utility

`MotionLib` can save a directory or YAML/list of `.motion` files into a packaged `.pt`. Use a CPU device unless packaging is large enough to benefit from GPU and the environment is verified.

## Utilities bundled with this skill

- `scripts/summarize_motion_lib.py` gives field/shape summaries.
- `scripts/subset_motion_lib.py` samples every Nth motion to make a smaller MotionLib for debugging or memory limits.

These scripts do not replace the full repository conversion scripts; they cover the safe, self-contained inspection and subsetting tasks future agents frequently need.
