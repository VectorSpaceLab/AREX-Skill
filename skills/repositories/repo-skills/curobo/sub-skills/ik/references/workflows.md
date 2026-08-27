# IK workflows

## Single target

Use a known reachable target first: create a one-row `Pose`, wrap it with the
actual tool frame, solve with 16–32 seeds, and verify by running FK on
`result.js_solution`. Keep solver and goals on one CUDA device.

## Batched reachability

Set `max_batch_size` to the number of target rows, construct `(B,3)` and `(B,4)`
tensors, and call `solve_pose` once. Report `success.sum()` and error statistics
only over successful rows. For workspace maps, vary the target grid while
keeping robot, seed, tolerance, and scene config fixed.

## Collision-aware IK

Create the solver with `scene_model="collision_table.yml"`,
`self_collision_check=True`, and a cache sized for runtime object types. Call
`update_world(Scene(cuboid=[...]))` to add/move obstacles. Check both IK success
and collision metrics; a low pose error can still be an invalid colliding state.

## Debugging

For a failing target, run eager mode (`use_cuda_graph=False`) with one seed and
`store_debug=True` only for diagnosis. Restore CUDA graphs, seed count, and
batching after identifying the configuration or target issue. Use differential
or Viser modes only in a separately managed interactive process.
