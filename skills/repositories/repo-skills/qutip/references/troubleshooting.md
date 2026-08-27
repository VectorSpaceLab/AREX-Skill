# Troubleshooting

## Install and import problems

- If `import qutip` fails, check that the package is installed in the active environment, not only present in a source checkout.
- Run `python -m pip check` to catch version conflicts.
- Use `qutip.about()` for a fast summary of NumPy, SciPy, Matplotlib, Cython, CPU count, and MKL detection.
- If `qutip.about()` prints no Matplotlib version, install `matplotlib` before using the plotting helpers.

## Source builds and runtime compilation

- String-based time-dependent coefficients use Cython compilation and a small on-disk cache.
- If coefficient compilation fails, confirm that `cython`, `filelock`, `setuptools`, and `wheel` are installed.
- If you see a temporary `qtcoeff_*.pyx` build, that is normal; it means the coefficient was compiled at runtime.
- Clear or relocate the coefficient cache through `qutip.settings.compile` and `qutip.settings.tmproot` when the default cache location is not writable.

## Solver and data-shape errors

- `Qobj` dimension mismatches usually mean the state, Hamiltonian, or collapse operators were built with inconsistent tensor structure.
- If a measurement helper says the operators and state are incompatible, rebuild the operator list so all projectors or observables share the same Hilbert-space dimensions.
- `steadystate` and the time-evolution solvers often need the same basic physics object, but they use different entry points; do not pass a density matrix where a Liouvillian is expected unless the docstring says so.
- SciPy keyword changes can matter. QuTiP has compatibility handling for solver options that changed across SciPy releases.

## Parallel helpers

- `parallel_map` works without extras, but `loky_pmap` needs `loky` and `mpi_pmap` needs `mpi4py` plus a working MPI runtime.
- If parallel execution behaves oddly, compare the result against `serial_map` first.
- Set `QUTIP_NUM_PROCESSES` or use the solver options if you need to pin the worker count.

## Plotting and visualization

- In headless environments, set the Matplotlib backend to `Agg` before importing or calling plotting helpers.
- `hinton` and other matrix plots expect consistent basis labels; errors such as `got 1 ticklabels but needed 5` usually mean the basis vector list length is wrong.
- Hinton plots of superoperators are limited; if you hit a qubit-only limitation, confirm that the object really is a superoperator on qubits.
- Bloch-sphere arc helpers reject degenerate geometry, such as identical start and end points or points on different spheres.

## Serialization and I/O

- `qsave` appends its own `.qu` suffix.
- Use a temporary directory for round-trip tests so you do not leave artifacts behind.
- If `qload` cannot open a saved object, confirm that the file was written by the same QuTiP family and that the path includes the automatically appended suffix.

## Optional backends and extras

- `qutip.qip` is not bundled in this repository; it requires the external `qutip-qip` package.
- `dnorm` may need `cvxpy` and `cvxopt` for the semidefinite path.
- MKL acceleration is optional. If it is absent, the CPU/SciPy path is still valid.
- OpenMP support is disabled in this source tree, so there is no OpenMP-specific runtime path to debug.

## When to stop and inspect further

If a failure is not obviously one of the cases above, inspect the live signature in the active environment and then read the matching subskill reference before changing the physics model or solver choice.
