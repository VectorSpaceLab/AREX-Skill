# Geometry and visualization API reference

This reference describes the NumPy/SymPy geometry helpers, the Matplotlib
helpers, and the URDF tree utility exposed by IKPy 4.0.0. The functions below
are diagnostic and model-space utilities; none of them sends commands to a
robot.

## Matrix and vector conventions

IKPy's geometry helpers use column vectors. A point is represented as
`p_h = [x, y, z, 1]`, and an affine transform is applied on the left:

```python
p_world_h = transform_world_from_local @ p_local_h
```

The usual affine shape is `4 x 4`, with a `3 x 3` rotation block, a translation
in `T[:3, 3]`, and a final row `[0, 0, 0, 1]`. `Chain.forward_kinematics`
starts with `np.eye(4)` and composes link frames as
`frame = frame @ link_frame_matrix`. With `full_kinematics=True`, it returns a
list of one `4 x 4` frame per link; otherwise it returns the terminal `4 x 4`
frame. Joint values for inactive links are still present in the input vector.
The construction and FK semantics themselves belong to `chain-kinematics`.

A few implementation details are important when inspecting helper results:

- `from_transformation_matrix(T)` returns `(T[:, -1], T[:-1, :-1])`. For a
  standard `4 x 4` affine matrix, its first item therefore has **shape `(4,)`**
  and includes the homogeneous final value `1`; it is not the usual `(3,)`
  position. Use `T[:3, 3]` when a three-dimensional point is required.
- `to_transformation_matrix(translation, orientation_matrix)` expects a
  length-3 translation and a `3 x 3` orientation. Its default orientation is
  `np.zeros((3, 3))`, not the identity, so always pass an orientation when a
  valid rigid transform is intended.
- The conversion helpers assume affine homogeneous coordinates. They strip the
  last row/column or last vector element; they do not divide by a general
  projective `w` value.

## Rotation helpers in `ikpy.utils.geometry`

All numeric rotation functions return a `3 x 3` NumPy array. Angles are in
radians.

| Function | Convention and result |
| --- | --- |
| `rx_matrix(theta)` | Positive right-handed rotation about X. |
| `ry_matrix(theta)` | Positive right-handed rotation about Y. |
| `rz_matrix(theta)` | Positive right-handed rotation about Z. |
| `rpy_matrix(roll, pitch, yaw)` | Extrinsic roll/pitch/yaw product `Rz(yaw) @ Ry(pitch) @ Rx(roll)`. This is the RPY convention used for URDF origins in this release. |
| `rotation_matrix(phi, theta, psi)` | A different Euler sequence: `Rz(phi) @ Rx(theta) @ Rz(psi)`. Do not substitute it for `rpy_matrix`. |
| `axis_rotation_matrix(axis, theta)` | Rodrigues-style rotation about `[x, y, z]`. The implementation uses the components as supplied and does not normalize them; pass a unit axis unless a deliberately scaled Rodrigues matrix is wanted. |
| `symbolic_rz_matrix(symbolic_theta)` | SymPy `3 x 3` Z rotation. |
| `symbolic_rotation_matrix(phi, theta, symbolic_psi)` | SymPy product matching the Z-X-Z `rotation_matrix` sequence. |
| `symbolic_axis_rotation_matrix(axis, symbolic_theta)` | SymPy Rodrigues-style matrix using the supplied axis components. |

For a rigid rotation, verify `R.shape == (3, 3)`, `R.T @ R` is close to the
identity, and `det(R)` is close to `1`. Such checks catch degrees-versus-radians,
row/column, and non-unit-axis mistakes before they are hidden in a rendering.

## Translation and Cartesian/homogeneous conversions

