# Chain kinematics troubleshooting

Use the symptom first, then rerun the smallest relevant check in
[`scripts/smoke_chain.py`](../scripts/smoke_chain.py). The guidance below is
specific to the NumPy/Scipy chain route. For JAX errors, use the sibling
JAX-backend route; for model-file errors, use robot-model-import.

## Install and import

### `ModuleNotFoundError: No module named 'ikpy'`

- **Cause:** IKPy is not installed in the Python interpreter running the
  command, or the environment is different from the one used to install it.
- **Recovery:** install the package (`pip install ikpy`) or install the
  checked-out project with its normal packaging command, then run
  `python -c "import ikpy; print(ikpy.__version__)"` in that same interpreter.
  Base kinematics needs NumPy, SciPy, and SymPy. Plotting is optional; do not
  install it just to run FK/IK.
- **Check:** run `python scripts/smoke_chain.py --help` and then the smoke
  command. The helper does not download models or require Matplotlib.

### Symbolic import or lambdify errors

- **Cause:** `sympy` is absent/broken, or a custom link contains an unsupported
  symbolic value.
- **Recovery:** verify `import sympy`; for a small diagnostic fixture set
  `use_symbolic_matrix=False` on `URDFLink`. Keep numeric arrays and scalar
  actuator values explicit. Do not treat this as a solver convergence issue.

### Plot import failure while testing kinematics

- **Cause:** `Chain.plot` imports optional plotting dependencies.
- **Recovery:** validate with `forward_kinematics` and residuals instead. Install
  `ikpy[plot]` only when plotting is actually needed, then route plotting code
  to visualization-geometry.

## Dimensions, order, and masks

### `ValueError: Your joints vector length is ... but you have ... links`

- **Cause:** FK received only active values or omitted the origin/fixed/tip
  entries.
- **Recovery:** construct `q = [0.0] * len(chain.links)` and replace active
  positions. Use `chain.active_to_full(active_values, initial_full)` when
  converting optimizer output. Confirm `len(q) == len(chain.links)` before FK.

### `ValueError: Your active links mask length ... is different ...`

- **Cause:** the mask does not have one boolean per link.
- **Recovery:** inspect `[(i, link.name, link.joint_type) for i, link in
  enumerate(chain.links)]`, then create the mask from that exact list. The
  origin and terminal/fixed links are usually `False`.

### The terminal link is optimized or the constructor did not warn

- **Cause:** the constructor's last-entry test uses Python identity (`is True`)
  against a NumPy scalar and can fail to override a NumPy boolean. A fixed tip
  can also be accidentally left active.
- **Recovery:** pass a Python list whose last entry is `False`, then assert
  `not bool(chain.active_links_mask[-1])` after construction. Keep the terminal
  value in every full vector. If the tip is meant to move, model that actuator
  as the preceding active link and leave the final geometry/tool link inactive.

### Fixed-link warning at chain construction

- **Symptom:** warning that a fixed link is active.
- **Cause:** `active_links_mask` includes `True` for `OriginLink` or another
  fixed link. It does not make that link movable.
- **Recovery:** mark it `False`; retain its zero/full-vector slot. Confirm the
  mask count and use `active_from_full` to see which values are actually
  optimized.

### IK returns a shape error or strange inactive values

- **Cause:** `initial_position` was shortened to active joints, or a target was
  passed in the wrong shape. IKPy reconstructs a full output from the full
  initial vector.
- **Recovery:** supply `initial_position=np.zeros(len(chain.links))` or a full
  previous solution. Use a position shape `(3,)`, one-axis orientation shape
  `(3,)`, `all` orientation shape `(3, 3)`, and frame target shape `(4, 4)`.

## Unreachable targets and bounds

### IK returns a result but FK misses the target

- **Cause:** IK is a numerical least-squares/minimize operation; the target may
  be outside the chain's reachable workspace, poorly conditioned, or trapped
  by a local minimum. No exception is required for a best-effort result.
- **Recovery:** recompute FK, calculate `np.linalg.norm(fk[:3, 3] - target)`,
  inspect the full result, try a physically plausible `initial_position`, and
  solve from several seeds when the application permits. Check link origins,
  axis directions, units, and the last-link offset before changing optimizer
  settings.
- **Stop/decision point:** if the residual remains too high across valid seeds,
  report the target as unreachable or the model as inconsistent instead of
  claiming success.

### `ValueError` from SciPy about an initial point or bounds

- **Cause:** an active initial value lies outside its `(lower, upper)` tuple,
  lower exceeds upper, or a bound has the wrong shape/type.
- **Recovery:** inspect `[(link.name, link.bounds) for link in chain.links]`,
  ensure finite limits and the initial active values use the same units (usually
  radians), and set bounds only on the intended active links. Inactive link
  bounds are not optimization variables.

### Bounded solution is at a limit

- **Meaning:** this often indicates a real constrained optimum, not a solver
  crash. Verify `lower <= q_active <= upper` and report the residual and the
  saturated joint.
- **Recovery:** widen the bound only if the robot permits it; otherwise change
  the target, initial seed, chain geometry, or task tolerance. Do not silently
  replace a physical bound with infinity.

