# Kinematics workflows

These procedures separate editable specs, compiled models, simulation data, and
optional task-level IK. They are designed for CPU MuJoCo and NumPy. Rendering,
viewer control, and environment reset/step belong to other sub-skills.

## 1. Inspect, edit, compile, and validate

1. Resolve the source XML and copy its identity for logging. Do not overwrite
   it. Decide which named bodies, geoms, sites, meshes, joints, or actuators
   must remain.
2. Construct `editor = ModelEditor(source_xml)`. A missing path should fail at
   construction with a `ValueError` containing the underlying file error.
3. Define an edit function with a narrow contract:

   ```python
   def edit_fn(spec):
       body = spec.body("segment")
       if body is None:
           raise ValueError("required body segment is missing")
       child = body.first_body()
       if child is None:
           raise ValueError("segment has no editable child")
       saved = (child.name, child.pos.copy())
       spec.delete(child)
       body.add_body(name=saved[0], pos=saved[1])
   ```

   In a digit simplification, first walk each root's child chain and snapshot
   each child name, position, and mesh geom names. Delete the old chain, then
   rebuild one body per saved entry, add mesh geoms by their original mesh
   names, and restore required tip/target sites. Verify every required lookup
   before compile; do not silently skip a missing digit.
4. Call `editor.edit_model(edit_fn)`, then `artifact = None` and use a
   `try/finally` block. Call `create_edited_xml()` inside the `try`, compile the
   returned artifact with `mujoco.MjModel.from_xml_path`, and inspect names and
   structural relationships. In `finally`, remove the artifact if it exists.
5. If a compile or serialization error is expected during a test, force it and
   assert that the artifact is absent afterward. If failure occurs before the
   editor returns a path, clean any caller-tracked partial path and retain the
   exception. Never call cleanup against the original source path.

The compile gate is important: a spec can contain an apparently valid edit
while the final XML has invalid mesh references, duplicate names, invalid
attributes, or a broken parent chain. For a compiled model, use MuJoCo name
lookups and inspect `body.parentid`, geom `bodyid`, site type/size/position, and
mesh existence as appropriate.

## 2. Apply a model to a robot boundary

When a task only needs kinematics, use the compiled model/data directly. If a
MyoSuite robot object is required, pass the compiled `mj_model` to `Robot` so
it creates data from the edited model. Forward the data before reading
`site_xpos` or `site_xmat`. Keep model editing separate from hardware
initialization and from environment lifecycle.

An environment that accepts `edit_fn` can apply the function while obtaining
its `MjSpec`, compile it, and then construct its simulation objects. That is
convenient for an environment variant, but it does not change the cleanup rule
for callers that explicitly create XML artifacts.

## 3. Validate an IK request

Use a boundary validator before entering the solver:

```python
import numpy as np

def validate_target(target_pos=None, target_quat=None):
    if target_pos is None and target_quat is None:
        raise ValueError("provide target_pos or target_quat")
    if target_pos is not None:
        p = np.asarray(target_pos, dtype=float)
        if p.shape != (3,) or not np.all(np.isfinite(p)):
            raise ValueError("target_pos must be finite with shape (3,)")
    if target_quat is not None:
        q = np.asarray(target_quat, dtype=float)
        if q.shape != (4,) or not np.all(np.isfinite(q)):
            raise ValueError("target_quat must be finite with shape (4,)")
        if np.linalg.norm(q) == 0:
            raise ValueError("target_quat must be nonzero")
```

Normalize a quaternion only if the caller's contract permits normalization;
otherwise reject a non-unit target and report the convention. The base helper
uses `(w, x, y, z)`. Confirm that `site_name` exists and that the initial data
has been forwarded. Select `joint_names` only when the task owns the named
joints; a tuple is accepted and converted to a list by the implementation.

## 4. Run and interpret site-pose IK

Call the solver with a bounded budget:

```python
result = qpos_from_site_pose(
    physics,
    site_name="end_effector",
    target_pos=target_pos,
    target_quat=target_quat,
    joint_names=None,
    max_steps=200,
    inplace=False,
)
if not result.success:
    raise RuntimeError(
        f"IK did not converge: err={result.err_norm:g}, steps={result.steps}"
    )
qpos = np.asarray(result.qpos).copy()
```

Position-only, orientation-only, and combined targets select different Jacobian
rows. `rot_weight` changes only the relative residual contribution; it cannot
make an unreachable position reachable. `regularization_strength` is useful
near singular or poorly conditioned configurations. `max_update_norm` keeps a
single update bounded. `progress_thresh` protects against a stalled local
minimum. `max_steps` is a hard stop, not a guarantee of convergence.

With `inplace=False`, compare or apply the returned copy explicitly; the
original physics state is restored. With `inplace=True`, call forward after
any external changes and treat the data as changed even when the solve fails.
After success, verify the achieved site pose against the target with explicit
position and quaternion/rotation tolerances, then apply joint-limit and model
policy checks before using the qpos.

## 5. Optional task-level tutorial pattern

A higher-level IK loop can use a mocap target, a frame task, a posture task,
a velocity solver, and repeated configuration integration. This pattern needs
an optional IK package and is useful for interactive task control, but it is
not the same API as `qpos_from_site_pose`. Use it only when that package is
installed and a viewer is explicitly requested. A non-rendering smoke should
use the bundled script instead.

## 6. Quaternion/vector/tensor composition

For a relative orientation, use `diffQuat(current, target)` according to the
helper's argument order, then `quat2Vel` or `quatDiff2Vel` with a positive
`dt`. For a vector in a rotated frame, choose `rotVecMat` versus
`rotVecMatT` deliberately; the latter multiplies by the matrix transpose.
For batch tensor data, flatten only at the optimizer boundary and retain the
original shapes for `unflatten_tensors`. Do not use tensor padding or
concatenation as a substitute for validating a target pose.

## 7. Required proof matrix

A later verifier should run at least:

| Case | Expected observation |
|---|---|
| Edit a generated model and compile | Required replacement names exist; source is unchanged. |
| Force compile/write failure | No temporary XML remains. |
| Valid reachable IK target | `success` is true and achieved residual is within policy. |
| Unreachable target | Bounded failure is surfaced with residual and step count. |
| Missing target or malformed dimensions | Validation raises before solver mutation. |
| Invalid model path | Construction raises a value error with the underlying reason. |
