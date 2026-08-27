---
name: jax-backend
description: "Use IKPy's optional JAX backend for CPU-safe JIT/AOT forward
  kinematics, autodiff Jacobians, and bounded SciPy inverse kinematics, with
  NumPy parity checks and explicit compilation and precision tradeoffs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# IKPy JAX backend

Use this sub-skill when an already-constructed IKPy `Chain` needs JAX-backed FK
or IK. Install the optional extra first; JAX is not a base dependency and this
skill never promises GPU acceleration.

## Operating route

1. Install `ikpy[jax]` and verify `ikpy.JAX_AVAILABLE` in the same Python
   environment that will run the chain.
2. Obtain the chain through **robot-model-import**. JAX dispatch is intended for
   `OriginLink` and `URDFLink` chains (revolute, prismatic, or fixed); route
   general chain construction and semantics to **chain-kinematics**.
3. Choose `jax_precompile=True` for predictable first-use latency or `False`
   for cheap cache creation and lazy first-call compilation. Run FK once and
   compare it with NumPy before using JAX IK.
4. Call `Chain.forward_kinematics(..., backend="jax")` or
   `Chain.inverse_kinematics(..., backend="jax")`. For a trajectory, pass the
   previous full solution as `initial_position`.
5. Read the linked references for exact signatures, solver kwargs, supported
   orientation modes, bounds, cache lifecycle, and failure recovery.

## Hard rules

- `jax` and `jaxlib` arrive through the optional `jax` extra:
  `python -m pip install 'ikpy[jax]'`.
- CPU JAX proves only CPU execution. The package does not guarantee CUDA,
  accelerator plugins, or a GPU speedup. An explicit `JAX_PLATFORMS=cpu` run is
  the safe baseline.
- The first JAX use can compile the cache. AOT/precompile trades longer cache
  creation for a faster first call; lazy mode moves compilation to the first
  operation. Neither mode persists a compiled binary across processes.
- Verify NumPy/JAX FK with `rtol=1e-5, atol=1e-5` (the repository's JAX tests'
  baseline) before trusting a result. Use x64 only when configured before JAX
  and cache creation.
- `DHLink` is not a supported JAX execution path: extraction labels it as a
  separate type, but the JAX dispatch switch has no DH case. Unknown custom
  link classes raise `ValueError`. Use NumPy or convert the model through the
  appropriate importer.
- Route robot loading to **robot-model-import**, general IK behavior to
  **chain-kinematics**, and plotting to **visualization-geometry**.

## References

- [API reference](references/api-reference.md) — public dispatch, cache, IK
  kwargs, low-level JAX functions, and geometry signatures.
- [Workflows](references/workflows.md) — installation, CPU-safe setup, parity,
  compilation choices, precompile/lazy use, and warm-start trajectories.
- [Troubleshooting](references/troubleshooting.md) — missing optional
  dependencies, precision, unsupported links, bounds, solver settings, and
  cache reuse.

The bundled `scripts/smoke_jax.py` is a deterministic, inline-chain smoke
check. It supports `--help`, exits cleanly when JAX is absent, checks NumPy/JAX
FK parity, and can run bounded JAX IK with `--ik` without requiring a GPU.
