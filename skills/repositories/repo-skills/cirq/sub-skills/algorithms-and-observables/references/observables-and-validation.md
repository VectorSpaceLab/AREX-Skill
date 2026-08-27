# Observables and validation

Use this reference when a Cirq algorithm needs Pauli observables, exact expectation values, Pauli-basis measurement operations, histogram interpretation, or qubit-order validation.

## Choose an observable workflow

| Goal | Prefer | Why |
| --- | --- | --- |
| Exact expectation on a small noiseless state | `PauliString.expectation_from_state_vector` or `PauliSum.expectation_from_state_vector` | Deterministic, catches qubit-map mistakes early. |
| Exact expectation on a density matrix | `expectation_from_density_matrix` | Appropriate after mixed-state/noisy simulation. |
| Sample an observable in a circuit | `measure_single_paulistring` or `measure_paulistring_terms` | Produces measurement operations for sampler-based workflows. |
| Validate an algorithm's measured bitstrings | `Result.histogram(..., fold_func=...)` | Avoids ambiguity in integer encoding and bit order. |
| Plot a final histogram | `plot_state_histogram` after simulation | Visualization belongs with simulator/plotting setup; keep data validation here. |

## API anchors

### `PauliString`

Verified constructor shape:

```python
cirq.PauliString(*contents, qubit_pauli_map=None, coefficient=1)
```

Construction patterns:

```python
q0, q1 = cirq.LineQubit.range(2)
zz = cirq.PauliString({q0: cirq.Z, q1: cirq.Z})
xx = cirq.X(q0) * cirq.X(q1)
weighted = -0.5 * cirq.Z(q0) * cirq.Z(q1)
```

Notes:

- Contents can include Pauli operations, dictionaries from qubits to Paulis, numbers, or iterables of those values.
- Identities are dropped; an all-identity product is not useful for Pauli measurement helpers.
- `PauliString` is immutable; create a new object for changed coefficients or qubit maps.
- Exact expectation helpers require Hermitian observables. A complex coefficient can make the observable non-Hermitian and raise an error.

### `PauliSum`

Verified constructor shape:

```python
cirq.PauliSum(linear_dict=None)
```

Prefer user-facing construction via arithmetic or `from_pauli_strings`:

```python
hamiltonian = cirq.Z(q0) * cirq.Z(q1) + 0.5 * cirq.X(q0) * cirq.X(q1)
# or
hamiltonian = cirq.PauliSum.from_pauli_strings([
    cirq.PauliString({q0: cirq.Z, q1: cirq.Z}),
    0.5 * cirq.PauliString({q0: cirq.X, q1: cirq.X}),
])
```

`PauliSum` terms are simplified internally; do not depend on iteration order for user-facing output.

### Exact expectations

Verified signatures include:

```python
PauliString.expectation_from_state_vector(
    state_vector, qubit_map, *, atol=1e-7, check_preconditions=True
)
PauliSum.expectation_from_state_vector(
    state_vector, qubit_map, *, atol=1e-7, check_preconditions=True
)
```

Density-matrix counterparts use the same `qubit_map`, `atol`, and `check_preconditions` pattern.

Minimal deterministic expectation check:

```python
q0, q1 = cirq.LineQubit.range(2)
qubits = [q0, q1]
circuit = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1))
result = cirq.Simulator(seed=1234).simulate(circuit, qubit_order=qubits)
state = result.final_state_vector
qubit_map = result.qubit_map

zz = cirq.Z(q0) * cirq.Z(q1)
xx = cirq.X(q0) * cirq.X(q1)
assert abs(zz.expectation_from_state_vector(state, qubit_map) - 1) < 1e-7
assert abs(xx.expectation_from_state_vector(state, qubit_map) - 1) < 1e-7
```

If you pass `qubit_order=qubits` to `simulate`, build any manual `qubit_map` as `{q: i for i, q in enumerate(qubits)}`. If you did not pass `qubit_order`, prefer the simulator result's `qubit_map` instead of reconstructing it by memory.

### Pauli measurement operations

Verified helper shapes:

```python
cirq.measure_single_paulistring(pauli_observable, key=None, confusion_matrix=None)
cirq.measure_paulistring_terms(pauli_basis, key_func=str)
```

Use `measure_single_paulistring` to add one measurement operation for a whole Pauli product:

```python
obs = cirq.X(q0) * cirq.Y(q1) * cirq.Z(q2)
circuit.append(cirq.measure_single_paulistring(obs, key="obs"))
```

Use `measure_paulistring_terms` when each qubit should get its own Pauli-basis measurement key:

```python
basis = cirq.X(q0) * cirq.Y(q1) * cirq.Z(q2)
circuit.append(cirq.measure_paulistring_terms(basis, key_func=lambda q: f"basis_{q}"))
```

Important constraints:

- `measure_single_paulistring` accepts only a `PauliString` with coefficient `+1` or `-1`.
- All-identity products are rejected because they collapse to non-observable identity content for these helpers.
- For non-unit coefficients or sums, use exact expectation from a state/density matrix or decompose into measurement groups at the application level.

## Qubit order validation

Most wrong observable results come from mixing three different orders:

1. The order used to build algorithm registers.
2. The order passed to simulator `qubit_order` or stored in `result.qubit_map`.
3. The order used by measurement operations and histogram folding.

Validation pattern:

```python
qubits = cirq.LineQubit.range(3)
result = cirq.Simulator().simulate(circuit, qubit_order=qubits)
qubit_map = result.qubit_map
assert qubit_map == {q: i for i, q in enumerate(qubits)}
```

When debugging, check a one-term observable such as `Z(q)` on a known basis state before checking a multi-qubit product. If `Z(q)` has the wrong sign or zero when it should be deterministic, the `qubit_map` is probably wrong.

## Bitstrings, histograms, and plotting

For sampled algorithm validation, explicitly convert measured bit arrays to strings:

```python
def bitstring(bits):
    return "".join(str(int(b)) for b in bits)

result = cirq.Simulator(seed=1234).run(circuit, repetitions=100)
counts = result.histogram(key="result", fold_func=bitstring)
most_common = counts.most_common(1)[0][0]
```

This avoids relying on an integer encoding convention when the user's expected answer is a human-readable bitstring.

For plotting, the verified public shape is:

```python
cirq.plot_state_histogram(
    data,
    ax=None,
    tick_label=None,
    xlabel="qubit state",
    ylabel="result count",
    title="Result State Histogram",
)
```

`data` can be a `Result`, a `Counter`, or a sequence of values. Keep plotting optional in validation code; plotting may require an interactive or configured Matplotlib backend.

## Variational-loop validation

For QAOA-like tasks:

- Validate the circuit with one fixed parameter vector before adding an optimizer.
- Assert the measurement key exists: `"m" in result.measurements` or use the key chosen by the recipe.
- Confirm `result.measurements[key].shape == (repetitions, n_qubits)` before computing a classical objective.
- Use `PauliSum` expectation on a small state-vector run to cross-check one fixed parameter point when feasible.
- Route detailed sweep APIs (`ParamResolver`, `Linspace`, `Points`, `run_sweep`, `simulate_sweep`) to `simulation-study-and-noise`.

## Smoke helper

The bundled `scripts/estimate_pauli_expectation.py` computes exact expectations for `|00>` or a Bell state using public Cirq APIs. Use it when you need a quick sanity check that the installed Cirq package, state-vector order, and Pauli expectation helpers agree.
