# Visualization and numeric-check workflows

These procedures are deliberately model-space and file-output only. They make
no assumption that a robot, simulator, driver, or controller is present.

## 1. Inspect a transform before rendering

Use a numeric check whenever a plot appears mirrored, rotated around the wrong
axis, or offset from the expected target. The check should be independent of
Matplotlib:

```python
import numpy as np
from ikpy.utils import geometry

roll, pitch, yaw = 0.2, -0.1, 0.4
R = geometry.rpy_matrix(roll, pitch, yaw)
expected = geometry.rz_matrix(yaw) @ geometry.ry_matrix(pitch) @ geometry.rx_matrix(roll)
assert R.shape == (3, 3)
np.testing.assert_allclose(R, expected)
np.testing.assert_allclose(R.T @ R, np.eye(3), atol=1e-12)
assert np.isclose(np.linalg.det(R), 1.0)

T = geometry.to_transformation_matrix([0.3, -0.2, 0.5], R)
assert T.shape == (4, 4)
np.testing.assert_allclose(T[:3, :3], R)
np.testing.assert_allclose(T[:3, 3], [0.3, -0.2, 0.5])
np.testing.assert_allclose(T[3, :], [0, 0, 0, 1])

point_h = geometry.cartesian_to_homogeneous_vectors(np.array([1., 2., 3.]))
point_back = geometry.homogeneous_to_cartesian_vectors(T @ point_h)
assert point_back.shape == (3,)
```

The `rotation_matrix(phi, theta, psi)` helper intentionally checks a different
Z-X-Z Euler sequence (`Rz(phi) @ Rx(theta) @ Rz(psi)`). Compare against that
product when testing it; do not use it as an alternate spelling of RPY. For
`axis_rotation_matrix`, normalize an arbitrary input axis yourself and verify
orthogonality. IKPy applies the provided axis components as-is.

When using `from_transformation_matrix`, inspect position as `T[:3, 3]` rather
than assuming the returned first tuple item is a 3-vector. The implementation
returns the complete final column, including homogeneous `w`.

## 2. Validate a chain numerically, then add a target overlay

After `chain-kinematics` has supplied a valid chain and full-length joint
vector, check frames before plotting:

```python
frames = chain.forward_kinematics(joints, full_kinematics=True)
assert len(frames) == len(chain.links)
assert all(frame.shape == (4, 4) for frame in frames)
end_frame = frames[-1]
end_position = end_frame[:3, 3]
```

If a target is available, compare `end_position` with it using a stated
absolute tolerance. A red point in a picture is not a substitute for this
numeric residual. If orientation matters, compare `end_frame[:3, :3]` to the
requested orientation and check orthogonality as above.

For a saved 3D overlay in a headless process, choose the backend before any
Matplotlib pyplot or IKPy plotting import:

```python
import matplotlib
matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt
from ikpy.utils import plot

fig, ax = plot.init_3d_figure()
chain.plot(joints, ax=ax, target=target, show=False)
# plot_basis starts with [-1, 1] limits; enlarge them for larger models.
fig.savefig(output_path, bbox_inches="tight")
plt.close(fig)
```

`Chain.plot` returns `None`; retain `fig` from `init_3d_figure`. Do not call
`plot.show_figure()` in batch jobs. If interactive display is explicitly
requested, call it only after the save and only in a branch controlled by that
request.

The bundled `scripts/smoke_plot.py` demonstrates this sequence using a tiny
inline chain, so it is safe to run without a model file. It accepts a selected
output path, refuses an existing file unless `--force` is supplied, and creates
missing parent directories.

## 3. Compare configurations without losing frame context

To compare a home and solved configuration, create one figure and call
`chain.plot` twice with `show=False`, or use two figures if the model is dense.
Give each call a meaningful chain name only when using the lower-level
`plot.plot_chain`; `Chain.plot` uses `chain.name`. Add one target point with
`target=[x, y, z]` and compute the endpoint residual separately.

For a target path, `plot.plot_target_trajectory` takes three coordinate
sequences, not a single `N x 3` argument:

```python
targets = np.asarray(targets)
plot.plot_target_trajectory(targets[:, 0], targets[:, 1], targets[:, 2], ax)
```

Before saving, adjust `ax.set_xlim3d`, `set_ylim3d`, and `set_zlim3d` if the
chain extends beyond the initial `[-1, 1]` ranges. Use a consistent scale when
comparing images. Close every non-interactive figure to prevent state leakage
between batch cases.

## 4. Show intermediate frames and joint axes

`plot.plot_chain` already draws the chain nodes, rotation/translation axes, and
the final frame. To inspect an intermediate frame, use the list returned by
`full_kinematics=True` and draw selected frames explicitly:

```python
fig, ax = plot.init_3d_figure()
plot.plot_chain(chain, joints, ax, name="configuration")
for index in (0, len(frames) // 2, len(frames) - 1):
    plot.plot_frame(frames[index], ax, length=chain.links[index].length or 0.1)
fig.savefig(output_path, bbox_inches="tight")
```

Use a positive fallback length for zero-length links so the frame is visible.
Remember that a frame is a transform, not a control command. If an axis looks
wrong, inspect the numeric `frame[:3, :3]`, the link's declared axis, and the
multiplication order before changing plot colors or camera limits.

## 5. Inspect and render a URDF link/joint tree

Once `robot-model-import` has established the path and intended root link:

```python
from ikpy.urdf.utils import get_urdf_tree

dot, tree = get_urdf_tree(
    urdf_path,
    root_element="base",
    out_image_path=None,
    legend=True,
)
print(dot.source)
print(sorted(tree.children_links))
```

This no-render call is useful in minimal or headless environments and still
checks XML parsing, root selection, and tree construction. To render, provide
an output base path in a writable directory:

```python
dot, tree = get_urdf_tree(
    urdf_path,
    root_element="base",
    out_image_path=output_base,
    legend=True,
)
```

Graphviz may append the selected format suffix to the base. Verify the actual
created file rather than assuming the input string is the final filename. The
Python package and the native `dot` executable are separate prerequisites.
Inspecting `dot.source` first also avoids paying the rendering cost when only a
structural check is needed.

## 6. Use visuals as validation evidence, not as hardware evidence

A good visual-validation record contains:

1. the package/API version and model source identity already approved by the
   caller;
2. joint-vector length and whether inactive links were included;
3. numeric end-frame position/orientation residuals and tolerances;
4. the output file path and rendering backend;
5. whether targets, trajectories, and intermediate frames were overlaid; and
6. any clipping, missing optional dependency, or unresolved model ambiguity.

A rendered chain only shows the transformations encoded by the local model. It
cannot prove the URDF matches a physical robot, that joint limits are safe, or
that a controller would move as shown. Keep this workflow disconnected from
hardware-control code and require a separate, authorized control procedure for
any physical action.
