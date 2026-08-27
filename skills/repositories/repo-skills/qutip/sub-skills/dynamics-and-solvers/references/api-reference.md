# Dynamics and solver API reference

This subskill covers the time-evolution and steady-state side of QuTiP.

## Solver families

A live signature check in the inspected build shows the core solver entry points as:

```python
mesolve(H, rho0, tlist, c_ops=None, *, e_ops=None, args=None, options=None)
sesolve(H, psi0, tlist, e_ops=None, *, args=None, options=None)
steadystate(A, c_ops=[], *, method='direct', solver=None, **kwargs)
coefficient(base, *, tlist=None, args=None, args_ctypes=None, order=3, compile_opt=None, ...)
```

The main solver choices are:

- `sesolve` for pure-state time evolution.
- `mesolve` for density matrices and collapse operators.
- `mcsolve` and `nm_mcsolve` for trajectory-based methods.
- `steadystate` for stationary solutions.
- `propagator` when you need an explicit evolution operator.
- `correlation_*`, `spectrum`, and `floquet_*` for derived dynamical quantities.

## Time dependence

QuTiP models time dependence with either list-style operators, callable coefficients, or `QobjEvo`.
Use the simplest form that keeps the model readable.

Important helpers:

- `QobjEvo` for compiled or structured time dependence.
- `coefficient` for reusable scalar coefficient objects.
- `CompilationOptions` when you need to control runtime compilation behavior.

## Parallel helpers and options

- `parallel_map`, `serial_map`, `loky_pmap`, and `mpi_pmap` are helper maps, not full solvers.
- `QUTIP_NUM_PROCESSES` can affect worker selection.
- `SolverOptions` and solver-specific `options` objects determine integrator behavior, tolerances, and backend choices.

## Reading the solver surface

If the task is asking "which solver should I use?", read this file first.
If the problem has already moved into bath models, HEOM, or PIQS, switch to the specialized-open-systems subskill.
