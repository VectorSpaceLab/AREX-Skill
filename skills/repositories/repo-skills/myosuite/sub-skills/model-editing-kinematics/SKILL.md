---
name: "model-editing-kinematics"
description: "Transform MuJoCo model specs safely and solve site-pose inverse
  kinematics with MyoSuite's CPU APIs, while preserving robot/model contracts
  and cleaning temporary artifacts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Model editing and kinematics

Use this sub-skill when a task changes a MuJoCo model before compilation,
needs a site pose converted to joint coordinates, or needs quaternion/vector
utility semantics. It is an operating guide, not an environment lifecycle,
renderer, reference-motion, or MJX-parity guide.

## Route the request

1. Identify the input model, the intended edit, the compile target, and the
   expected cleanup behavior before touching the model.
2. For a one-off XML edit, use `ModelEditor(model_path)` and keep the edit in a
   callable `edit_fn(spec) -> None`. For a reusable pure XML transformation,
   use the XML helpers described in [API reference](references/api-reference.md).
3. For inverse kinematics, name the target site and state whether position,
   orientation, or both are constrained. Validate target shapes before calling
   the solver.
4. Prefer a bounded, non-rendering CPU smoke test. Use
   [`scripts/ik_smoke.py`](scripts/ik_smoke.py) when a minimal proof is enough.

## Core contracts

### Model editing

- `ModelEditor` loads a file into `mujoco.MjSpec`; it does not return a
  compiled model from `edit_model`.
- `edit_model(edit_fn=None)` mutates the in-memory spec. `None` is a deliberate
  no-op and should preserve the serialized spec.
- An edit function should inspect names and properties before deleting,
  preserve required poses/mesh names, add replacement bodies/geoms/sites, and
  leave compilation to the caller.
- `create_edited_xml()` compiles the spec, serializes it, writes a timestamped
  XML artifact, and returns its path. Compile or write failures happen before a
  usable artifact is guaranteed.
- Always use `try/finally`: delete the returned artifact only when it exists,
  and also clean a partially created path on write/compile failure when the
  caller owns that path. Never delete the source model.

### Kinematics

- `qpos_from_site_pose(physics, site_name, target_pos=None,
  target_quat=None, ...)` returns `IKResult(qpos, err_norm, steps, success)`.
- Supply at least one target. Position is shape `(3,)`, orientation is shape
  `(4,)` in MuJoCo `(w, x, y, z)` order; reject malformed or non-finite values.
- `joint_names` is `None`, a list, tuple, or NumPy array. Use it to limit
  degrees of freedom; do not assume joint IDs equal DOF indices.
- Treat `success` as the gate, not a small-looking `qpos` change. Inspect
  `err_norm` and `steps`; a failure is diagnostic data, not a valid pose.
- Use `inplace=False` by default so the caller's state is restored. Use
  `inplace=True` only when the caller explicitly wants the data mutated.

## Solver controls

Start with defaults and lower the scope before increasing iterations. The
important controls are `tol`, `rot_weight`, `regularization_threshold`,
`regularization_strength`, `max_update_norm`, `progress_thresh`, and
`max_steps`. Regularization is active while the weighted residual exceeds its
threshold; the update is capped by `max_update_norm`; the progress heuristic
can stop a stalled local solve early. The implementation does not enforce
joint limits, so validate or clamp the resulting configuration against the
model's policy before applying it.

For a failed solve, record the site name, target shapes, selected joints,
initial state policy, `err_norm`, `steps`, and whether the target is reachable.
Retry only with a justified initial state, joint subset, damping/regularization,
or iteration bound. Do not silently convert an unreachable target into a
success.

## Utility routing

- Quaternion composition/difference: `mulQuat`, `negQuat`, `diffQuat`,
  `quatDiff2Vel`, `quat2Vel`.
- Representations: `euler2mat`, `mat2euler`, `euler2quat`, `quat2mat`,
  `mat2quat`, `quat2euler`, and the intrinsic Euler pair.
- Vector rotation: `rotVecMat`, `rotVecMatT`, `rotVecQuat`.
- Vector alignment: `calculate_cosine`; equal shapes are required, and zero
  norms need an explicit interpretation by the caller.
- Tensor packing is shape-preserving bookkeeping: use flatten/unflatten for
  parameter blocks and stack/concat helpers only when leading dimensions match.
  These helpers do not change MuJoCo coordinate conventions.

See [kinematics workflows](references/kinematics-workflows.md) for concrete
edit, compile, IK, and cleanup sequences. See [troubleshooting](references/troubleshooting.md)
for failure-specific recovery.

## Robot/model relationship

A compiled `mujoco.MjModel` is the shared boundary between editing and a robot:
editing produces an `MjSpec`, compilation produces the model, and `Robot` can
construct its `MjData` from either a model path or an already compiled model.
Forward the data before reading site/body transforms. Environment code may apply
an `edit_fn` while building its spec and compile afterward; this sub-skill does
not own reset, stepping, rewards, or observation lifecycle.

## Runtime and safety boundaries

The documented path is base MuJoCo plus NumPy on CPU. MJX/JAX and CUDA are
optional acceleration paths and are not required for these APIs; do not claim
parity or import them as a fallback. The bundled smoke is non-rendering and
uses a generated temporary model. Viewer/Mink workflows remain optional and
are not needed to validate the solver contract.

Before handoff, verify:

- imports and internal links resolve without checkout-specific paths;
- edit functions compile a model and preserve intended names/properties;
- every created artifact is removed on success and on forced failure;
- valid and invalid IK targets exercise both return and validation paths; and
- the smoke reports `success`, residual, and iteration count rather than only
  printing a final configuration.
