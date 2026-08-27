# JAX backend troubleshooting

## JAX is missing or partially installed

**Symptom:** `ikpy.JAX_AVAILABLE` is `False`, or accessing
`chain.jax_cache` raises an import error.

**Checks:**

```bash
python -m pip show ikpy jax jaxlib scipy
python -c "import sys; print(sys.executable)"
python -c "import ikpy; print(ikpy.JAX_AVAILABLE)"
```

Install the optional extra into the interpreter shown by `sys.executable`:

```bash
python -m pip install 'ikpy[jax]'
```

`jax` and `jaxlib` are optional; a base `pip install ikpy` is expected to work
without them and should use the NumPy backend. Do not make production code
silently switch to JAX after catching every import error: report the missing
optional capability or intentionally choose `backend="numpy"`.

If importing JAX fails due to an incompatible wheel, Python version, or platform,
repair the environment using the JAX installation appropriate for that
platform. IKPy's `jax` extra expresses the dependency, but cannot select a
compatible CUDA plugin for every machine.

## CUDA versus CPU confusion

**Symptom:** a benchmark says “JAX is installed” but no GPU is used, or a CUDA
error appears on a CPU-only host.

`jax`/`jaxlib` do not mean that IKPy guarantees CUDA acceleration. The backend
works on CPU JAX, and all examples and smoke checks must be valid without a
GPU. Inspect the actual runtime:

```python
import jax
print(jax.default_backend())
print(jax.devices())
```

For a safe CPU run, set `JAX_PLATFORMS=cpu` before importing JAX. Do not claim
GPU support from a CPU result. If a CUDA device is desired, validate JAX's
installed accelerator runtime independently, then benchmark after warm-up;
IKPy itself does not install or guarantee the CUDA plugin.

## Compilation is slow or first call is unexpectedly slow

**Cause:** with the default `jax_precompile=True`, first access to
`chain.jax_cache` AOT-compiles FK, full FK, and all valid orientation/position
IK residual/Jacobian pairs. With `False`, the first FK or first new IK variant
compiles lazily.

Choose deliberately:

- `jax_precompile=True`: pay at startup, avoid compilation on the first
  service request, and reuse the cache for the same chain.
- `jax_precompile=False`: cheap setup, but the first operation pays JIT cost and
  each new lazy IK mode can compile when first used.

Warm up the exact operation and solver mode before measuring steady-state
latency. A new chain, changed input shape, changed dtype, or changed static
configuration can trigger another JAX compilation. The cache is in-memory and
not a persistent on-disk compilation cache.

Do not reduce correctness tolerances to hide a compile delay. Bound
`scipy_max_nfev` for a smoke check and separate compile time from solve time.

## Precision, dtype, and parity errors

**Symptom:** NumPy/JAX FK differs more than expected, or IK is sensitive to
small changes.

`JaxKinematicsCache` selects `jnp.float64` only when
`jax.config.jax_enable_x64` is true at cache creation; otherwise it uses
`jnp.float32`. JAX commonly warns or truncates requested float64 values when
x64 is disabled. Enable x64 before importing/initializing the JAX cache when
higher precision is necessary:

```bash
JAX_ENABLE_X64=True JAX_PLATFORMS=cpu python your_program.py
```

Alternatively configure JAX at the very beginning of the process, before the
first cache is created. Rebuild the Chain/cache after changing precision; an
existing cache keeps its selected dtype.

The repository's expected FK parity baseline is:

```python
np.testing.assert_allclose(jax_fk, numpy_fk, rtol=1e-5, atol=1e-5)
```

Use a non-zero joint test as well as the zero configuration. If the mismatch is
small but accumulates in a long chain, compare each full intermediate frame to
localize the link. If it is large, check units (radians/meters), axes, origin
RPY values, active masks, and whether the model contains a DH/custom link.

For IK, compare achieved FK target error and orientation residual, not exact
joint arrays. Analytical and finite-difference solves can select different
valid configurations.

## Unsupported link types or unexpected kinematics

JAX parameter extraction supports:

- `OriginLink`;
- `URDFLink` with `joint_type="revolute"`, `"prismatic"`, or `"fixed"`.

Unknown link classes raise `ValueError`. `DHLink` is labeled during parameter
extraction but is not executable in the current four-way
`jax.lax.switch` used by `compute_single_link_matrix`; do not represent DH
chains as JAX-supported. Use the NumPy backend for DH or convert the chain to a
supported URDF-style model through **robot-model-import**.

The JAX geometry path uses URDF origin translation/orientation and rotation or
translation axes. A custom link's NumPy `get_link_frame_matrix` implementation
is not automatically used by the JAX backend. Run NumPy/JAX full-FK parity
before enabling JAX IK.

