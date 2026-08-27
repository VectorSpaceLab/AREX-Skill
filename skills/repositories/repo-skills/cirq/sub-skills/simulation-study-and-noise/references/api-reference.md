# Cirq simulation, study, and noise API reference

This reference covers local Cirq execution APIs for simulator choice, sampling, sweeps, result inspection, and local noise. It intentionally stays within local CPU workflows and does not cover cloud-provider samplers.

## Simulator and sampler selection

| Need | Prefer | Why | Watch for |
| --- | --- | --- | --- |
| Measurement samples from a unitary or lightly noisy circuit | `cirq.Simulator(seed=...)` or `cirq.sample(..., seed=...)` | Fast default local sampler; returns `cirq.Result` with measurement arrays. | Sampling only reports measurement keys; use `simulate` for state data. |
| Exact mixed-state evolution or inspecting a noisy final state | `cirq.DensityMatrixSimulator(noise=..., seed=...)` | Represents density matrices and supports non-unitary channels/noise models directly. | Memory scales as 4^n in qubit count. |
| Stabilizer/Clifford circuits with Clifford measurements | `cirq.CliffordSimulator(seed=...)` | Efficient for Clifford-only/stabilizer workflows. | Non-Clifford rotations, general channels, or arbitrary gates require another simulator. |
| A concise one-off sample with optional noise | `cirq.sample(program=..., noise=..., repetitions=..., seed=...)` | Functional wrapper for quick local sampling. | For reusable workflows, instantiate the simulator explicitly. |
| Parameterized sampling or simulation | `run_sweep` / `simulate_sweep` with `Linspace`, `Points`, or dictionaries | Keeps resolver values attached to each result. | Every symbol used by numeric gates must be resolved. |

## Core constructors and method signatures

Use these signatures as the stable call-shape guide:

```python
cirq.Simulator(*, dtype=np.complex64, noise=None, seed=None, split_untangled_states=True)
cirq.DensityMatrixSimulator(*, dtype=np.complex64, noise=None, seed=None, split_untangled_states=True)
cirq.CliffordSimulator(seed=None, split_untangled_states=False)
```

Execution methods on simulator objects:

```python
sim.run(program, param_resolver=None, repetitions=1) -> cirq.Result
sim.run_sweep(program, params, repetitions=1) -> Sequence[cirq.Result]
sim.simulate(program, param_resolver=None, qubit_order=..., initial_state=None)
sim.simulate_sweep(program, params, qubit_order=..., initial_state=None) -> list
```

Functional sampling wrapper:

```python
cirq.sample(
    program,
    *,
    noise=None,
    param_resolver=None,
    repetitions=1,
    dtype=np.complex64,
    seed=None,
) -> cirq.Result
```

Result histogram methods:

```python
result.histogram(key, fold_func=None, fold_base=None) -> collections.Counter
result.multi_measurement_histogram(keys, fold_func=...) -> collections.Counter
```

Parameter sweeps:

```python
cirq.Linspace(key, start, stop, length)
cirq.Points(key, points)
# Also accepted by sweep-aware methods: dictionaries and lists of dictionaries.
```

Common channels and noise models:

```python
cirq.depolarize(p, n_qubits=1)
cirq.amplitude_damp(gamma)
cirq.phase_damp(gamma)
cirq.bit_flip(p=None)
cirq.ConstantQubitNoiseModel(qubit_noise_gate, prepend=False)
circuit.with_noise(noise) -> cirq.Circuit
```

Histogram plotting:

```python
cirq.plot_state_histogram(
    data,
    ax=None,
    tick_label=None,
    xlabel='qubit state',
    ylabel='result count',
    title='Result State Histogram',
)
```

`data` may be a `cirq.Result`, a histogram `Counter`, or a numeric sequence. Pass an explicit Matplotlib axis in production code so plot ownership is clear.

## `run` versus `simulate`

- `run` and `run_sweep` emulate repeated hardware-like sampling. They require explicit measurements for useful output and return `cirq.Result` objects.
- `simulate` and `simulate_sweep` return trial-result objects with final state data such as a state vector or density matrix, depending on the simulator.
- Measurement in a circuit may collapse simulated state. If the goal is a final state before measurement, simulate a measurement-free circuit or split the circuit at the intended observation point.
- `qubit_order` controls state-vector or density-matrix basis ordering. Specify it when comparing amplitudes, bitstrings, or expected arrays.

## Results and histograms

A `cirq.Result` stores measurement arrays by key. Use exact measurement keys:

```python
counts = result.histogram(key='m')
combined = result.multi_measurement_histogram(keys=['a', 'b'])
```

`histogram` folds measured bits into integer outcomes by default. Use `fold_func` when you need custom labels, tuples, parity, or post-processing. Use `multi_measurement_histogram` when the outcome is a joint event across multiple measurement keys.

## Parameter resolution and sweeps

Common sweep inputs:

```python
# Single resolver.
result = sim.run(circuit, param_resolver={'theta': 0.25}, repetitions=100)

# Explicit list of resolver dictionaries.
results = sim.run_sweep(circuit, params=[{'theta': 0.0}, {'theta': 0.5}], repetitions=100)

# Generated sweep.
sweep = cirq.Linspace('theta', start=0.0, stop=1.0, length=5)
results = sim.run_sweep(circuit, params=sweep, repetitions=100)

# Chosen points.
points = cirq.Points('theta', [0.0, 0.25, 0.5])
```

For unresolved-symbol failures, inspect the circuit's parameter names, make sure string keys match the symbolic names, or pre-resolve with `cirq.resolve_parameters(circuit, resolver)` before execution.

## Local noise APIs

Use channels as gates on qubits or wrap them in a noise model:

```python
q = cirq.LineQubit(0)
channel_op = cirq.amplitude_damp(0.1)(q)
noise = cirq.ConstantQubitNoiseModel(cirq.amplitude_damp(0.1))
noisy_circuit = circuit.with_noise(noise)
```

Guidance:

- `depolarize`, `phase_damp`, `amplitude_damp`, and `bit_flip` take probabilities or damping parameters in the closed interval `[0, 1]`.
- Pass `n_qubits=2` to `depolarize` when modeling a two-qubit depolarizing channel.
- `ConstantQubitNoiseModel` applies the same qubit noise gate throughout a circuit. Use `prepend=True` only when noise should be inserted before operations instead of after them.
- For exact mixed-state effects of non-unitary channels, prefer `DensityMatrixSimulator` and inspect `final_density_matrix`.
