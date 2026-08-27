# Troubleshooting algorithms and observables

Use this page when an algorithm circuit, histogram, Pauli measurement, or expectation value is numerically plausible but not correct.

## Fast triage checklist

1. Print the circuit diagram and check register roles, measurement keys, and whether measurements are terminal.
2. For exact expectations, print `result.qubit_map` or the explicit `qubit_order` used to create it.
3. Validate a one-qubit observable on a known state before validating a multi-qubit `PauliString` or `PauliSum`.
4. For sampled algorithms, convert measurement arrays with an explicit `fold_func` rather than interpreting histogram integers by memory.
5. If an issue is about simulator choice, sweeps, noise, result objects, or plotting backend, route to `simulation-study-and-noise`.

## Symptoms and fixes

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `expectation_from_state_vector` reports that the qubit map must be complete | Missing an observable qubit from `qubit_map` or using a map for a different register | Use `simulate(..., qubit_order=qubits)` and `{q: i for i, q in enumerate(qubits)}`, or use `result.qubit_map` from the simulator result. |
| Error mentions qubit-map indices | Duplicate, negative, out-of-range, or non-integer index in `qubit_map` | Rebuild the map from the exact state-vector order; do not merge maps from different registers. |
| Error says input state dtype must be complex | State vector or density matrix was integer/float typed | Cast to `np.complex64` or `np.complex128` before exact expectation calls. |
| Error says state vector is not normalized | The vector is not a valid quantum state or is a deliberately unnormalized intermediate | Normalize the state or keep `check_preconditions=True` and fix the upstream state. Use `check_preconditions=False` only for a known, intentionally unchecked diagnostic. |
| Error mentions non-Hermitian PauliString/PauliSum | Observable has an imaginary coefficient or otherwise is not Hermitian | Use real coefficients for expectation values; split non-Hermitian expressions into Hermitian real/imaginary parts if that is the intended analysis. |
| `measure_single_paulistring` rejects the observable coefficient | The coefficient is not `+1` or `-1` | Use a unit-coefficient Pauli basis measurement and apply the scalar in post-processing, or use exact expectation helpers for weighted observables. |
| `measure_single_paulistring` or `measure_paulistring_terms` rejects an all-identity product | Identities are dropped, leaving no actual Pauli basis to measure | Treat identity expectation as a constant separately; do not add an identity-only measurement operation. |
| Bell-state `ZZ`/`XX` expectation is not `+1` | Qubit order or map does not match the state vector | Run `python scripts/estimate_pauli_expectation.py --state bell --observable zz` and compare the script's qubit map pattern to the user's code. |
| A sampled bitstring appears reversed | Histogram integer encoding or measurement-qubit order was assumed incorrectly | Use `Result.histogram(key, fold_func=lambda bits: "".join(str(int(b)) for b in bits))` and define the expected string in the same qubit order passed to `measure`. |
| Phase-estimation estimate is off by a power of two or bit reversal | Counting-register order or QFT `without_reverse` choice is inconsistent with readout | Use a known phase such as `1/4` and test both the inverse-QFT register order and modal integer conversion before arbitrary phases. |
| QFT followed by inverse QFT is not identity | Manual construction omitted swaps, reversed the register, or used inconsistent controls | Compare against `cirq.qft(*qubits, without_reverse=...)` for the same option. If hardware adjacency caused changes, route to `transformers-and-compilation`. |
| Teleportation circuit cannot be treated as one unitary | It contains mid-circuit measurements and classical controls by design | Validate by simulating the circuit and comparing Bob's final Bloch vector or Pauli expectations; do not require a global unitary. |
| Classical-control correction does not fire in teleportation | Measurement key typo or mismatched key object/string | Reuse constants for key names and print the diagram to confirm the classical-control wires use the same keys as the measurements. |
| Grover or Bernstein-Vazirani validation fails intermittently | Random secret bits, too few repetitions, or unstable histogram assertion | Fix the secret bits and seed for tests. Assert the most common bitstring or exact deterministic result only when repetitions and algorithm setting justify it. |
| QAOA objective does not change during optimization | Resolver keys do not match symbols, parameters are generated but not inserted, or measurement key is wrong | Test one fixed parameter vector, print `cirq.parameter_names(circuit)`, and assert `result.measurements[key]` has the expected shape before optimizing. |
| Optimizer loop is slow or flaky | Random graph/initial point, too many repetitions, or full classical optimization in a smoke test | Use a tiny graph, fixed parameters, fixed seed, and a one-step objective check for acceptance; reserve long optimization for integration runs. |
| Shor/HHL-style example is too slow | Classical simulation cost grows quickly | Use the smallest demonstrable input and a classical consistency check. Treat full examples as educational, not a default verification target. |

## Qubit-map diagnostic pattern

When an expectation is wrong, add this temporary check near the simulation:

```python
qubits = list(qubits)
result = cirq.Simulator(seed=1234).simulate(circuit, qubit_order=qubits)
expected_map = {q: i for i, q in enumerate(qubits)}
assert result.qubit_map == expected_map
print("qubit order:", qubits)
print("qubit map:", result.qubit_map)
```

Then test a single-qubit observable such as `cirq.Z(qubits[0])` on a known basis state. Only after that passes should you test a multi-qubit product or sum.

## Measurement and histogram diagnostics

For result interpretation bugs, avoid integer histograms until the expected bit ordering is settled:

```python
def as_bits(bits):
    return "".join(str(int(b)) for b in bits)

counts = result.histogram(key="result", fold_func=as_bits)
print(counts)
```

If multiple measurement keys are used, inspect `result.measurements.keys()` and the shape of each array before combining records. Superdense coding and teleportation examples often have separate input/control/output keys by design.

## When to route elsewhere

- Use `core-circuits-and-ops` if the failure is about constructing gates/operations, measurement keys, custom gates, parameters as syntax, or circuit diagrams.
- Use `simulation-study-and-noise` if the failure is about sampler vs simulator APIs, sweeps, noisy channels, density-matrix simulation, result objects, or plotting backend.
- Use `transformers-and-compilation` if the failure appears after decomposing, optimizing, targeting a gateset, or routing onto a device graph.
- Use `hardware-providers-and-serialization` if the failure appears only when packaging for a provider, serializing for a service, or using credentials.
