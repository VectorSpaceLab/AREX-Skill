# Analysis troubleshooting

Use this table before increasing a dimension, solver budget, or generator count.
The intended recovery is to validate the public contract and keep the workflow
bounded.

## Install and import

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: openfermion` | The package is not installed in the active runtime or the runtime is not the one used for the analysis. | Install the compatible OpenFermion distribution in the intended environment, then run `python -c "import openfermion, scipy; print(openfermion.__version__)"`. Do not diagnose from a checkout import. |
| Import of `openfermion.linalg` fails on SciPy symbols | NumPy/SciPy versions are incompatible or SciPy is missing. | Install the package's supported core dependencies together; verify `import numpy, scipy` before retrying. Keep the sparse/eigensolver route disabled until both import. |
| `openfermion.measurements.vpe_estimators` fails on `cirq` | The VPE helper imports Cirq and the optional circuit stack is unavailable or incompatible. | Install a compatible Cirq core dependency or route circuit/VPE circuit creation to the circuit skill. Do not replace the missing dependency with a fake result for a production estimate. |
| RDM data loading fails on HDF5-related imports | A molecule/data-file workflow is being mixed into a pure tensor map, or its data dependency is absent. | Keep pure NumPy RDM maps in this route. For molecule-backed RDMs, use the chemistry route and install its documented data dependencies. |

## Optional dependency and backend boundaries

| Symptom | Likely cause | Recovery |
|---|---|---|
| A sparse matrix operation tries to allocate an unexpectedly large object | `2**n_qubits` or `trunc**n_modes` was not bounded; sparse storage does not make the Hilbert dimension free. | Print the planned dimension before conversion. Reduce the problem, use a symmetry-sector matrix, a `LinearQubitOperator`, or stop with a resource estimate. |
| A user expects GPU acceleration from `eigsh`/Davidson | These APIs use the SciPy/NumPy CPU path; no GPU backend is implied by a sparse matrix. | Report the CPU numerical result only. Route a backend-specific implementation elsewhere and do not claim GPU coverage from this skill. |
| Parallel `LinearQubitOperator` creates processes or hangs | A multiprocessing implementation was selected without a process budget or safe runtime start method. | Use the serial `LinearQubitOperator`/`QubitDavidson` for bounded work. Only enable parallel options after explicitly budgeting processes and validating the host runtime. |
| A VPE phase estimate has no usable samples | The circuit/result backend is not available, or the result object is not a Cirq-compatible measurement result. | Stop at the numerical boundary, verify the circuit workflow separately, and require a result sequence containing the expected `msmt` data before fitting. |

## Shape, tensor, and configuration validation

| Symptom | Likely cause | Recovery |
|---|---|---|
| `get_sparse_operator(..., n_qubits=k)` raises `Invalid number of qubits specified` | A term references a qubit at or above `k`. | Set `n_qubits` to at least one more than the highest referenced qubit, or intentionally remove the term. Never use a smaller value to truncate an operator. |
| Matrix shape is not `(2**n, 2**n)` | The qubit/mode count was inferred from the wrong object, or a restricted-sector matrix was mistaken for a full Hilbert matrix. | Record whether the matrix is full or sector-restricted. For a full matrix pass `n_qubits`; for a sector matrix record the selected indices and compare against the binomial sector size. |
| `IndexError`, broadcasting error, or a numerically plausible but wrong RDM | OPDM/TPDM/PHDM axes have incompatible ranks, dimensions, or index order. | Require OPDM `(m,m)`, TPDM/PHDM `(m,m,m,m)` before mapping. Preserve the conventions `opdm[p,q]=<a_p†a_q>` and `tpdm[p,q,r,s]=<a_p†a_q†a_r a_s>`. Test a round trip and trace. |
| `NaN`, `inf`, or divide-by-zero in `map_two_pdm_to_one_pdm` or a hole contraction | `particle_number == 1` or `hole_number == 1`, or normalization does not match the supplied count. | Check the count before calling. Obtain the correct normalization from the state/RDM producer; do not patch the denominator after the fact. |
| `ValueError` from `map_particle_hole_dm_to_one_pdm` | `num_particles > num_basis_functions`. | Correct the metadata or stop: a particle count exceeding the basis is physically and algebraically invalid for this map. |
| One-norm result changes unexpectedly when switching APIs | The constant term was included in one call and omitted in the other, or integral axes are not spatial-orbital tensors. | Use `get_one_norm_int` only with the intended constant and `get_one_norm_int_woconst` only when it is intentionally excluded. Validate `(n,n)` and `(n,n,n,n)` shapes and matching `n`. |
| `Grid` raises `ValueError` at construction or `OrbitalSpecificationError` at lookup | Dimensions/length/scale types are invalid, a coordinate is outside `[0,length)`, or a qubit id is outside the spinless/spinful range. | Use a positive integer dimension, integer or per-axis length, positive float or correctly shaped scale matrix, then validate coordinates with `orbital_id`/`grid_indices` before using them. |
| Lattice iteration gives an unexpected number of neighbors | `periodic`, `ordered`, `spinless`, or `n_dofs` changed the count; edge types are not interchangeable. | Record constructor flags, call `validate_edge_type`, and distinguish ordered from unordered site pairs. Use the model/chemistry route for Hamiltonian semantics. |

## API misuse and numerical inputs

| Symptom | Likely cause | Recovery |
|---|---|---|
| `sparse_eigenspectrum` exhausts memory | It intentionally densifies the complete matrix. | Replace it with `get_ground_state`, `get_gap`, or Davidson. If a full spectrum is required, reduce `n_qubits` first and state the dense bound. |
| `get_ground_state` or `get_gap` fails for a tiny matrix | SciPy's `eigsh` restrictions (`k` near matrix dimension), a non-Hermitian input, or a bad initial guess. | Check `shape`, Hermiticity, and initial-guess length. For a genuinely tiny matrix use a bounded dense `numpy.linalg.eigh` reference; for a gap, ensure dimension supports two states. |
| `expectation` raises an input-state error or returns a surprising complex value | The state is neither a NumPy vector/column nor a sparse density matrix, dimensions disagree, or the state is not normalized. | Validate shape and norm. Use a NumPy vector with a `LinearOperator`; use a sparse density matrix only with a sparse matrix operator. Interpret small imaginary roundoff separately from a non-Hermitian result. |
| Davidson returns `success=False` or rejects `n_lowest` | `n_lowest` is not below the effective subspace, the initial guess has the wrong row count/zero columns, or the iteration budget is too small. | Check `DavidsonOptions`, set `max_subspace > n_lowest`, use a nonzero dimension-compatible guess, then inspect the residual. Increase limits only under a stated bound. |
| `QubitDavidson(..., options=DavidsonOptions(...))` raises an error about `processes` | In the inspected 1.8.x development line, the wrapper forwards the same `options` object to the linear-operator factory, which interprets it as parallel options. | Use `QubitDavidson(..., options=None)` for defaults. For custom iteration settings, instantiate `Davidson` with a serial `generate_linear_qubit_operator`, `get_linear_qubit_operator_diagonal`, and a separate `DavidsonOptions`, or use `SparseDavidson`. |
| `group_into_tensor_product_basis_sets` raises `TypeError` | The input is a `FermionOperator`, `BosonOperator`, or another type. | Route mapping/construction appropriately and pass only a `QubitOperator` to this grouping API. |
| Partition iterator raises `ValueError` or yields no values | A binary partition has fewer than two labels, `partition_size > len(qubit_list)`, `max_word_size` exceeds `num_qubits`, or `num_iterations=0` intentionally suppresses output. | Validate the requested coverage and consume the generator explicitly. For empty or zero-iteration output, treat it as an intentional empty schedule rather than a solver failure. |
| `linearize_term` raises an assertion or `ValueError` | The term is not identity, normal-ordered one-body, or normal-ordered two-body in the expected creation/annihilation order. | Normal-order and validate the term family before vectorization. Do not feed arbitrary high-body or nonphysical terms to the equality-constraint layout. |
| `operator_to_vector` has a shorter length than the declared orbital space | It infers the orbital count from referenced terms, so identity-only inputs or unreferenced trailing orbitals do not establish the intended dimension. | Compare `count_qubits(operator)` with the declared `n_orbitals` before vectorizing. Require an operator/dimension representation that makes the full orbital space explicit; do not pad an ambiguous vector silently. |
| `operator_to_vector` fails with a complex coefficient | The implementation allocates a real coefficient vector. | Use the equality-projection path only for the supported real coefficient workflow, or keep the complex operator outside this helper and document the limitation. |

## Workflow-specific failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `get_interaction_rdm` is slow or appears stalled | It enumerates all one- and two-body index combinations and Jordan–Wigner terms; cost grows as the fourth power of the orbital count. | Bound `n_qubits`, use a tiny measured operator for validation, and record the complexity. Do not use it as a large-scale measurement engine without a separate performance plan. |
| RDM round trip changes more than tolerance | Mixed OPDM/TPDM convention, transposed PHDM axes, inconsistent orbital dimension, or wrong particle/hole count. | Recheck the exact tensor convention, use the map pair from the API table, compare shapes before and after, and validate trace identities. Do not symmetrize blindly to hide an index error. |
| `apply_constraints` fails its LP or takes too long | The operator has too many orbitals/terms, complex coefficients, or an infeasible/ill-conditioned constraint setup. | Preflight real one-/two-body terms, bound `n_orbitals`, inspect the LP status, and stop if the problem is not a deliberately small resource-functional calculation. Compare only the intended sector. |
| `PhaseFitEstimator` returns unstable amplitudes or a nonsensical energy | Phase samples are not generated at `get_simulation_points()`, the eigenvalue span is zero or poorly scaled, or the samples are too noisy for the fit. | Generate points from the same estimator, keep eigenvalue order consistent, check finite values and span, and report the result as an estimate. Use `safe=True` before experimenting with fewer points. |
| `get_phase_function` raises an incorrect-result-count error | `len(results)` differs from the selected rotation set length. | Supply one result per rotation, or pass the exact custom `rotation_set`. Validate the `msmt` key and target bit position before fitting. |
| A measurement schedule does not reduce experiments as expected | Tensor-product grouping is heuristic and seed/order dependent; partition coverage is not the same as grouping or shot allocation. | Reassemble grouped operators to confirm coverage, record the seed and basis keys, and keep shot optimization/circuit post-rotations in the circuit/simulation workflow. |
| A resource number is presented as a physical observable | One-norm, contextuality, and equality-constrained bounds are functionals with specific input conventions. | Label the functional and its convention, preserve constant-inclusion and sector metadata, and do not substitute it for an expectation value or an experimentally measured quantity. |

When a failure remains after these checks, retain the smallest reproducible
operator/tensor, its declared dimensions and conventions, the exact public
signature used, and the exception text. Do not broaden the workload while the
input contract is unresolved.
