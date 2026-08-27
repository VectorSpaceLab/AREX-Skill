# Troubleshooting model editing and kinematics

## Model and XML failures

### `ModelEditor` raises `ValueError: Error opening file`

**Likely causes:** the path is absent, unreadable, a relative path was resolved
from the wrong working directory, or an XML include/asset is unavailable.

**Recovery:** check existence and readability before construction, use an
absolute path supplied by the caller, and inspect the underlying MuJoCo error.
Do not create a new model path by guessing an asset location. The invalid-path
case should fail without creating an edited artifact.

### Edit function gets `None` for a body or site

**Likely cause:** the name belongs to a different model variant, was already
removed, or the edit assumed a body hierarchy that is not present.

**Recovery:** enumerate or query names from the current `MjSpec`, fail with the
missing name and expected role, and make the edit variant-aware. Snapshot
properties before deleting a body. Never proceed by adding a replacement with
an invented pose unless the task explicitly defines that pose.

### Compiled XML fails after a successful-looking edit

**Likely causes:** a mesh name was not preserved, duplicate names were added,
a parent chain was broken, a site/geom attribute has the wrong type, or an
include-relative asset cannot be resolved.

**Recovery:** call `spec.compile()` before serialization when possible, then
compile the written XML too. Validate replacement body/geom/site names and
parent IDs. Compare the generated XML with the source only for intended
changes. Keep source assets read-only.

### Temporary XML remains after a failure

**Likely cause:** cleanup was called only on the success path, or
`delete_edited_xml()` was called after a failure before a usable artifact path
was known.

**Recovery:** track `artifact: str | None`, remove it in `finally` only if it
exists, and clean caller-tracked partial files. Make cleanup idempotent in the
caller; the raw editor method itself assumes the path exists. Test both a
successful compile and a forced compile/write failure.

### Cleanup deletes the wrong file or raises `FileNotFoundError`

**Likely cause:** the editor's derived path was confused with the original
model, or cleanup was repeated without an existence guard.

**Recovery:** compare the returned artifact with the source before deletion,
use an explicit ownership flag, and guard `os.path.exists`. Never use a broad
glob or delete a directory recursively for this workflow.

## IK input and interface failures

### `ValueError` says a target is required

**Cause:** both `target_pos` and `target_quat` are `None`.

**Recovery:** provide one or both targets. Do not pass an empty array as a
placeholder; validate the exact shape `(3,)` or `(4,)` first.

### Shape, dtype, or NaN errors occur

**Likely causes:** a batched `(1, 3)` position was passed where `(3,)` is
required, quaternion order was confused, or a tensor contains NaN/Inf.

**Recovery:** squeeze or select one sample at the task boundary, convert to a
finite floating NumPy array, and reject the request if the resulting shape is
wrong. Preserve MuJoCo quaternion order `(w, x, y, z)`. Do not silently flatten
an array because that can turn a malformed batch into a plausible but wrong
pose.

### `joint_names` type error or wrong DOFs move

**Likely causes:** a string was passed instead of a list/tuple/NumPy array, or
joint IDs were mistaken for DOF indices. Ball/free joints may contribute more
than one DOF.

**Recovery:** pass a sequence of model joint names, confirm each name exists,
and let the named indexer map names to DOFs. If no subset is intended, use
`None`. Log the selected names and resulting number of columns.

### Site lookup fails or site pose is stale

**Likely causes:** the site was removed by an edit, the wrong model/data pair
was used, or forward kinematics was not run after changing qpos.

**Recovery:** query the site in the compiled model, pair data with that model,
run MuJoCo forward propagation, and retry. If the target site was intentionally
replaced, update the request to the new name rather than hiding the failure.

### Solver returns `success=False` at `max_steps`

**Likely causes:** target is unreachable, the initial configuration is poor,
the Jacobian is singular, the selected joints cannot express the pose, or the
budget is too small. The algorithm does not enforce joint limits.

**Recovery:** report `err_norm` and `steps`, test reachability with a nearby
known target, choose an allowed joint subset that spans the task, try a
justified initial state, increase `max_steps` within a stated bound, or add
regularization. Check position and orientation residuals separately. Never
label an unsuccessful result as a solution.

### Solver stops early with insufficient progress

**Cause:** the progress heuristic sees a large residual relative to the joint
update, often near a singularity or local minimum.

**Recovery:** inspect the Jacobian rank/conditioning, move the initial state,
use a less restrictive joint subset only when permitted, or tune
`regularization_strength`, `max_update_norm`, and `progress_thresh`. Keep a
hard step bound and record the changed controls.

### Orientation appears correct but position is poor (or vice versa)

**Cause:** position and rotation are combined with `rot_weight`; one objective
may dominate. A quaternion sign or frame convention may also be wrong.

**Recovery:** run position-only and orientation-only diagnostics, inspect each
residual, confirm the target frame and quaternion order, then choose a justified
weight. Verify the achieved rotation with a matrix or relative quaternion, not
component-wise quaternion equality.

## Runtime boundaries

### MJX/JAX/CUDA is unavailable

This is not a base CPU failure. Model editing, standard MuJoCo compilation,
NumPy helpers, and the documented site-pose API remain CPU paths. Install and
verify optional acceleration separately when the task explicitly needs it;
do not silently substitute an unverified JAX implementation or claim parity.

### Bundled smoke cannot import MyoSuite

**Likely cause:** the base package dependencies, especially Gymnasium, are not
installed in the active environment. The smoke is intentionally non-rendering
but still requires the installed MyoSuite package and MuJoCo.

**Recovery:** run it in the prepared MyoSuite CPU environment, inspect the
first missing dependency, and do not repair by adding a viewer or CUDA stack.
The script should fail clearly and leave no generated asset behind.
