# Cross-cutting troubleshooting

## Install/import

- `No module named curobo`: install the distribution in the environment whose
  Python will execute the workflow; the distribution is `nvidia-curobo`, not
  `curobo`.
- CUDA or Warp import errors: verify the PyTorch CUDA build, driver/runtime
  compatibility, `warp-lang`, and the selected CUDA extra. A passing CPU import
  does not prove kernel readiness.
- v1 symbols or constructor arguments fail: the checkout is v2; pin the v1
  release instead of translating arguments by guesswork.
- Optional Viser/USD/feature imports fail: keep those branches disabled unless
  the corresponding extra and external data/model are intentionally installed.

## Device and memory

- `torch.cuda.is_available()` false: inspect driver visibility, container GPU
  passthrough, `CUDA_VISIBLE_DEVICES`, and the PyTorch wheel before changing
  cuRobo configs.
- `CUDA out of memory` during a tiny probe: another process may occupy the
  default device. Select a free GPU; then reduce seeds, `max_batch_size`, mapper
  extent, sphere count, or parallel environments.
- Device mismatch: create all `Pose`, `JointState`, scene tensors, and
  `DeviceCfg` values on the solver device; do not mix CPU tensors into CUDA
  goals.
- Graph capture/replay errors after a shape change: reset/rebuild the solver or
  rerun with `use_cuda_graph=False` to isolate the issue, then restore graphs
  for normal runtime.

## Config/data

- YAML not found or wrong robot: use a bundled robot config name/content path and
  confirm its URDF, sphere approximation, tool frame, and joint names agree.
- Shape errors: record batch, goalset, horizon, tool-frame count, DOF, and tensor
  device. cuRobo uses `(B, DOF)` joint positions, `(B, 3)` positions,
  `(B, 4)` wxyz quaternions, and trajectory tensors with an explicit horizon.
- Poor or zero solve success: test a reachable target and a known-valid seed;
  check quaternion normalization/order, tolerances, joint limits, collision
  activation distance, and whether the target tool frame exists.
- Invalid collision scene: give every object a unique name and a 7-value pose;
  match obstacle schema to `Scene`; size collision caches for the object count.

## Solver lifecycle

- After changing world geometry, call the solver's `update_world` path rather
  than mutating an internal scene object. Preserve cache capacity when adding
  objects.
- Inspect result success/error/metrics before consuming a trajectory. Do not
  treat a returned tensor as a valid plan when convergence or collision metrics
  fail.
- For online MPC, update current and goal state in the documented order and
  retain the previous solution as a warm start. Use safe deceleration on an
  unsuccessful solve rather than commanding an unvalidated action.
