---
name: simulation-study-and-noise
description: "Run local Cirq simulator, sampler, sweep, histogram, state,
  density-matrix, Clifford, and noisy-channel workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Simulation, study, and noise

Use this sub-skill when a task asks you to execute Cirq programs locally, choose a simulator or sampler, run parameter sweeps, inspect measurement results, visualize histograms, simulate state vectors or density matrices, or add local noise/channels.

## Route here for

- `cirq.Simulator`, `cirq.DensityMatrixSimulator`, `cirq.CliffordSimulator`, and `cirq.sample`.
- `run`, `run_sweep`, `simulate`, and `simulate_sweep` decisions.
- `Result.histogram`, `Result.multi_measurement_histogram`, and `plot_state_histogram` usage.
- `Linspace` and `Points` sweeps, parameter resolver troubleshooting, and repeated sampling.
- Local noisy simulation with `depolarize`, `amplitude_damp`, `phase_damp`, `bit_flip`, `ConstantQubitNoiseModel`, and `Circuit.with_noise`.

## Route elsewhere

- Circuit object construction, custom gates, qids, measurement-key basics, JSON/QASM object handling: `core-circuits-and-ops`.
- Circuit transformation, decomposition, target-gateset optimization, routing, and compilation before simulation: `transformers-and-compilation`.
- Cloud samplers, provider credentials, hardware jobs, and provider serializers: `hardware-providers-and-serialization`.
- Algorithm design, Pauli observables, expectation-value workflows, and textbook circuit recipes: `algorithms-and-observables`.

## Operating checklist

1. Decide whether the user needs samples, sweeps, or final state data.
2. Choose the smallest adequate backend: pure-state `Simulator`, mixed-state `DensityMatrixSimulator`, stabilizer-only `CliffordSimulator`, or quick `cirq.sample`.
3. Ensure all symbolic parameters are resolved through a resolver or sweep before numeric simulation.
4. Ensure sampling circuits have explicit measurement keys, then read counts through `Result` histogram methods.
5. For non-unitary channels/noise models, use density-matrix simulation when the post-noise state itself matters.
6. Set seeds for deterministic demonstrations and tests; treat noisy counts as statistical unless repetitions and seed are controlled.

## Bundled references and script

- API signatures and simulator-selection guide: [references/api-reference.md](references/api-reference.md)
- End-to-end local workflows: [references/workflows.md](references/workflows.md)
- Simulator and histogram troubleshooting: [references/troubleshooting.md](references/troubleshooting.md)
- Safe local noisy-sampling smoke demo: [scripts/run_noisy_smoke.py](scripts/run_noisy_smoke.py)