## Solver kwargs rejected or ineffective

**Symptom:** SciPy reports an invalid option, an unexpected method/loss error,
or the option appears ignored.

Use only the names in the JAX signature:
`tol`, `use_analytical_jacobian`, `scipy_method`, `scipy_x_scale`,
`scipy_loss`, `scipy_gtol`, `scipy_max_nfev`, `scipy_tr_solver`,
`scipy_tr_options`, and `scipy_verbose`, plus `orientation_mode` and
`no_position` where applicable.

Important forwarding rules:

- `tol` becomes both SciPy `ftol` and `xtol`; it does not set `gtol`.
  Supply `scipy_gtol` separately when needed.
- `scipy_method` must be `trf`, `dogbox`, or `lm` for the documented route.
  `lm` cannot use bounds, and SciPy's `lm` has restrictions on residual size
  and non-linear losses.
- `scipy_tr_solver` and `scipy_tr_options` are forwarded only for `trf` and
  `dogbox`; they do not configure `lm`.
- `scipy_x_scale="jac"` is the repository default. Use `None` to omit the
  kwarg or an array-like scale with the correct active-variable length.
- `scipy_loss` is passed through to SciPy. The documented choices are
  `linear`, `soft_l1`, `huber`, `cauchy`, and `arctan`; method-specific SciPy
  restrictions still apply.
- `scipy_verbose` is a SciPy verbosity value, normally 0, 1, or 2; keep it at
  0 for machine-readable smoke output.
- `use_analytical_jacobian=False` does not make JAX disappear: JAX still
  computes residuals, while SciPy estimates the Jacobian by finite differences.

Do not pass generic NumPy inverse-kinematics names such as
`starting_nodes_angles` to the JAX path and expect them to be translated.
`Chain.inverse_kinematics_frame` always validates the target as a 4x4 array.

## Bounds and active masks

**Symptom:** a solution stops at an unexpected limit or `least_squares` reports
an infeasible starting point.

The cache stores bounds only for active links. Finite `link.bounds` values are
passed to SciPy for `trf` and `dogbox`. Non-finite values are replaced with
`-2*pi` and `+2*pi`, so the JAX bounded route is not truly unbounded. `lm`
omits bounds altogether.

The starting position must be full-chain length. Active values seed SciPy;
inactive values remain from `initial_position`, and the returned result is full
length. Ensure every active initial value lies within the effective bounded
interval. If necessary, use `lm` only when unconstrained behavior is acceptable,
or fix the model's link bounds and recreate the cache.

A target can be unreachable even when the solver terminates successfully. Check
`np.linalg.norm(fk[:3, 3] - target_position)` and the requested orientation
residual. A low optimizer termination status is not an accuracy guarantee.

## Cache is stale, missing expected variants, or memory is high

The cache belongs to one Chain instance and is created once:

```python
cache_a = chain.jax_cache
cache_b = chain.jax_cache
assert cache_a is cache_b
```

If `jax_precompile=True`, `_fk_compiled` and `_fk_full_compiled` are populated,
and `_ik_residuals`/`_ik_jacobian` contain these valid keys:

```text
(None, False)
("X", False), ("X", True)
("Y", False), ("Y", True)
("Z", False), ("Z", True)
("all", False), ("all", True)
```

`(None, True)` is intentionally absent because it is an empty objective. In
lazy mode, FK compiled handles are `None` and JIT wrappers are present; IK
variants are compiled on demand.

High precompile cost or memory usage is expected for long chains because every
valid orientation/position combination receives a residual and Jacobian
program. Prefer lazy mode when only one mode is needed, or precompile once in a
long-lived process. If chain structure, active mask, link bounds, dtype, or JAX
configuration changes, use a newly constructed Chain rather than relying on an
old cache.

## Bad IK result or apparent local minimum

The JAX analytical Jacobian improves derivative quality but does not make IK
globally optimal. Check these in order:

1. Verify NumPy/JAX FK parity at the initial position.
2. Verify target frame shape, units, axes, and reachable workspace.
3. Use a meaningful `initial_position`; for trajectories, warm-start from the
   preceding successful full solution.
4. Try `scipy_x_scale="jac"` and a bounded finite `scipy_max_nfev`.
5. Compare `use_analytical_jacobian=True` with finite differences.
6. Try `dogbox` for bound-sensitive cases or `lsmr` with
   `scipy_tr_options={"regularize": True}` for an ill-conditioned `trf`
   problem.

Keep the achieved residual in logs. Changing method, warm start, or loss can
change the valid joint branch even when the end-effector pose is equivalent.
