# JAX backend API reference

This reference describes IKPy 4.0.0's JAX surface. The public entry points are
methods on `ikpy.chain.Chain`; `JaxKinematicsCache` and the low-level functions
are useful for advanced inspection and controlled reuse.

## Optional dependency and availability

The base installation contains NumPy, SciPy, and SymPy. JAX support is an
optional extra:

```bash
python -m pip install 'ikpy[jax]'
# Equivalent package requirements: jax and jaxlib
```

`ikpy.JAX_AVAILABLE` is `True` only when importing both `jax` and
`ikpy.jax_backend` succeeds. `Chain.jax_cache` raises:

```python
ImportError("JAX is not installed. Install it with: pip install jax jaxlib")
```

JAX device selection is controlled by the installed JAX runtime and environment,
not by IKPy. CPU JAX is the only baseline guaranteed by this skill; the optional
extra does not itself guarantee CUDA, a compatible GPU plugin, or acceleration.

## Chain dispatch signatures

```python
Chain.__init__(
    links,
    active_links_mask=None,
    name="chain",
    urdf_metadata=None,
    jax_precompile=True,
    **kwargs,
)
```

`jax_precompile` is stored on the chain and used when `jax_cache` is first
accessed. `True` creates AOT-compiled FK, full-FK, residual, and Jacobian
functions during cache construction. `False` creates JIT wrappers and defers
compilation until they are called. The cache is memoized at
`chain._jax_cache`; changing `chain._jax_precompile` after cache creation does
not rebuild an existing cache.

```python
@property
Chain.jax_cache -> JaxKinematicsCache
```

```python
Chain.forward_kinematics(
    joints: list,
    full_kinematics=False,
    backend: str = "numpy",
)
```

`joints` must contain one value for every link, including inactive and origin
links. With `backend="jax"`, the method calls
`chain.jax_cache.forward_kinematics`. It returns a NumPy `(4, 4)` array, or a
list of NumPy `(4, 4)` arrays when `full_kinematics=True`. The only documented
backend values are `"numpy"` and `"jax"`; other values fall through to the
NumPy implementation rather than selecting a third backend.

```python
Chain.inverse_kinematics(
    target_position=None,
    target_orientation=None,
    orientation_mode=None,
    backend: str = "numpy",
    **kwargs,
)
```

```python
Chain.inverse_kinematics_frame(
    target,
    initial_position=None,
    backend: str = "numpy",
    **kwargs,
)
```

`target` must have shape `(4, 4)`. For the JAX route, `Chain` extracts the JAX
kwargs below and forwards them to `JaxKinematicsCache.inverse_kinematics`.
`initial_position` is full-chain length and defaults to zeros. Returned IK
solutions are full-chain NumPy arrays, with inactive values preserved from the
initial position.

The high-level `Chain.inverse_kinematics` builds an identity target frame:
`target_position` sets the translation, and `target_orientation` fills the
selected rotation axis or full rotation block. Supported `orientation_mode`
values are exactly:

- `None`: position only when a position is provided; no orientation residual.
- `"X"`, `"Y"`, or `"Z"`: match that target frame axis. If no position is
  supplied, only the selected axis is optimized.
- `"all"`: match the complete `3 x 3` rotation block. If no position is
  supplied, only the orientation block is optimized.

When using `inverse_kinematics_frame` directly, pass `orientation_mode` and
`no_position` in `kwargs`; they are not explicit parameters on that method.
`(orientation_mode=None, no_position=True)` is rejected by the residual builder
because it would request an empty objective.

## JAX IK kwargs

The exact backend signature is:

```python
JaxKinematicsCache.inverse_kinematics(
    target_frame,
    initial_position=None,
    orientation_mode=None,
    no_position=False,
    tol=1e-6,
    use_analytical_jacobian=True,
    scipy_method="trf",
    scipy_x_scale="jac",
    scipy_loss="linear",
    scipy_gtol=None,
    scipy_max_nfev=None,
    scipy_tr_solver=None,
    scipy_tr_options=None,
    scipy_verbose=0,
)
```

All of these names can be passed through `Chain.inverse_kinematics` or
`Chain.inverse_kinematics_frame` with `backend="jax"`:

| kwarg | Meaning and accepted values |
| --- | --- |
| `tol` | Passed as SciPy `ftol` and `xtol`; default `1e-6`. It does not set `gtol`. |
| `use_analytical_jacobian` | `True` (default) passes a JAX `jax.jacfwd` Jacobian to SciPy; `False` omits `jac` and lets SciPy finite-difference it. |
| `scipy_method` | SciPy least-squares method: `"trf"` (default), `"dogbox"`, or `"lm"`. `"lm"` is unconstrained here because IKPy omits bounds for it. |
| `scipy_x_scale` | Passed as `x_scale` when not `None`; default `"jac"`, or an array-like scale. `None` omits it. |
| `scipy_loss` | Passed as `loss`; repository docs list `"linear"` (default), `"soft_l1"`, `"huber"`, `"cauchy"`, and `"arctan"`. SciPy method restrictions still apply, especially `"lm"` with non-linear losses. |
| `scipy_gtol` | Optional gradient termination tolerance; omitted when `None`. |
| `scipy_max_nfev` | Optional maximum function evaluations; omitted when `None`. Use a finite small value in smoke or control loops. |
| `scipy_tr_solver` | Optional `"exact"` or `"lsmr"`; added only for `"trf"` and `"dogbox"`. |
| `scipy_tr_options` | Optional dict passed as `tr_options`, only for `"trf"` and `"dogbox"`; for `lsmr`/`trf`, `{"regularize": True}` can help ill-conditioned Jacobians. |
| `scipy_verbose` | SciPy verbosity integer, normally `0`, `1`, or `2`; default `0`. |

