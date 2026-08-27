# JAX backend workflows

The examples below use an existing `Chain` named `chain`. Obtain that chain
through **robot-model-import** and follow **chain-kinematics** for model and
IK semantics. They deliberately use ordinary NumPy-compatible inputs and do
not require a GPU.

## 1. Install and select a safe CPU runtime

JAX is optional in IKPy 4.0.0. Install the extra in the environment that owns
both IKPy and SciPy:

```bash
python -m pip install 'ikpy[jax]'
```

For a deterministic CPU smoke run, select CPU before importing JAX:

```bash
JAX_PLATFORMS=cpu python - <<'PY'
import ikpy
import jax
print("available:", ikpy.JAX_AVAILABLE)
print("backend:", jax.default_backend())
print("devices:", jax.devices())
PY
```

On Windows PowerShell, use `$env:JAX_PLATFORMS = "cpu"` before starting
Python. If the optional packages are absent, keep the regular NumPy backend
rather than catching and hiding a partially installed JAX environment:

```python
import ikpy
if not ikpy.JAX_AVAILABLE:
    raise RuntimeError("Install with: python -m pip install 'ikpy[jax]'")
```

JAX chooses devices according to its own installation and configuration. A
visible GPU in another environment is not evidence that this IKPy install has
CUDA support. Treat GPU execution as optional and unverified unless the
specific JAX runtime reports a working device.

## 2. NumPy/JAX FK parity before IK

Start with a full-length joint vector. Inactive joints and the origin link still
need entries:

```python
import numpy as np

joints = np.zeros(len(chain.links), dtype=float)
fk_numpy = chain.forward_kinematics(joints, backend="numpy")
fk_jax = chain.forward_kinematics(joints, backend="jax")
np.testing.assert_allclose(fk_jax, fk_numpy, rtol=1e-5, atol=1e-5)

full_numpy = chain.forward_kinematics(joints, full_kinematics=True, backend="numpy")
full_jax = chain.forward_kinematics(joints, full_kinematics=True, backend="jax")
assert len(full_numpy) == len(full_jax) == len(chain.links)
for numpy_frame, jax_frame in zip(full_numpy, full_jax):
    np.testing.assert_allclose(jax_frame, numpy_frame, rtol=1e-5, atol=1e-5)
```

Repeat with at least one non-zero revolute value and one prismatic value when
the model has them. A mismatch usually indicates a model/link representation
problem, an unsupported link class, or a dtype/tolerance issue—not a reason to
silently loosen tolerances.

## 3. First-call compilation and reuse

Default chain construction uses `jax_precompile=True`:

```python
chain = Chain.from_urdf_file(
    "robot.urdf",
    base_elements=["base_link"],
    jax_precompile=True,
)
# The cache and its AOT programs are built at this first JAX access.
first = chain.forward_kinematics(joints, backend="jax")
second = chain.forward_kinematics(joints, backend="jax")
```

The JAX cache is lazy at the Chain object level (`chain._jax_cache` starts as
`None`) but precompiles its programs when `chain.jax_cache` is first requested.
The first access can therefore be substantially slower and use additional
memory. Subsequent calls with the same static chain shape reuse the compiled
functions.

Do not benchmark the first call as steady-state performance. Synchronize an
array result if measuring JAX execution in a lower-level benchmark, because
JAX operations may be asynchronous on accelerators. IKPy converts its public
results to NumPy, but compilation remains part of the first-call cost.

## 4. Precompile versus lazy compilation

Use precompile when a long-lived process can pay startup cost before serving a
latency-sensitive request:

```python
precompiled_chain = Chain.from_urdf_file(
    "robot.urdf", base_elements=["base_link"], jax_precompile=True
)
_ = precompiled_chain.jax_cache  # explicit startup boundary
```

Precompile uses `jax.jit(...).lower(...).compile()` for endpoint FK, full FK,
and all valid `(orientation_mode, no_position)` IK residual/Jacobian variants.
This makes the first actual call predictable, but cache creation can be
expensive.

Use lazy mode when chain setup should be cheap or only a subset of operations is
needed:

```python
lazy_chain = Chain.from_urdf_file(
    "robot.urdf", base_elements=["base_link"], jax_precompile=False
)
# Cache creation is cheap; this call pays the FK JIT compilation cost.
_ = lazy_chain.forward_kinematics(joints, backend="jax")
```

Lazy mode still JIT-compiles the FK functions when first called. Lazy IK
variants are compiled on demand when an orientation/position combination is
first requested. Neither mode should be described as persistent disk caching
or as compilation-free execution.

A chain's cache is reused by identity:

```python
assert chain.jax_cache is chain.jax_cache
```

If link values, link count, active mask, bounds, or representation change after
cache creation, construct a new Chain (or clear its private cache and recreate
it under controlled application code). Never share a cache between different
chains.

