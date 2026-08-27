# Visualization and geometry troubleshooting

## Optional dependency failures

### `matplotlib` is missing

`ikpy.utils.plot` imports Matplotlib immediately, and `Chain.plot` imports that
module when called. Install the package's `plot` extra or install Matplotlib in
the active Python environment. The base IKPy dependencies do not guarantee
plotting support. Numeric geometry checks in `ikpy.utils.geometry` do not need
Matplotlib.

If a script only needs `--help`, keep plotting imports after argument parsing;
the bundled smoke script follows that pattern. This makes command discovery
work even when optional plotting dependencies are absent, although generating
the image still requires them.

### Python `graphviz` or native Graphviz is missing

`ikpy.urdf.utils` imports `graphviz.Digraph` at module import time, so even a
no-render call can fail if the Python `graphviz` package is absent. Install the
package's plotting extra or add the Python package to the environment.

A separate failure occurs during `dot.render(...)` when the native Graphviz
`dot` executable is not installed or is not on `PATH`. Installing only the
Python package is not sufficient for rendering. If native Graphviz is
unavailable, call `get_urdf_tree(..., out_image_path=None)`, inspect
`dot.source` and the returned `URDFTree`, or produce a DOT source artifact for
a separately provisioned renderer. Do not silently treat a returned `Digraph`
as a rendered image.

### JAX is unrelated to plotting

The optional JAX extra is not required for these Matplotlib or Graphviz
operations. Use NumPy geometry for deterministic inspection unless the
separate JAX-backend workflow is specifically under test.

## Headless backend errors

Set the backend before importing `matplotlib.pyplot` or `ikpy.utils.plot`:

```python
import matplotlib
matplotlib.use("Agg", force=True)
from ikpy.utils import plot
```

Alternatively, configure a process-wide non-interactive Matplotlib backend
before launching the process. Changing the backend after pyplot has already
created a figure may be too late and can produce display or GUI backend
errors. In CI and batch jobs:

- call `Chain.plot(..., show=False)`;
- save the retained `fig` explicitly;
- do not call `plot.show_figure()`; and
- close the figure after saving.

`show=True` is an explicit interactive request and calls Matplotlib show. It is
not a necessary step for saving an image. If a display is expected but no
window appears, verify that the caller did request interactive behavior rather
than trying to fix a safe headless run.

## Shape and convention mistakes

### Wrong frame or mirrored orientation

Confirm all of the following:

- RPY is `Rz(yaw) @ Ry(pitch) @ Rx(roll)` and angles are radians.
- `rotation_matrix(phi, theta, psi)` is Z-X-Z (`Rz(phi) @ Rx(theta) @
  Rz(psi)`), not RPY.
- IKPy uses column vectors and left multiplication; do not transpose a frame
  merely to make a row-vector convention fit.
- An affine point is length 4 with final value 1, while a Cartesian point is
  length 3.
- `axis_rotation_matrix` does not normalize its axis; normalize a direction
  before using Rodrigues' formula.

Check `R.T @ R`, determinant, `T.shape`, `T[:3, 3]`, and the final row before
looking at a picture. For `from_transformation_matrix`, remember that the
returned first item is `T[:, -1]` and thus has four entries for a `4 x 4`
transform. `homogeneous_to_cartesian_vectors` strips the final value, while
`homogeneous_to_cartesian` strips the last row and column and returns only the
rotation block.

`to_transformation_matrix` silently uses a zero `3 x 3` orientation if its
orientation argument is omitted. Pass `np.eye(3)` for an identity orientation;
do not assume the default is a valid identity rotation.

### Wrong chain input

`Chain.forward_kinematics` and the plotting path require one joint value per
link, including inactive links. A length mismatch raises `ValueError`. The
last link is normally inactive in a chain's active mask, but its value remains
in the vector. Chain construction and FK/IK repairs belong to
`chain-kinematics`.

`Chain.plot` accepts a Matplotlib axes object or `None`; it does not accept a
raw figure in place of axes. A target should provide at least three numeric
coordinates. An IK target may be reachable numerically even when the visual
model or units are wrong, so compare the terminal frame directly.

## Overplotting, clipping, and misleading images

- `init_3d_figure` calls `plot_basis`, which sets all three axes to `[-1, 1]`.
  Reset limits for chains or targets outside that cube.
- `Chain.plot` and `plot.plot_chain` draw onto existing axes and do not clear
  them. Repeated calls can make nodes, axes, and targets look thicker or hide
  which configuration is which. Use separate figures, clear the axes between
  cases, or label lower-level `plot_chain` calls.
- `plot_chain` draws the terminal frame and joint axes based on the numeric
  full-kinematics frames. A visually plausible line can still have a bad
  orientation; always pair an image with numeric checks.
- Save with a deliberate format and close the figure. The smoke script refuses
  to overwrite an existing output unless `--force` is supplied; follow the
  same policy in batch evaluations when accidental replacement would obscure
  evidence.
- If a target is not visible, check that it is a three-coordinate sequence,
  that it lies within current axis limits, and that the chain and target use
  the same units and frame.

## URDF tree failures

- `ValueError: <root> not found in the URDF` means `root_element` is not an
  exact link name. It is not a request to guess a nearby link or a joint name.
- XML parsing errors indicate malformed or unreadable input; route the model
  file and parser diagnosis to `robot-model-import`.
- If the DOT object exists but no image appears, check the actual rendered
  filename (Graphviz commonly appends a suffix), output directory permissions,
  and the native `dot` executable.
- A tree visualization only follows links and joints reachable from the chosen
  root in the parsed XML. It is not a complete physical or actuator audit.

## Unsafe hardware assumptions

Plotting and geometry helpers are offline computations. They do not connect to
motors, issue joint commands, enforce a controller's limits, or guarantee that
an imported model matches a physical assembly. Never use `show=True`, a saved
image, a target overlay, or a successful numeric residual as authorization for
motion. Keep hardware drivers and control scripts outside this sub-skill.

Before any separately governed physical operation, validate units, joint
limits, coordinate frames, collision constraints, emergency-stop readiness,
and model-to-hardware identity through the authorized control workflow. If that
information is unavailable, stop at numeric inspection and offline rendering.
