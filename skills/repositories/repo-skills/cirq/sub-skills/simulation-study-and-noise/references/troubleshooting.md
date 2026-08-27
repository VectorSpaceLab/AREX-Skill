# Cirq local simulator troubleshooting

Use this reference when local execution, sweeps, noisy simulation, or result inspection behaves unexpectedly.

## Problem-to-fix table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| A noisy/channel circuit gives no usable final state vector or appears inconsistent with expected mixed-state behavior. | Non-unitary channels can create mixed states; a pure-state result is the wrong representation. | Use `cirq.DensityMatrixSimulator(noise=..., seed=...)` and inspect `final_density_matrix`. Keep `Simulator` for pure-state/unitary workflows or simple sampling. |
| A parameterized circuit fails with unresolved symbols. | A `sympy.Symbol` in a gate was not assigned a numeric value, or the resolver key does not match the symbol name. | Use `run(..., param_resolver={'name': value})`, `run_sweep`, `simulate_sweep`, or pre-resolve with `cirq.resolve_parameters`. Inspect parameter names before running. |
| `run` returns an empty or unhelpful result. | The circuit has no measurement operations or the requested key was not measured. | Add `cirq.measure(..., key='m')` for sampling, or use `simulate` if the task is to inspect amplitudes/state instead of samples. |
| `result.histogram(key='m')` raises a key error. | The key string does not exactly match a measurement key in the result. | Print or inspect `result.measurements.keys()`, then use the exact key. For separate keys, use `multi_measurement_histogram(keys=[...])`. |
| Repeated noisy or sampling runs differ. | Sampling and noisy trajectories are stochastic. | Set `seed` on `Simulator`, `DensityMatrixSimulator`, `CliffordSimulator`, or `cirq.sample`; fix `repetitions`; assert distributional tolerances instead of exact counts unless seed and version are controlled. |
| Memory usage explodes or the process is killed. | State-vector simulation scales as 2^n amplitudes; density matrices scale as 4^n elements. Sweeps and large retained results multiply cost. | Reduce qubits, avoid density-matrix simulation unless needed, keep sweeps small, prefer `CliffordSimulator` for Clifford-only circuits, and avoid storing large intermediate states. |
| `CliffordSimulator` rejects a circuit or gives unsupported-operation errors. | The circuit contains non-Clifford gates, arbitrary rotations, or general channels/noise. | Switch to `Simulator` for pure-state non-Clifford circuits or `DensityMatrixSimulator` for general noisy/channel circuits. |
| Histogram integers do not match expected bitstring order. | Histogram folding and state-vector basis order may not match the user's assumed qubit order. | Specify `qubit_order` for simulation; for histograms, use custom `fold_func` or inspect raw arrays in `result.measurements[key]`. |
| A plotted histogram is unreadable for many qubits. | The state space is too large or the output is sparse. | Plot `result.histogram(key=...)` or a filtered `Counter` instead of all possible states; reduce measured qubits or summarize top outcomes. |
| Counts from `cirq.sample(..., noise=...)` differ from an explicitly instantiated simulator. | Different simulator choices or random seeds can model noisy sampling differently. | Use a single explicit simulator class for comparisons; choose `DensityMatrixSimulator` when the density-matrix model is the reference. |

## Diagnostic snippets

### Confirm measurement keys before histogramming

```python
result = sim.run(circuit, repetitions=10)
print(sorted(str(k) for k in result.measurements.keys()))
```

If the expected key is absent, inspect the circuit diagram and add or rename `cirq.measure` operations.

### Check unresolved parameter names

```python
import cirq

print(cirq.parameter_names(circuit))
resolved = cirq.resolve_parameters(circuit, {'theta': 0.25})
```

If names remain after resolution, every sweep or resolver entry should be checked for spelling and nesting. Parameterized subcircuits and repeated gate definitions can hide additional symbols.

### Choose a simulator after channels are introduced

```python
# Sampling only.
sampled = cirq.sample(program=circuit, noise=noise, repetitions=100, seed=1234)

# Exact mixed-state inspection.
trial = cirq.DensityMatrixSimulator(noise=noise, seed=1234).simulate(base_circuit)
rho = trial.final_density_matrix
```

If the task asks for probabilities after noise rather than individual samples, a density matrix is usually the more direct diagnostic.

### Make histogram folding explicit

```python
# Integer outcomes for one key.
counts = result.histogram(key='m')

# Raw measured bits.
raw = result.measurements['m']

# Custom labels from measured bit tuples.
labels = result.histogram(key='m', fold_func=lambda bits: ''.join(str(int(b)) for b in bits))
```

Use this when bit ordering, multi-qubit keys, or presentation labels matter.

## Required escalation or routing

- If the user needs to construct or modify the circuit object before running it, route to `core-circuits-and-ops` first.
- If the user needs a circuit optimized or routed to a target device before local simulation, route to `transformers-and-compilation` first.
- If the sampler is a cloud provider or requires credentials, route to `hardware-providers-and-serialization`; do not try to run live hardware from this sub-skill.
- If the problem is algorithm correctness, observable expectation values, or textbook circuit design, route to `algorithms-and-observables` and return here only for execution and histograms.
