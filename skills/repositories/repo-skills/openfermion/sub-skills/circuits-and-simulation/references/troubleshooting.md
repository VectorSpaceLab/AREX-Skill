# Circuits and simulation troubleshooting

Diagnose in this order: import, operator/type contract, dimensions and basis
convention, formula/ordering, circuit materialization, then simulator or
plugin. Keep the original requested time, register order, and approximation
controls visible while repairing a failure.

## Install and import

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: openfermion` | The runtime lacks the core package or the selected environment is not active. | Install/select a supported OpenFermion environment, then verify `import openfermion` and `openfermion.__version__`. |
| `ModuleNotFoundError: cirq` while importing circuit APIs | Cirq is required by Cirq-returning primitives, native Trotter algorithms, gates, and VPE modules. | Install a compatible Cirq release in the runtime; keep algebra-only work separate if Cirq is intentionally unavailable. |
| Import fails after adding a hardware package | Optional plugin or version conflict is masking a core import. | Verify `import openfermion` and `import cirq` in isolation, then add one plugin at a time. This skill does not select or repair hardware plugins. |
| A helper works only from the repository directory | A local checkout import or working-directory assumption leaked into the recipe. | Use public `openfermion` imports and run `scripts/circuit_smoke.py` from an arbitrary directory. |
| Cirq operation repr/API differs across versions | Cirq gatesets and decomposition details are version-sensitive. | Depend on the documented public operation interface, not a text diagram or private Cirq class. Record the version when exact decomposition matters. |

## Optional dependency, backend, and plugin boundary

| Symptom | Likely cause | Recovery |
|---|---|---|
| `cirq.Simulator` is unavailable | The installed Cirq package is incomplete or a nonstandard distribution is selected. | Test `import cirq; cirq.Simulator()` separately. Do not substitute a hardware plugin in a structural smoke check. |
| `cirq.contrib` or a target gateset is missing | The requested feature belongs to a Cirq contrib/device package, not the OpenFermion circuit contract. | Keep the OpenFermion operation tree and route target compilation to the approved Cirq/backend workflow. |
| A custom gate cannot be decomposed by the chosen device | Native gateset/device support is outside OpenFermion's guarantee. | Inspect `cirq.decompose` and the target gateset under the caller's backend environment; do not claim hardware compatibility from circuit construction alone. |
| GPU/accelerator simulation is requested | OpenFermion's circuit helpers do not choose accelerator runtimes. | Report the generated circuit and hand off to a separately approved simulator/plugin workflow. |
| A large circuit times out | Trotter rank, steps, formula order, basis changes, or swap networks grew beyond the bounded scope. | Report structural counts first; reduce one declared approximation control or use a resource-planning workflow. Do not silently shrink the system. |

## Dimensions, data, and configuration

| Symptom | Likely cause | Recovery |
|---|---|---|
| `prepare_slater_determinant` fails or addresses a missing qubit | Matrix columns `N` do not equal `len(qubits)`. | Require a two-dimensional `eta x N` matrix and pass exactly `N` qubits. Check `eta <= N`. |
| Slater result has the wrong particle count | The matrix row count or initial computational state was misread. | A matrix with `eta` rows prepares `eta` particles; an integer is big-endian, while a sequence lists occupied qubit indices. Verify the initial state convention explicitly. |
| Slater preparation is numerically unstable or unexpected | Matrix rows are not orthonormal. | Check `Q @ Q.conj().T` against identity before calling; orthonormalize or correct the input in the upstream model stage. |
| `bogoliubov_transform` reports a bad shape | `W` is not `(N,N)` or `(N,2N)` for `N=len(qubits)`. | Validate the shape before construction. For spin-block paths, also confirm the documented spin ordering. |
| Gaussian spin-sector call raises `NotImplementedError` | A spin sector was requested for a non-particle-number-conserving Hamiltonian. | Omit `spin_sector` and use the general Gaussian path, or route to a supported spin-separated number-conserving case. |
| Gaussian circuit appears to prepare the wrong state | `occupied_orbitals` are energy-basis modes, while `initial_state` is a computational-basis state. | Keep those two lists separate and compute the expected energy/state from the same Hamiltonian diagonalization convention. |
| UCC singlet raises for odd `n_qubits` | Singlet implementation assumes paired spin orbitals. | Use an even spin-orbital count or use the general `uccsd_generator` with a correctly dimensioned amplitude representation. |
| UCC singlet generator has indexing/length errors | Packed amplitudes do not have the exact formula-derived length, or dense arrays use another mode count. | Compute `uccsd_singlet_paramsize(n_qubits, n_electrons)` first; require that exact length and arrays shaped over `n_qubits`. Also validate `0 <= n_electrons <= n_qubits`. |
| UCC operator is not unitary when exponentiated | `anti_hermitian=False` was used, or complex/physical amplitudes were supplied under an unrecorded convention. | Use the default anti-Hermitian generator for UCC and verify `G == -G†` before mapping/exponentiating. |
| Low-rank call rejects a tensor as spin-asymmetric | `spin_basis=True` requires a spin-symmetric interaction. | Use a genuinely spin-symmetric tensor, or set `spin_basis=False` only when the tensor is already in the expected non-spin basis. Do not discard spin-dependent terms. |
| Low-rank call rejects imaginary or nonsymmetric coefficients | Exact diagonalization path requires a real symmetric interaction array within tolerance. | Validate reality, chemist ordering, and symmetry; if the physical operator is complex/spin dependent, route to a compatible algorithm instead. |
| `prepare_one_body_squared_evolution` raises `ValueError` | The one-body matrix is not Hermitian. | Check `numpy.allclose(h, h.conj().T)` and fix the upstream operator convention. |

## API and Cirq misuse

| Symptom | Likely cause | Recovery |
|---|---|---|
| `trotter_operator_grouping` rejects the input | The input is not a non-empty `QubitOperator`, or `trotter_order` is outside 1–3. | Convert/select the correct operator in the mapping stage, keep this skill's input contract, and use a positive step count. |
| Second/third-order grouping raises “not enough terms” | The Hamiltonian has fewer than two terms. | Use first order for a one-term operator or retain at least two explicit terms. Do not fabricate a zero term. |
| A custom `term_ordering` gives `KeyError` or unexpected output | A term key is missing, misspelled, duplicated, or ordering was assumed to be cosmetic. | Inspect `list(hamiltonian.terms)`, copy exact keys, and record the order. The default is sorted keys. |
| `pauli_exp_to_qasm` rejects `qubit_list` | It must be a list/tuple with at least one entry per indexed qubit. | Supply labels for every mode index used by the operator. An ancilla label is separate from `qubit_list`. |
| QASM-like text has no operation for identity | Identity exponentiation is a global phase; the non-ancilla path emits no gate. | Preserve the phase in a simulator/compiler that supports global phases, or state that it was intentionally omitted. The controlled path emits an ancilla `Rz` phase. |
| Complex QubitOperator coefficient loses its imaginary part in QASM | The QASM helper casts coefficients to `float(numpy.real(...))`. | Use a Hermitian real-coefficient Pauli operator for this helper, or choose a complex-capable circuit representation and document it. |
| `PauliSumExponential` rejects a Cirq sum | Its terms do not commute, or the supplied object is not a valid Pauli sum. | Group commuting terms first, or append one `PauliSumExponential` per Trotter factor as in the bundled smoke helper. |
| Cirq circuit has unexpected depth | Appending order, overlapping qubits, decomposition, and insertion strategy affect moments. | Measure `len(circuit)` after materialization; use an explicit `InsertStrategy` and report both high-level operation count and decomposed depth when needed. |
| Native Trotter call rejects the Hamiltonian type | The chosen algorithm supports only a specific representation. | Use `LOW_RANK` for `InteractionOperator`, `LINEAR_SWAP_NETWORK`/`SPLIT_OPERATOR` for `DiagonalCoulombHamiltonian`, or route model conversion upstream. |
| Controlled native Trotter call raises `TypeError` or `ValueError` | No control qubit was supplied, or the algorithm lacks the requested controlled order. | Supply a real `cirq.Qid`, choose a supported controlled variant/order, and keep the control out of the system-qubit sequence. |
| `omit_final_swaps=True` changes later measurements | Swap-network steps induce a mode permutation. | Track the returned logical ordering or keep final swaps. Never compare amplitudes without aligning qubit/mode order. |

## VPE workflow failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| VPE circuit rejects a rotation | `initial_rotation`/`final_rotation` was passed as an untargeted gate rather than an operation. | Bind it first, for example `cirq.ry(angle).on(target_qubit)`. |
| VPE circuit measures the wrong bit | `qubits` sequence and `target_qid` index disagree. | Pass the same ordered sequence to circuit construction and `get_phase_function`; use the target's integer index in that sequence. |
| `get_phase_function` reports an incorrect result count | Results were not collected for every rotation tuple or a custom rotation set was used without passing it back. | Keep one result per rotation in exact order and pass the same custom `rotation_set` to the estimator. |
| `get_phase_function` sees no `msmt` column | The circuit was rebuilt with another measurement key or did not include the final measurement. | Preserve the generated circuit's `key='msmt'` contract and run every supplied qubit. |
| `PhaseFitEstimator` is unstable or aliases frequencies | Time points are too sparse, eigenvalue span is zero/poorly scaled, or unknown frequencies were supplied as known. | Use `get_simulation_points(safe=True)`, check the eigenvalue range, and treat the result as a fit under the supplied spectral model—not a universal phase estimator. |
| VPE result is not reproducible | Shot noise, random simulator sampling, custom rotations, or differing circuit order changed the data. | Record rotation set, qubit order, repetitions, simulator seed/noise, and estimator frequencies. VPE circuit generation alone has no noise/shot guarantee. |

## Scope limits

Do not repair a failure by installing a plugin, downloading a benchmark,
changing the Hamiltonian basis, dropping a matrix row, or silently changing the
Trotter order. Report the smallest failing contract and route model/mapping,
hardware, or large-scale benchmarking work to its owning workflow.
