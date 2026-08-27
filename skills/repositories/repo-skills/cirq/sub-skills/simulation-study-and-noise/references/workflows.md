# Local simulation, sweep, histogram, and noise workflows

These workflows assume an importable `cirq` package and local CPU execution. They are safe to adapt into tests or notebooks without network access or provider credentials.

## 1. Sample a measured circuit

Use `run` when the circuit contains measurements and the user wants repeated bitstring samples.

```python
import cirq

q = cirq.LineQubit(0)
circuit = cirq.Circuit(cirq.H(q), cirq.measure(q, key='m'))

sim = cirq.Simulator(seed=1234)
result = sim.run(circuit, repetitions=100)
counts = result.histogram(key='m')
print(counts)
```

Checklist:

- Measurement key exists: `cirq.measure(..., key='m')`.
- Repetitions are high enough for a stable estimate.
- Seed is set when exact output needs to be reproducible.

## 2. Simulate a final state vector

Use `simulate` when the user asks for amplitudes, final state, state-vector comparison, or a measurement-free evolution.

```python
import numpy as np
import cirq

q0, q1 = cirq.LineQubit.range(2)
circuit = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1))

sim = cirq.Simulator(dtype=np.complex64, seed=1234)
trial = sim.simulate(circuit, qubit_order=[q0, q1])
state = trial.final_state_vector
print(np.round(state, 3))
```

Checklist:

- Provide `qubit_order` when comparing array entries to bitstrings.
- Remove terminal measurements if the desired state is before measurement.
- For arbitrary non-unitary channels, switch to the density-matrix workflow.

## 3. Run a parameter sweep

Use `run_sweep` for sampled parameter scans and `simulate_sweep` when state data is needed per resolver.

```python
import sympy
import cirq

q = cirq.LineQubit(0)
theta = sympy.Symbol('theta')
circuit = cirq.Circuit(cirq.rx(theta)(q), cirq.measure(q, key='m'))

sweep = cirq.Linspace('theta', start=0.0, stop=3.14159, length=5)
sim = cirq.Simulator(seed=1234)
for result in sim.run_sweep(circuit, params=sweep, repetitions=200):
    print(result.params, result.histogram(key='m'))
```

Alternatives:

```python
points = cirq.Points('theta', [0.0, 0.5, 1.0])
resolvers = [{'theta': 0.0}, {'theta': 0.5}, {'theta': 1.0}]
```

Checklist:

- The sweep key string must match the symbolic parameter name.
- Every symbol in the circuit must receive a numeric value.
- Keep sweep length bounded when repetitions are large.

## 4. Combine multiple measurement keys

Use `multi_measurement_histogram` for joint outcomes across separate measurement operations.

```python
q0, q1 = cirq.LineQubit.range(2)
circuit = cirq.Circuit(
    cirq.H(q0),
    cirq.CNOT(q0, q1),
    cirq.measure(q0, key='a'),
    cirq.measure(q1, key='b'),
)
result = cirq.Simulator(seed=1234).run(circuit, repetitions=100)
print(result.histogram(key='a'))
print(result.histogram(key='b'))
print(result.multi_measurement_histogram(keys=['a', 'b']))
```

If a single measurement key measures multiple qubits, `result.histogram(key='m')` folds that key's bit row into integer outcomes by default.

## 5. Add local noise for sampling

Use `cirq.sample` for a compact one-off noisy sampling workflow or instantiate a simulator if you need repeated control.

```python
q = cirq.NamedQubit('q')
circuit = cirq.Circuit(
    cirq.measure(q, key='initial_state'),
    cirq.X(q),
    cirq.measure(q, key='after_not_gate'),
)
noise = cirq.ConstantQubitNoiseModel(cirq.amplitude_damp(0.4))
result = cirq.sample(program=circuit, noise=noise, repetitions=100, seed=1234)
print(result.histogram(key='initial_state'))
print(result.histogram(key='after_not_gate'))
```

Other common local channels:

```python
cirq.depolarize(0.01)
cirq.depolarize(0.02, n_qubits=2)
cirq.phase_damp(0.05)
cirq.bit_flip(0.01)
```

Checklist:

- Use channel probabilities or damping values between 0 and 1.
- Set a seed for reproducible smoke tests.
- Treat histograms as samples from a distribution, not exact probabilities, unless the setup is deterministic.

## 6. Inspect a noisy density matrix

When channels/noise appear and the user asks for the final quantum state, use `DensityMatrixSimulator` instead of a pure-state result.

```python
q = cirq.LineQubit(0)
circuit = cirq.Circuit(cirq.X(q))
noise = cirq.ConstantQubitNoiseModel(cirq.amplitude_damp(0.4))

sim = cirq.DensityMatrixSimulator(noise=noise, seed=1234)
trial = sim.simulate(circuit, qubit_order=[q])
print(trial.final_density_matrix)
```

Checklist:

- Density matrices scale as 4^n; keep qubit count small for local diagnostics.
- Use `final_density_matrix` instead of `final_state_vector`.
- Specify `qubit_order` before comparing matrix indices.

## 7. Make the noisy circuit explicit

Use `Circuit.with_noise` when the task asks to inspect or reuse the circuit with inserted noise.

```python
q = cirq.LineQubit(0)
circuit = cirq.Circuit(cirq.H(q), cirq.measure(q, key='m'))
noisy_circuit = circuit.with_noise(cirq.ConstantQubitNoiseModel(cirq.depolarize(0.01)))
print(noisy_circuit)
```

This is useful for debugging where noise is inserted, but avoid expanding large circuits just to sample them.

## 8. Plot a state histogram

Use `plot_state_histogram` when a local plot is requested and Matplotlib is available.

```python
import matplotlib.pyplot as plt
import cirq

q = cirq.LineQubit.range(3)
circuit = cirq.Circuit(cirq.H.on_each(*q), cirq.measure(*q, key='m'))
result = cirq.Simulator(seed=1234).run(circuit, repetitions=100)

fig, ax = plt.subplots()
cirq.plot_state_histogram(result, ax=ax)
fig.tight_layout()
```

For sparse or custom-labeled plots, pass `result.histogram(key='m')` or another `Counter` to `plot_state_histogram` instead of the full result.

## 9. Run the bundled smoke demo

The bundled script is a deterministic one-qubit noisy-sampling check:

```bash
python scripts/run_noisy_smoke.py --help
python scripts/run_noisy_smoke.py --repetitions 100 --amplitude-damp 0.4 --seed 1234
```

Expected behavior: the script prints the circuit, the configured amplitude-damping noise, and histograms for `initial_state` and `after_not_gate`. It does not require network access, provider credentials, or a source checkout.
