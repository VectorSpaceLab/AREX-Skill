# Dynamics and solver troubleshooting

## Solver selection mistakes

- If a pure state is evolving coherently, `sesolve` is usually the right starting point.
- If you have collapse operators or want a density matrix, move to `mesolve`.
- If you only need the stationary state, use `steadystate` instead of running a long trajectory.

## Time dependence

- If a string coefficient does not compile, check that runtime compilation dependencies are installed.
- A temporary `qtcoeff_*.pyx` build is expected when Cython compiles a string coefficient.
- If the coefficient output is complex, keep it as complex; do not coerce it to float unless the physics truly requires a real value.

## Steady-state and solver-option issues

- Solver keyword names can change across SciPy versions; QuTiP handles some of the compatibility differences internally.
- If the steady-state solve is slow or unstable, try a simpler method first before adding preconditioners or alternate solvers.
- MKL acceleration is optional; if it is absent, the SciPy path is still valid.

## Parallel helpers

- `loky_pmap` needs `loky`.
- `mpi_pmap` needs `mpi4py` and a working MPI runtime.
- `parallel_map` and `serial_map` are good fallback checks when extras are missing.
- Do not assume `reduce_func` will short-circuit early on every backend; if early termination matters, verify the behavior against the current QuTiP version before depending on it.

## When the problem is really open-system modeling

If the task is about bath spectral densities, PIQS, HEOM, or transfer-tensor methods, switch to `specialized-open-systems` instead of continuing to widen the solver call.
