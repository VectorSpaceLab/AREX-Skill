# Camera-to-UR5 calibration

The historical source artifact `calibrate.py` estimates a rigid
camera/world relationship with a checkerboard attached to the tool and a
scalar depth correction. This reference preserves its math and file contract;
the runtime graph cannot execute that calibration motion.

## Non-runnable boundary and preconditions

**Never invoke `calibrate.py` from the original checkout for verification.**
Require all of the following before an operator considers a calibration run:

1. An operator-supplied, separately reviewed calibration application under
   `<CALIBRATION_APP_ROOT>` and a separately reviewed writable output directory
   `<CALIBRATION_OUTPUT_DIR>`. Never use or require the original checkout's
   `real/` directory.
2. The parent skill's physical safety boundary: supervised controller mode,
   confirmed `<operator-approved-controller-host>`, command port `30002`,
   real-time port `30003`, tool attachment, emergency stop, collision review,
   and abort plan.
3. A started external RealSense streamer and a full frame from the bundled
   motion-free helper. Confirm sharp RGB, a visible checkerboard, and nonzero
   depth at the board.
4. The checkerboard midpoint offset from the tool center in robot coordinates.
   The source example is `[0, -0.13, 0.02]` metres and is not universal. Confirm
   the actual fixed tool orientation; the source example is `[-pi/2, 0, 0]`.
5. A reviewed calibration workspace distinct from the main runtime workspace:
   `x=[0.3,0.748]`, `y=[0.05,0.4]`, `z=[-0.2,-0.1]` metres, with source
   `calib_grid_step=0.05` m. Change it only after reachability and collision
   review. Back up prior files in the operator output directory.

The bundled camera helper is the only directly runnable camera check:

```shell
python <skill-root>/sub-skills/real-robot/scripts/capture_rgbd.py \
  --host <CAMERA_HOST> --port 50000 --timeout 5
```

## Historical procedure, as evidence

The source procedure constructs points from the calibration grid, closes and
homes the robot, moves the tool, waits, and detects a `(3,3)` internal-corner
pattern with OpenCV. The README describes a 4x4 board while the implementation
uses three by three inner corners; configure the separately reviewed
application and physical board consistently.

For each successful detection, the center corner is back-projected with color
intrinsics and current depth, adjusted by `checkerboard_offset_from_tool`, and
used in an SVD rigid fit while one Z/depth scale is optimized with Nelder-Mead.
The stored camera pose is the inverse of the fitted world-to-camera transform.
These are source-derived facts, not instructions to run the source file.

Inspect detection count and spatial spread, checkerboard overlays, fitted
residual/RMSE, and proper rigid-pose checks. Recollect if points are clustered,
depth is zero/noisy, the board slips, or residual is large. A scalar Z fit
cannot repair wrong intrinsics, offset, moving-camera data, mirrored frames, or
general affine distortion.

## Output contract and units

The separately reviewed calibration application must save these files under
`<CALIBRATION_OUTPUT_DIR>`:

- `camera_pose.txt`: a 4x4 homogeneous camera-to-robot pose with rotation and
  translation in metres. The downstream geometry path uses this direction;
  validate the final row, finite values, orthonormal rotation, and determinant
  near +1.
- `camera_depth_scale.txt`: one finite positive dimensionless scalar. Raw
  `uint16` depth is first multiplied by the RealSense wire scale to obtain
  metres, then this scalar is applied once by the runtime application. It is
  not a millimetres-to-metres conversion.

The historical source uses space-delimited `np.savetxt`. Preserve exact shapes
and delimiter semantics. Do not replace a 4x4 pose with 3x4, put millimetres in
translation, or apply the scalar twice. Hand transform math to
[perception-geometry](../../perception-geometry/SKILL.md).

## Controlled post-calibration sequence

Archive prior outputs, validate the new pair offline, run one motion-free frame
probe, and compare a transformed checkerboard point against a measured tool
position. Only after separate operator approval should a reviewed application
perform one low-speed touch test. Keep the gripper open, use a conservative
point away from edges, and stop on any mismatch. Do not proceed directly to an
unattended policy loop.
