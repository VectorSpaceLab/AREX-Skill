---
name: numpy-scipy-primitives
description: "Routes autograd.numpy and autograd.scipy wrapper behavior,
  supported and unsupported NumPy patterns, complex numbers, xarray
  interoperability, and SciPy-extra troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# NumPy and SciPy Primitives

Use this sub-skill when the user asks about `autograd.numpy` or `autograd.scipy` behavior rather than about core derivative operators or custom rules. It is the right place for wrapper support questions, xarray `__array_ufunc__` interop, and public limitations around NumPy/SciPy patterns.

## Route here for

- `autograd.numpy` wrapper behavior, supported NumPy calls, and common array-construction helpers.
- `autograd.numpy.linalg` and `autograd.numpy.fft` behavior, including complex-number support and known shape/axis limits.
- `autograd.scipy.special`, `signal`, `linalg`, `integrate`, and `stats` wrappers, including `logsumexp`.
- NumPy containers or array-like objects that implement `__array_ufunc__`, especially `xarray.DataArray`.
- Troubleshooting whether a failure is a missing optional dependency or an unsupported wrapper pattern.

## Route elsewhere for

- `grad`, `jacobian`, `value_and_grad`, `make_vjp`, `make_jvp`, Hessians, and other core derivative operators: [differentiation-core](../differentiation-core/SKILL.md).
- New primitives, custom VJPs/JVPs, or wrapper authoring: [extend-primitives](../extend-primitives/SKILL.md).

## Read first

- [API reference](references/api-reference.md)
- [Workflow recipes](references/workflows.md)
- [Troubleshooting](references/troubleshooting.md)

## Safe helper

Run the bundled wrapper smoke helper from this sub-skill directory or any shell that can resolve the script path:

```bash
python scripts/wrappers_smoke.py
python scripts/wrappers_smoke.py --simulate-missing scipy
python scripts/wrappers_smoke.py --simulate-missing xarray
```

The helper uses tiny in-memory arrays only. It does not download data or require network access. When SciPy or xarray are absent, it prints a clear skip message with the suggested install step instead of failing immediately.

## Core rules

1. Prefer `autograd.numpy` for user-facing array code. Keep the final result scalar before calling differentiation operators from the core sub-skill.
2. Use `np.dot`, `np.matmul`, or `np.tensordot`; do not rely on the `A.dot(B)` method form.
3. Do not mutate differentiable arrays in place. Rewrite assignments and `+=` style updates as pure expressions.
4. When a primitive takes a list or tuple, build an explicit array first with `np.array(...)` unless the wrapper already documents a safe list path.
5. For container checks on boxed values, use the Autograd builtins versions of `isinstance` and `tuple` when needed.
6. `xarray.DataArray` and other `__array_ufunc__` containers can carry boxed values through NumPy ufuncs. Keep the container during the ufunc step, then reduce to a plain scalar with `.data` or an equivalent extraction at the end.
7. `autograd.scipy` requires SciPy. If the import is missing, install `autograd[scipy]` or `scipy` itself.
8. Complex numbers are supported, but non-holomorphic questions and low-level derivative semantics belong in the differentiation-core route.
9. Some matrix norms, repeated-axis FFT gradients, and odd-length real FFT gradient paths are unsupported. Treat `NotImplementedError` as a limitation signal, not a bug in the wrapper layer.

## What this sub-skill does not do

- It does not teach custom primitive authoring or gradient-rule registration.
- It does not explain the full derivative-operator API surface.
