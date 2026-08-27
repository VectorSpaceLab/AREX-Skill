# API index

This is a compact map of the QuTiP entry points most people reach for first.
Read the matching subskill for details, edge cases, and longer recipes.

## Quantum objects and algebra

| Entry point | Typical use | Subskill |
| --- | --- | --- |
| `Qobj(arg=None, dims=None, copy=True, superrep=None, isherm=None, isunitary=None, dtype=None)` | Wrap raw arrays as quantum objects | `core-objects` |
| `basis(dimensions, n=None, offset=None, *, dtype=None)` | Create basis kets | `core-objects` |
| `sigmax()`, `sigmay()`, `sigmaz()`, `qeye()`, `destroy()`, `create()` | Common operators | `core-objects` |
| `tensor(*args)` | Tensor product composition | `core-objects` |
| `ket2dm(ket)` | Convert a ket to a density matrix | `core-objects` |
| `measure_observable(state, op, tol=None)` | Projective measurement | `core-objects` |
| `measurement_statistics_observable(state, op, tol=None)` | Measurement probabilities and projections | `core-objects` |
| `fidelity`, `tracedist`, `bures_dist`, `average_gate_fidelity`, `unitarity` | State and channel metrics | `core-objects` |
| `qsave(data, filename)` / `qload(filename)` | Serialize QuTiP objects | `analysis-and-io` |

## Dynamics and solver surface

| Entry point | Typical use | Subskill |
| --- | --- | --- |
| `mesolve(H, rho0, tlist, c_ops=None, *, e_ops=None, args=None, options=None)` | Lindblad master-equation evolution | `dynamics-and-solvers` |
| `sesolve(H, psi0, tlist, e_ops=None, *, args=None, options=None)` | Schrödinger evolution | `dynamics-and-solvers` |
| `mcsolve(...)`, `nm_mcsolve(...)`, `ssesolve(...)`, `smesolve(...)` | Trajectory and stochastic solvers | `dynamics-and-solvers` |
| `steadystate(A, c_ops=[], *, method='direct', solver=None, **kwargs)` | Steady-state solutions | `dynamics-and-solvers` |
| `coefficient(base, *, tlist=None, args=None, order=3, compile_opt=None, ...)` | Time-dependent coefficients | `dynamics-and-solvers` |
| `propagator(...)`, `correlation_*`, `spectrum(...)`, `floquet_*` | Propagators, correlations, spectra, Floquet analysis | `dynamics-and-solvers` |
| `parallel_map`, `serial_map`, `loky_pmap`, `mpi_pmap` | Parallel helper maps | `dynamics-and-solvers` |

## Specialized open-system models

| Entry point | Typical use | Subskill |
| --- | --- | --- |
| `qutip.core.environment.DrudeLorentzEnvironment(...)` and related environment classes | Spectral densities and bath models | `specialized-open-systems` |
| `qutip.piqs.piqs.Dicke`, `num_dicke_states`, `jspin`, `dicke`, `excited`, `ground` | Permutationally invariant quantum systems | `specialized-open-systems` |
| `qutip.solver.nonmarkov.transfertensor.ttmsolve` | Transfer-tensor non-Markovian dynamics | `specialized-open-systems` |
| `brmesolve(...)` | Bloch-Redfield dynamics | `specialized-open-systems` |
| `heom/*` solvers and baths | Hierarchical equations of motion | `specialized-open-systems` |

## Visualization and analysis

| Entry point | Typical use | Subskill |
| --- | --- | --- |
| `Bloch(...)` | Bloch-sphere rendering | `analysis-and-io` |
| `hinton(...)`, `matrix_histogram(...)`, `plot_fock_distribution(...)` | Matrix and state visualizations | `analysis-and-io` |
| `plot_wigner(...)`, `wigner(...)`, `qfunc(...)`, `spin_wigner(...)` | Quasi-probability plots | `analysis-and-io` |
| `plot_expectation_values(...)`, `plot_energy_levels(...)`, `plot_qubism(...)` | Result summaries and specialized plots | `analysis-and-io` |
| `tomography.qpt(...)`, `qpt_plot(...)` | Process-tomography workflows | `analysis-and-io` |
| `about()`, `cite()` | Environment and citation helpers | `analysis-and-io` |

## Inspection helpers

When a workflow feels ambiguous, confirm the live signature in the active environment with `inspect.signature(...)`, then follow the matching subskill.
