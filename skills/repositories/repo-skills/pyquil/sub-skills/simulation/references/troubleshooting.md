# Simulation troubleshooting

Use the symptom, cause, and recovery below before changing backends. Preserve
the original program and record `n_qubits`, seed, state shape, noise map, and
whether a service call was attempted.

| Symptom | Likely cause | Recovery |
|---|---|---|
| `api.QVMError: Could not communicate with QVM at ...` from `.wavefunction(...)` | `WavefunctionSimulator` is service-backed and no QVM is reachable | If the task is local, switch to `PyQVM` or a direct reference/NumPy simulator. If a QVM is required, route endpoint/service diagnostics to `../compile-execute/`; do not call this an in-process result. |
| Bell vector appears as `[0, 0, 1, 0]` instead of `[0, 1, 0, 0]` for `X(0)` | NumPy tensor was flattened without reversing axes, or q0-left/q0-right conventions were mixed | Test `X(0)` and `X(1)`. Compare NumPy with `wf.transpose().reshape(-1)`; use canonical labels `00,01,10,11` with q0 on the right. |
| Sample rows seem to use the wrong qubit columns | `Wavefunction.sample_bitstrings`, simulator sampling, and `run_and_measure` have different presentation rules | For service calls pass `qubits=[...]` and treat columns as that list. For local simulators assert a basis state and document q0 column 0. Do not infer order from a Bell state alone. |
| `ValueError` mentioning “without setting the random state” | Direct simulator was created with `rs=None` and asked to measure or sample | Instantiate with `rs=np.random.RandomState(seed)` or run through `PyQVM(seed=seed)`. Deterministic unitary gates and expectations do not require `rs`. |
| `NotImplementedError: The numpy simulator cannot handle noise` | A post-gate noise map was attached to an explicit `NumpyWavefunctionSimulator` | Use the default density selection: `PyQVM(..., post_gate_noise_probabilities={...})`, or explicitly choose `ReferenceDensitySimulator`. The map is experimental and limited to six named channels. |
| `NotImplementedError: The reference wavefunction simulator cannot handle noise` | A post-gate noise map was attached to a pure-state reference backend | Switch to `ReferenceDensitySimulator`; do not fake noise by perturbing amplitudes. Route complete noise models to `../noise-experiments/`. |
| Noise map is ignored or gives an unknown-key failure | Keys are not `relaxation`, `dephasing`, `depolarizing`, `phase_flip`, `bit_flip`, or `bitphase_flip`, or no gate was executed | Validate the dictionary and run a program containing a gate. Remember the map applies after every gate, on every qubit in that gate; it is not readout noise or a full hardware model. |
| `ValueError` from density initialization: “not square”, “not defined on the same numbers of qubits”, “not Hermitian”, “not trace one”, or negative eigenvalues | Matrix shape/dimension or quantum-state invariants are invalid | For n qubits pass a `(2**n, 2**n)` complex matrix. Check `rho == rho.conj().T`, `trace(rho)==1`, and nonnegative eigenvalues. Build a pure state with `outer(psi, psi.conj())` after normalizing `psi`. |
| `ReferenceDensitySimulator.expectation(...)` raises `NotImplementedError` | This backend's expectation method is intentionally unimplemented in this version | Compute a controlled diagnostic with `np.trace(rho @ lifted_pauli(...))`, or route observable estimation/Experiments to `../noise-experiments/`. Label the manual calculation explicitly. |
| `ValueError` from `program_unitary` or direct `do_program` for a declaration, measurement, or control instruction | Matrix/direct gate path is gate-only | Use `program_unitary` only for unitary gate programs. Use `PyQVM` for classical memory/control flow and measurements; route program authoring questions to `../program-authoring/`. |
| `NotImplementedError` for a parameterized `DEFGATE` | PyQVM rejects parameterized `DEFGATE`s; it also rejects `DEFGATE ... AS MATRIX | PAULI-SUM` variants | Resolve the gate to supported constant matrix instructions before local PyQVM execution, or use a backend/compiler path that explicitly supports the definition. Do not claim all valid Quil is PyQVM-executable. |
| `NotImplementedError` for `ResetQubit`, shared memory, or batch execution | PyQVM has explicit unsupported instruction/operation boundaries | Simplify to supported global `RESET`/ordinary memory if semantics permit, or route to the compiler/QVM path. `execute_with_memory_map_batch` cannot be used as a local batch shortcut because state resets per execute. |
| `KeyError`/unknown gate or failure in a custom matrix application | Gate name is outside the simulator matrix registry, parameters are symbolic, or matrix shape does not match qubit count | Use `simulation.matrices.QUANTUM_GATES`/a concrete supported gate, resolve parameters before `lifted_gate`, and validate a custom matrix is square with dimension `2**k`. `do_gate_matrix` performs no unitarity check. |
| Process is killed or allocation hangs as qubits increase | Statevector O(2^n), density/operator O(4^n), plus temporary arrays | Estimate `16*2**n` bytes for a complex128 vector and `16*4**n` for dense density/operator storage. Reduce qubits, use sparse/analytic reasoning, avoid density when pure state is sufficient, and stop before allocation. |
| Density trace drifts after a custom update | Non-unitary matrix was applied as a unitary, Kraus operators were incomplete, or an ordering/lifting error occurred | Recheck the channel's Kraus completeness, use the named PyQuil Kraus factories, validate Hermitian/trace/PSD after every step, and compare a one-qubit known channel before scaling up. |
| `Wavefunction` constructor rejects a state | Vector length is empty/non-power-of-two or probabilities do not sum to one | Normalize a length `2**n` complex vector; use `Wavefunction.zeros(n)` for the ground state. Use numerical arrays for assertions, not rounded pretty-print output. |
| A result is claimed as deterministic but repeated runs differ | A measurement/noisy gate/global `Wavefunction` sampler used an unseeded RNG, or the remote service has independent stochastic behavior | Seed `PyQVM`/direct `rs`, keep sampling counts and seed in the record, and treat `WavefunctionSimulator.random_seed` as a QVM request setting—not proof of local RNG control. |

## Fast recovery probes

1. Run `python scripts/bell_state_inprocess.py --help` and then the helper
   itself. A pass proves only the bundled local Bell assertions.
2. Re-run the same Bell program with both
   `ReferenceWavefunctionSimulator` and `PyQVM` and compare the canonical
   vector, probabilities, and `XX`/`YY`/`ZZ` expectations.
3. For ordering, run `X(0)` and `X(1)` separately and assert indices/columns.
4. For density, start with `zero_state_matrix(n)`, apply one gate/noise step,
   and check shape, Hermiticity, trace, and eigenvalues before adding shots.
5. If any call constructs `WavefunctionSimulator`, mark the workflow
   service-dependent and stop local verification at the first QVM error.