| Function | Input/output behavior |
| --- | --- |
| `get_translation_matrix(mu)` | Builds a numeric `4 x 4` identity with `mu` in `[:3, 3]`. |
| `get_symbolic_translation_matrix(mu)` | SymPy version of the same affine translation. |
| `homogeneous_translation_matrix(trans_x, trans_y, trans_z)` | Numeric `4 x 4` translation matrix from three scalars. |
| `cartesian_to_homogeneous(M, matrix_type="numpy")` | Embeds a square `n x n` Cartesian matrix in the upper-left of an `(n+1) x (n+1)` identity. `matrix_type` accepts `"numpy"` or `"sympy"`; other values raise `ValueError`. |
| `cartesian_to_homogeneous_vectors(v, matrix_type="numpy")` | Appends `1` to a NumPy vector, producing length `n+1`. Other matrix types raise `ValueError`. |
| `homogeneous_to_cartesian_vectors(v_h)` | Returns `v_h[:-1]`; for a normal 4-vector this is shape `(3,)`. |
| `homogeneous_to_cartesian(T_h)` | Returns `T_h[:-1, :-1]`; for a normal transform this is the `3 x 3` rotation block, not the translation. |
| `from_transformation_matrix(T)` | Returns the implementation's `(T[:, -1], T[:-1, :-1])`; see the shape warning above. |
| `to_transformation_matrix(translation, orientation_matrix)` | Places a length-3 translation and `3 x 3` orientation into a `4 x 4` identity. |

For a point, use `cartesian_to_homogeneous_vectors` and a matrix product. For a
rotation block, use `cartesian_to_homogeneous`. Do not pass a `3 x 1` matrix to
the vector helper when downstream code expects a one-dimensional `(3,)` array.

## Matplotlib chain and frame helpers

`ikpy.utils.plot` imports Matplotlib at module import time. Install the `plot`
extra (`matplotlib` and the Python `graphviz` package) when these optional
visualization APIs are needed; NumPy/SciPy/SymPy are the base dependencies.
In a headless process, choose `Agg` before importing this module.

| Function | Behavior |
| --- | --- |
| `plot_basis(ax, arm_length=1)` | Sets X/Y/Z labels and limits to `[-1, 1]`, then draws the origin basis. Reset limits after the call for larger models. |
| `init_3d_figure()` | Creates a Matplotlib figure and 3D axes, calls `plot_basis`, and returns `(fig, ax)`. |
| `plot_chain(chain, joints, ax, name="chain")` | Computes `full_kinematics=True`, plots link-node positions, joint axes, and the final frame. `joints` must have one value per link. It draws onto the supplied axes and does not show or save the figure. |
| `plot_frame(frame_matrix, ax, length=1)` | Draws dashed X/Y/Z axes from the frame origin using a `4 x 4` transform. |
| `plot_target(target, ax)` | Adds a red scatter point using the first three target values. |
| `plot_target_trajectory(targets_x, targets_y, targets_z, ax)` | Adds a scatter trajectory from three separate coordinate arrays. |
| `show_figure()` | Calls Matplotlib's `show`; call it only for an explicitly interactive request. |

`Chain.plot(joints, ax, target=None, show=False)` is a thin wrapper around
these helpers. If `ax` is `None`, it creates a new 3D figure, plots the chain,
optionally adds the target, and only calls `show_figure` when `show=True`. It
returns `None`, so retain the figure returned by `init_3d_figure` when saving.
Repeated calls on one axes intentionally overplot; use distinct names, clear
axes, or separate figures when comparing configurations.

## URDF tree visualization

`ikpy.urdf.utils.get_urdf_tree(urdf_path, root_element,
out_image_path=None, legend=False)` parses an existing URDF XML file and
returns `(dot, urdf_tree)`:

- `root_element` must exactly match a `<link name="...">`; otherwise it raises
  `ValueError`.
- `dot` is a `graphviz.Digraph`. Link nodes use blue styling and joint nodes use
  green styling; `dot.source` is useful for a text-only inspection.
- `urdf_tree` is an experimental `URDFTree`; its `children_links` dictionary
  exposes the recursively discovered child links.
- With `out_image_path=None`, no rendering is requested. With a path, the
  utility calls `dot.render(out_image_path)`, which generally treats the value
  as a Graphviz output base and may append a format suffix. Rendering needs both
  the Python `graphviz` package and the system Graphviz `dot` executable.
- This helper visualizes the parsed link/joint tree; it does not create an
  IKPy `Chain` and does not validate actuator limits or physical connectivity.

Inspect the DOT/tree return values first, and render only after the root and
write location are known. Parser/model details belong to `robot-model-import`.
