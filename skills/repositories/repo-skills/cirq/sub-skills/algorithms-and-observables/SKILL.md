---
name: algorithms-and-observables
description: "Use Cirq to assemble textbook algorithm circuits, Pauli
  observables, expectation-value checks, and variational-loop validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Cirq algorithms and observables

Use this sub-skill when the task is about algorithm-level Cirq patterns or observable validation rather than basic circuit syntax. Typical triggers include QFT, phase estimation, Grover search, Bernstein-Vazirani, quantum teleportation, superdense coding, QAOA-style ansatz loops, `PauliString`, `PauliSum`, Pauli measurements, expectation values, or interpreting algorithm result histograms.

## Start here

1. Pick the closest recipe in [algorithm-recipes.md](references/algorithm-recipes.md).
2. For observables, expectation values, qubit-order checks, or result validation, read [observables-and-validation.md](references/observables-and-validation.md).
3. If a result looks wrong, use [troubleshooting.md](references/troubleshooting.md) before changing the circuit.
4. For a tiny deterministic smoke check of Pauli expectations, run [estimate_pauli_expectation.py](scripts/estimate_pauli_expectation.py):

```bash
python scripts/estimate_pauli_expectation.py --state bell --observable zz
python scripts/estimate_pauli_expectation.py --state zero --observable sum
```

## Routing boundaries

- Route raw qubits, gates, moments, measurement keys, parameters, custom gates, JSON/QASM, and protocol mechanics to [core-circuits-and-ops](../core-circuits-and-ops/SKILL.md).
- Route simulator choice, noisy runs, sweeps, result objects, histograms at sampler depth, and plotting setup to [simulation-study-and-noise](../simulation-study-and-noise/SKILL.md).
- Route decomposition, optimizer passes, target gatesets, adjacency constraints, and hardware routing to [transformers-and-compilation](../transformers-and-compilation/SKILL.md).
- Route provider packaging, cloud samplers, credentials, provider serializers, and widgets to [hardware-providers-and-serialization](../hardware-providers-and-serialization/SKILL.md).

## API anchors covered here

- Built-in QFT: `cirq.qft(*qubits, without_reverse=False, inverse=False)` and `cirq.QuantumFourierTransformGate(num_qubits, without_reverse=False)`.
- Observables: `cirq.PauliString(*contents, qubit_pauli_map=None, coefficient=1)` and `cirq.PauliSum(linear_dict=None)`; prefer arithmetic or `PauliSum.from_pauli_strings` for user code.
- Exact expectations: `PauliString.expectation_from_state_vector(...)`, `PauliSum.expectation_from_state_vector(...)`, and density-matrix counterparts.
- Measurement of Pauli observables: `cirq.measure_single_paulistring(...)` and `cirq.measure_paulistring_terms(...)`.
- Histogram/plot handoff: `cirq.Result.histogram`, custom `fold_func` bitstrings, and `cirq.plot_state_histogram(...)` for plotting after simulation.

## Validation stance

Favor small, deterministic validation circuits before scaling an algorithm. For textbook examples, validate one known setting with a state-vector or expectation-value check, then validate sampled behavior with explicit measurement keys and qubit order. Treat Shor/HHL-scale examples and full optimizer loops as educational or integration tests, not fast smoke tests.
