# Simulation API reference

Read this reference for signatures, return shapes, and capability boundaries.
The signatures below were checked against the installed PyQuil 4.18.0 package;
the details are distilled for runtime use rather than copied as a source API
listing.

## Simulators

```python
PyQVM(
    n_qubits: int,
    quantum_simulator_type: type[AbstractQuantumSimulator] | None = None,
    seed: int | None = None,
    post_gate_noise_probabilities: dict[str, float] | None = None,
)
NumpyWavefunctionSimulator(n_qubits: int, rs: RandomState | None = None)
ReferenceWavefunctionSimulator(n_qubits: int, rs: RandomState | None = None)
ReferenceDensitySimulator(n_qubits: int, rs: RandomState | None = None)
```

`PyQVM` exposes `wf_simulator`, `execute(program, memory_map=None, **kwargs)`,
`execute_once(program)`, `get_result(...)`, and `read_memory(region_name=...)`.
`execute` requires a `Program`, resets the state before each execution, and
runs the program's shot loop. `execute_once` does not automatically reset
wavefunction or classical RAM. A direct simulator's `do_program(program)`
accepts only `Gate` instructions and returns itself.

State fields are implementation-facing but stable for this simulation route:

- Reference wavefunction: `sim.wf`, a complex128 flat array of shape
  `(2**n_qubits,)`.
- NumPy wavefunction: `sim.wf`, a complex128 tensor of shape `(2,)*n_qubits`.
  To compare it with the canonical flat vector, use
  `sim.wf.transpose().reshape(-1)`.
- Density: `sim.density`, a complex128 matrix of shape
  `(2**n_qubits, 2**n_qubits)`; `initial_density` is the state restored by
  `reset()` after `set_initial_state(...)`.

All simulator classes implement the conceptual boundary
`do_gate`, `do_gate_matrix`, `do_measurement`, `expectation`, `reset`, and
`sample_bitstrings`. They return themselves for gate/reset operations where
applicable.

## Wavefunction object

`pyquil.wavefunction.Wavefunction(amplitude_vector)` accepts a non-empty
power-of-two-length vector whose squared magnitudes sum to one. Useful methods:

| API | Return and meaning |
|---|---|
| `Wavefunction.zeros(n)` | ground state with `2**n` amplitudes |
| `.amplitudes` | original NumPy amplitude vector |
| `len(wavefunction)` | qubit count |
| `.probabilities()` | NumPy array of length `2**n`, canonical lexicographic order |
| `.get_outcome_probs()` | all bitstrings (`str`) to probabilities |
| `.pretty_print(decimal_digits=2)` | compact amplitude expression; display only |
| `.pretty_print_probabilities(decimal_digits=2)` | nonzero-after-rounding bitstring map |
| `.sample_bitstrings(n_samples)` | `(n_samples, n_qubits)` array from global NumPy RNG |

`pretty_print*` methods round and may omit small values; never use them as a
numerical equality check. `Wavefunction.sample_bitstrings` is distinct from
`WavefunctionSimulator.run_and_measure`: the latter takes an optional ordered
`qubits` list and returns columns in that requested order.

## Service-backed WavefunctionSimulator

```python
WavefunctionSimulator(
    *,
    gate_noise: tuple[float, float, float] | None = None,
    measurement_noise: tuple[float, float, float] | None = None,
    random_seed: int | None = None,
    timeout: float = 10.0,
    client_configuration: QCSClient | None = None,
)
```

This class is in `pyquil.api` but delegates to a QVM HTTP endpoint. Its main
methods are:

- `.wavefunction(quil_program, memory_map=None) -> Wavefunction`;
- `.expectation(prep_prog, pauli_terms, memory_map=None) -> float | np.ndarray`;
- `.run_and_measure(quil_program, qubits=None, trials=1, memory_map=None) -> np.ndarray`.

`pauli_terms` accepts a `PauliSum` or a list of `PauliTerm`s. A `PauliSum` is
aggregated; a list returns one value per term. `gate_noise` and
`measurement_noise` are service-request parameters `(Px, Py, Pz)`; they are not
PyQVM's post-gate probability dictionary. The first state/expectation/measure
call is the meaningful connectivity check. No QVM response may be claimed
from constructor success alone.

## Matrix and state tools

The public `pyquil.simulation` exports include
`get_measure_probabilities`, `targeted_einsum`, `targeted_tensordot`, and
`zero_state_matrix`. The `pyquil.simulation.matrices` module provides named
standard gate matrices in `QUANTUM_GATES` and the six Kraus-operator factories
in `KRAUS_OPS`/their named functions. Useful matrix tools are in
`pyquil.simulation.tools`:

| Function | Contract |
|---|---|
| `all_bitstrings(n_bits)` | `(2**n_bits, n_bits)` int8 array in lexicographic order |
| `lifted_gate_matrix(matrix, qubit_inds, n_qubits)` | full `(2**n, 2**n)` operator for a `2**k` square matrix |
| `lifted_gate(gate, n_qubits)` | full operator for a constant-parameter Quil gate |
| `program_unitary(program, n_qubits)` | product of gate operators; gate/HALT only |
| `lifted_pauli(pauli_sum_or_term, qubits)` / `tensor_up(...)` | operator on the listed Hilbert-space qubits |
| `lifted_state_operator(state, qubits)` | tensor-product state projector for experiment state objects |
| `unitary_equal(A, B)` | global-phase-insensitive comparison for equal-shape matrices |

`lifted_gate_matrix` and `lifted_pauli` use Quil's little-endian convention:
for two qubits and `qubits=[0, 1]`, a Pauli on q0 appears on the right factor
(e.g. `sX(0)*sY(1)` lifts to `kron(Y, X)`). Check matrix shape and qubit list
before applying a custom matrix; direct `do_gate_matrix` deliberately does not
perform a unitarity check.

## Observable boundary

For a wavefunction simulator, `expectation(PauliTerm | PauliSum)` computes the
state expectation locally. For Bell `H(0); CNOT(0, 1)`, use
`XX = sX(0)*sX(1)`, `YY = sY(0)*sY(1)`, and `ZZ = sZ(0)*sZ(1)`; expected values
are approximately `+1`, `-1`, and `+1`. `ReferenceDensitySimulator.expectation`
currently raises `NotImplementedError`, so calculate a density diagnostic as
`np.trace(rho @ lifted_pauli(operator, list(range(n_qubits))))` when the
operator and matrix ordering are controlled. Complete measurement/estimation
work belongs to `../noise-experiments/`.

## Resource sizing

For complex128 storage, estimate:

```text
wavefunction bytes  ~= 16 * 2**n
 density bytes      ~= 16 * 4**n
full operator bytes ~= 16 * 4**n
```

For orientation, a 20-qubit statevector is about 16 MiB, while a dense
20-qubit density matrix is about 16 TiB. Temporary contractions and lifted
operators increase the peak. Reject or redesign large requests before
constructing the object.
