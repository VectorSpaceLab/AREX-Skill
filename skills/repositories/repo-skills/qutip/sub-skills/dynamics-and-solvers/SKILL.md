---
name: "dynamics-and-solvers"
description: "QuTiP time-evolution, steady-state, time-dependent coefficient,
  and solver workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# Dynamics and solvers

Use this subskill when the task is about evolving states, solving master equations, computing steady states, building time-dependent coefficients, or choosing among QuTiP's solver families.

## Read this subskill when the prompt mentions

- `sesolve`, `mesolve`, `mcsolve`, `nm_mcsolve`, `ssesolve`, `smesolve`
- `steadystate`, `propagator`, `correlation`, `spectrum`, `floquet`
- `QobjEvo`, `coefficient`, string coefficients, or runtime-compiled coefficients
- `parallel_map`, `serial_map`, `loky_pmap`, `mpi_pmap`
- solver options, `QUTIP_NUM_PROCESSES`, integrators, or time-dependent Hamiltonians and collapse operators

## What to decide first

1. Is the system pure-state or density-matrix based?
2. Is the task time evolution, steady state, or a derived quantity such as a spectrum or correlation?
3. Is the Hamiltonian time-independent, list-form, or built with `QobjEvo` or `coefficient`?
4. Does the task need optional parallel helpers or accelerated steady-state backends?

## Core workflow

- Start with the simplest solver that matches the physics: `sesolve` for pure states, `mesolve` for density matrices, `steadystate` for stationary solutions.
- Add collapse operators only when the model is open.
- Use `QobjEvo` or `coefficient` when the model has explicit time dependence.
- Check solver options and expected data types before increasing model size.
- If the task moves into PIQS, HEOM, transfer-tensor, or bath-model construction, hand it to `specialized-open-systems`.

## Typical success signals

- The solver returns the expected `Result` or state object.
- Observables have the expected time-series length.
- Time-dependent coefficients evaluate numerically in the active environment.
- Optional parallel helpers fall back cleanly when extras are absent.

## Boundaries

Use this subskill for solver mechanics and ordinary dynamics. Do not use it as the main route for:

- Basic `Qobj` construction or tensor algebra before the model exists; start in `core-objects`.
- PIQS, HEOM, transfer-tensor, or explicit bath/environment model design; switch to `specialized-open-systems`.
- Plotting or saving the solver result; switch to `analysis-and-io` after the solve.

## Answer shape

When responding from this subskill, give:

1. The solver choice and why it matches the physics.
2. The expected forms of `H`, initial state, `tlist`, `c_ops`, `e_ops`, and `args`.
3. A minimal executable code snippet.
4. The validation signal, such as expectation-vector length, trace, or coefficient value.
5. The optional dependency or backend note when the route uses Cython, Loky, MPI, or MKL.

## Validation hints

- Start with a two-level or tiny Hilbert-space example before scaling up.
- Check that time-dependent arguments are passed consistently through `args`.
- Compare against `serial_map` or a one-worker map when debugging parallel helpers.

## Reference files

- `references/api-reference.md` for solver families, signatures, and the main option families.
- `references/workflows.md` for small end-to-end evolution and steady-state recipes.
- `references/troubleshooting.md` for coefficient compilation, solver-option, and backend issues.

## Helper script

- `scripts/solver_smoke.py` runs a tiny evolution, steady-state, coefficient, and parallel-map smoke check.