IK uses `scipy.optimize.least_squares`. The active variables are selected from
`chain.active_links_mask`, and the result is written back into the full initial
joint vector. SciPy bounds are passed for `trf` and `dogbox`, but not `lm`.
Finite link bounds are honored. Non-finite bounds are replaced by `-2*pi` and
`+2*pi` for the bounded methods; therefore an unbounded link is still
artificially constrained in JAX `trf`/`dogbox` mode.

## JaxKinematicsCache methods

```python
JaxKinematicsCache(chain, precompile=True)
```

The constructor extracts link parameters, active indices, dtype, and active
bounds. It supports the same link encoding as the JAX extractor: `OriginLink`,
`URDFLink` with `revolute`, `prismatic`, or `fixed` joint type. `DHLink` is
recognized by extraction but cannot be evaluated by
`compute_single_link_matrix`'s four-way JAX switch; do not use it with this
backend.

```python
JaxKinematicsCache.forward_kinematics(
    joints,
    full_kinematics=False,
)
```

Accepts a full-chain vector. With `full_kinematics=False`, returns a NumPy
`(4, 4)` matrix. With `True`, returns a Python list of one NumPy `(4, 4)`
matrix per link.

```python
JaxKinematicsCache.active_to_full(active_joints, initial_position)
JaxKinematicsCache.active_from_full(joints)
```

These use JAX array indexing/update and return JAX arrays. `active_to_full`
replaces values at active indices while preserving inactive values from
`initial_position`; `active_from_full` extracts values selected by the active
mask. The public Chain methods normally handle this conversion for you.

Internally, the cache exposes `_fk_compiled`, `_fk_full_compiled`,
`_ik_residuals`, and `_ik_jacobian` in precompile mode, and `_fk_jit`,
`_fk_full_jit`, plus empty IK maps in lazy mode. These underscore attributes are
implementation details; use identity checks only when diagnosing cache reuse.

## Low-level JAX functions

These functions accept JAX arrays and return JAX arrays. They are not needed
for ordinary Chain use, but document the backend's exact data flow:

```python
extract_chain_parameters(chain) -> dict
```

The returned dictionary has JAX arrays named `origin_translations` (shape
`(n_links, 3)`), `origin_orientations` (`(n_links, 3)`), `rotation_axes`
(`(n_links, 3)`), `translation_axes` (`(n_links, 3)`), `joint_types` (int32
`(n_links,)`), and Python integer `n_links`. Joint type codes are 0 origin,
1 revolute, 2 prismatic, 3 fixed, and 4 DH (the last code is not executable by
the current switch).

```python
compute_single_link_matrix(
    origin_translation,
    origin_orientation,
    rotation_axis,
    translation_axis,
    joint_type,
    joint_param,
) -> jax.Array  # (4, 4)

forward_kinematics_jax(joints, chain_params) -> jax.Array  # (4, 4)
forward_kinematics_full_jax(joints, chain_params) -> jax.Array  # (n_links, 4, 4)
```

`compute_single_link_matrix` accepts joint type codes 0 through 3. It uses
`jax.lax.switch`; all branches must remain JIT-compatible. FK iterates links in
chain order and multiplies homogeneous transforms from left to right.

## JAX geometry signatures

`ikpy.utils.jax_geometry` provides JIT-decorated pure-JAX helpers. Exact
call signatures are:

```python
rx_matrix(theta) -> (3, 3)
ry_matrix(theta) -> (3, 3)
rz_matrix(theta) -> (3, 3)
rotation_matrix(phi, theta, psi) -> (3, 3)
rpy_matrix(roll, pitch, yaw) -> (3, 3)
axis_rotation_matrix(axis, theta) -> (3, 3)
homogeneous_translation_matrix(trans_x, trans_y, trans_z) -> (4, 4)
get_translation_matrix(mu) -> (4, 4)
cartesian_to_homogeneous(cartesian_matrix) -> (4, 4)
cartesian_to_homogeneous_vectors(cartesian_vector) -> (4,)
homogeneous_to_cartesian_vectors(homogeneous_vector) -> (3,)
homogeneous_to_cartesian(homogeneous_matrix) -> (3, 3)
from_transformation_matrix(transformation_matrix) -> (translation, rotation)
to_transformation_matrix(translation, orientation_matrix) -> (4, 4)
compute_link_frame_matrix_revolute(
    origin_translation, origin_orientation, rotation_axis, theta
) -> (4, 4)
compute_link_frame_matrix_prismatic(
    origin_translation, origin_orientation, translation_axis, mu
) -> (4, 4)
compute_link_frame_matrix_fixed(
    origin_translation, origin_orientation
) -> (4, 4)
```

`rotation_matrix(phi, theta, psi)` composes `Rz(phi) @ Rx(theta) @ Rz(psi)`;
`rpy_matrix(roll, pitch, yaw)` composes extrinsic roll/pitch/yaw as
`Rz(yaw) @ Ry(pitch) @ Rx(roll)`. Geometry helpers are differentiable where
JAX's trigonometric and array operations are differentiable.