## 5. Position IK with explicit limits

The shortest JAX route is position-only IK:

```python
solution = chain.inverse_kinematics(
    target_position=np.asarray([0.50, 0.20, 0.30]),
    backend="jax",
    scipy_method="trf",
    scipy_x_scale="jac",
    scipy_max_nfev=100,
)
pose = chain.forward_kinematics(solution, backend="jax")
position_error = np.linalg.norm(pose[:3, 3] - [0.50, 0.20, 0.30])
assert position_error < 1e-2
```

`trf` and `dogbox` use the active link bounds. For a link with non-finite
bounds, IKPy substitutes `[-2*pi, +2*pi]` in the JAX bounded solve. `lm` omits
bounds and is therefore not an equivalent constrained solve. A target outside
the reachable workspace can terminate with a non-zero residual; always compute
and report the achieved error.

## 6. Orientation modes and frame IK

Use a target orientation with the mode it describes:

```python
identity = np.eye(4)
identity[:3, 3] = [0.50, 0.20, 0.30]

# Position plus one axis:
solution_z = chain.inverse_kinematics_frame(
    identity,
    initial_position=np.zeros(len(chain.links)),
    backend="jax",
    orientation_mode="Z",
    no_position=False,
)

# Full rotation block and position:
solution_all = chain.inverse_kinematics_frame(
    identity,
    initial_position=np.zeros(len(chain.links)),
    backend="jax",
    orientation_mode="all",
)
```

The valid modes are `None`, `"X"`, `"Y"`, `"Z"`, and `"all"`. `None` with
`no_position=True` is invalid because it leaves no residual. A complete
rotation target should be a valid rotation matrix; IKPy compares frame columns
or the flattened full `3 x 3` block, rather than applying a special angular
wrap-around metric.

For the high-level method, provide `target_orientation` as a 3-vector for
`"X"`, `"Y"`, or `"Z"`, and as a `3 x 3` matrix for `"all"`.

## 7. Analytical Jacobian versus finite differences

The default uses JAX forward-mode autodiff and passes the resulting analytical
Jacobian to SciPy:

```python
analytic = chain.inverse_kinematics(
    target_position=target_position,
    initial_position=initial_position,
    backend="jax",
    use_analytical_jacobian=True,
)
```

To compare against SciPy finite differences, omit `jac` by setting the switch
false:

```python
finite_difference = chain.inverse_kinematics(
    target_position=target_position,
    initial_position=initial_position,
    backend="jax",
    use_analytical_jacobian=False,
)
```

Compare each result by FK and residual, not by requiring identical joint
vectors; redundant chains can have multiple valid solutions. The repository's
JAX tests use a position error below `0.01` for representative targets and
`rtol=1e-5, atol=1e-5` for FK parity. Keep `scipy_max_nfev` bounded in tests or
interactive services.

## 8. Warm-started trajectory tracking

Use the prior **full** solution as the next initial position. Preserve the
active/inactive layout:

```python
current_joints = np.zeros(len(chain.links), dtype=float)
for target in trajectory:
    result = chain.inverse_kinematics(
        target_position=np.asarray(target, dtype=float),
        initial_position=current_joints,
        backend="jax",
        scipy_method="trf",
        scipy_x_scale="jac",
        scipy_max_nfev=75,
    )
    fk = chain.forward_kinematics(result, backend="jax")
    error = np.linalg.norm(fk[:3, 3] - target)
    if error >= 1e-2:
        raise RuntimeError(f"unmet waypoint: {error}")
    current_joints = result
```

Warm starts often reduce iterations and help maintain a continuous branch, but
they do not guarantee the globally nearest or unique solution. A cold start is
`initial_position=None` (zero vector). If a waypoint is difficult, retain the
last successful solution, reduce the waypoint step, or use a bounded finite
`scipy_max_nfev`; do not assume a failed solve is a compilation failure.

## 9. Safe CPU example

This is the minimal operational pattern:

```python
import os
os.environ.setdefault("JAX_PLATFORMS", "cpu")  # before importing jax/ikpy

import numpy as np
import ikpy
from ikpy.chain import Chain

if not ikpy.JAX_AVAILABLE:
    raise ImportError("Install the optional dependency with pip install 'ikpy[jax]'")

chain = Chain.from_urdf_file("robot.urdf", jax_precompile=False)
q = np.zeros(len(chain.links))
np.testing.assert_allclose(
    chain.forward_kinematics(q, backend="jax"),
    chain.forward_kinematics(q, backend="numpy"),
    rtol=1e-5,
    atol=1e-5,
)
```

Setting `JAX_PLATFORMS=cpu` is a reproducible CPU choice, not a claim that
other platforms are unsupported. Remove it only when the installed JAX runtime
and any CUDA/plugin dependencies have been explicitly validated.