### `max_iter` appears to have no effect

- **Cause:** the NumPy implementation retains `max_iter` only for compatibility
  and logs that it is no longer used.
- **Recovery:** remove it rather than assuming a three-iteration test is being
  enforced. Use the supported SciPy kwargs appropriate to the package version
  only after checking the installed implementation; validate with residuals.

## Optimizer and target-mode failures

### `Unknown solver: ...`

- **Cause:** NumPy IK accepts only `optimizer="least_squares"` or
  `optimizer="scalar"`.
- **Recovery:** use the default `least_squares` first; use `scalar` only when
  its scalar-norm behavior is desired. Do not pass JAX profiling labels such as
  `"scipy"` to the NumPy API.

### `Unable to optimize against neither position or orientation`

- **Cause:** `target_position=None` and `orientation_mode=None` leave no
  residual objective.
- **Recovery:** provide a `(3,)` position, or provide `target_orientation` and
  one of `"X"`, `"Y"`, `"Z"`, or `"all"`.

### `Unknown orientation mode: ...`

- **Cause:** mode is case-sensitive and must be exactly `None`, `"X"`, `"Y"`,
  `"Z"`, or `"all"`.
- **Recovery:** normalize user-facing input before calling IK, but keep the
  package spelling in the actual call.

### Orientation target broadcasts, fails assignment, or converges to a bad frame

- **Cause:** `X`, `Y`, and `Z` require a 3-vector; `all` requires a 3x3 block.
  The implementation inserts the values into an identity frame without
  validating orthonormality, so a malformed matrix can still be optimized.
- **Recovery:** validate `np.asarray(target).shape`; for `all`, check
  `R.T @ R ≈ I` and `det(R) ≈ 1`; compare the selected frame columns after FK.
  Use a staged solve (position first, then orientation with the prior solution)
  when a coupled objective is difficult.

### Orientation-only solve moves the tool position

- **Meaning:** expected. With `target_position=None`, only orientation is in the
  residual, so any position compatible with that orientation may be returned.
- **Recovery:** if position must remain fixed, include `target_position` in the
  same call; otherwise validate only the orientation block and preserve the
  solution's full vector for the next warm start.

## Link modeling and geometry

### `Joint type is 'revolute' ...` or `Joint type is 'prismatic' ...`

- **Cause:** the axis fields do not match the declared joint type.
- **Recovery:** revolute means `rotation` only; prismatic means `translation`
  only; fixed means neither. Use 3-element numeric vectors and check the axis
  convention before solving.

### FK has the wrong translation or orientation

- **Cause:** frame products are ordered: origin translation, RPY orientation,
  then actuator transform. An incorrect axis, RPY order, unit, or link offset
  changes the entire downstream frame.
- **Recovery:** call `forward_kinematics(q, full_kinematics=True)` and inspect the
  first frame where the expected transform diverges. Check that RPY is supplied
  as `[roll, pitch, yaw]` and follows `Rz(yaw) @ Ry(pitch) @ Rx(roll)`. Check
  that axes are unit vectors and prismatic values are distances.

### DH labels or frames look unexpected

- **Cause:** in this release `DHLink(name=...)` accepts the name but does not
  pass it to the base `Link` correctly; the generated link name may be a boolean.
  DH output is a `numpy.matrix`, and the `theta` parameter is added to the
  stored offset.
- **Recovery:** set `link.name` after construction, convert frames with
  `np.asarray`, verify the standard DH row and `length`, and keep all angles in
  radians. Compare each intermediate frame, not only the end frame.

### `from_transformation_matrix` returns a four-element translation

- **Cause:** the actual helper returns the complete homogeneous last column,
  including its trailing `1`.
- **Recovery:** use `translation4[:3]` for Cartesian coordinates and validate
  `translation4[3] == 1`; the rotation output is the upper-left `(3, 3)` block.

## Serialization and composition

### `to_json_file` raises `KeyError` or writes an unexpected path

- **Cause:** the chain was constructed directly from links and has no private
  URDF metadata, or the original URDF path has an unexpected relative dirname.
- **Recovery:** use JSON serialization only for a chain returned by
  `Chain.from_urdf_file`; keep the JSON beside its referenced URDF. For custom
  chains, define an application-owned schema for link parameters rather than
  populating private `_urdf_metadata`.

### `to_json_file` raises `OSError: File ... exists`

- **Cause:** serialization protects an existing `<chain name>.json`.
- **Recovery:** choose a new chain name/output context or call `force=True`
  only when replacing that exact file is intentional. After writing, reload
  with `Chain.from_json_file` and compare a known FK frame.

### `Chain.concat` reports a mask-length mismatch

- **Cause:** v4.0.0 implements `chain1.active_links_mask + chain2.active_links_mask`
  on NumPy arrays, which is elementwise addition rather than list extension.
- **Recovery:** concatenate `chain1.links + chain2.links` and Python lists of
  booleans explicitly, construct a new `Chain`, then verify the combined mask
  length and inactive terminal link. Treat the public `concat` helper as
  unreliable for this release.
