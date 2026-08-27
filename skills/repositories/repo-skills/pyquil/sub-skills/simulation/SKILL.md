---
name: simulation
description: "Choose and operate PyQuil's in-process and service-backed
  simulators, inspect quantum states and observables, and diagnose ordering,
  noise, random-state, and scaling failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PyQuil simulation

Use this route when the task is to simulate a small Quil `Program`, inspect a
wavefunction or density matrix, calculate Pauli expectations, sample outcomes,
construct simulation matrices, or decide whether a QVM service is required.
This route assumes a usable PyQuil installation and a concrete qubit count.
For general program construction, use [program-authoring](../program-authoring/SKILL.md).
For compilation, `QuantumComputer`, QVM/QPU jobs, or QCS orchestration, use
[compile-execute](../compile-execute/SKILL.md). For complete channel,
readout, and Experiment workflows, use [noise-experiments](../noise-experiments/SKILL.md).

## First decision: local or service-backed

- **Service-free local simulation:** choose `PyQVM` for a QAM-shaped execution
  path, or use `ReferenceWavefunctionSimulator`/`NumpyWavefunctionSimulator`
  directly for a gate-only numerical path. `PyQVM(n_qubits=..., seed=...)`
  supplies a shared random state and is the safest default when measurement,
  sampling, control flow, or repeatable noise is involved.
- **Service-backed wavefunction:** `pyquil.api.WavefunctionSimulator` is a
  client for the QVM HTTP wavefunction/expectation/measurement endpoints. It
  is **not** an in-process simulator. With no QVM service, its
  `.wavefunction(...)` call attempts HTTP and raises `api.QVMError` (typically
  beginning `Could not communicate with QVM at ...`). Do not use it to prove
  service-free execution.
- **Density/noise:** `PyQVM` with `post_gate_noise_probabilities` selects
  `ReferenceDensitySimulator` by default. This is an experimental post-gate
  single-qubit Kraus path, not the full noise/Experiment API; route the latter
  to [noise-experiments](../noise-experiments/SKILL.md).

Read [simulator-selection.md](references/simulator-selection.md) before choosing
an engine, especially when a request mentions QVM, noise, state injection, or
many qubits.

## Minimal local workflow

1. Build or receive a `Program` from [program-authoring](../program-authoring/SKILL.md).
   Count the qubits explicitly; `PyQVM` allocates the full Hilbert space.
2. For a gate-only state, use `ReferenceWavefunctionSimulator(n_qubits)` or
   `NumpyWavefunctionSimulator(n_qubits)`, then `.do_program(program)`.
3. For Quil/QAM semantics, use `PyQVM(n_qubits, seed=integer).execute(program)`.
   Execution requires a `Program`, resets the simulator at each `execute` call,
   and returns the stateful `PyQVM`; inspect `qam.wf_simulator`.
4. Validate the state before interpreting it: a wavefunction has `2**n`
   amplitudes; the NumPy tensor has shape `(2,) * n`; a density matrix has
   shape `(2**n, 2**n)`, is Hermitian, and has trace one.
5. Convert results into the requested representation. Read
   [state-and-observables.md](references/state-and-observables.md) for exact
   bit ordering, `Wavefunction` helpers, expectations, density observables,
   sampling, and matrix lifting.
6. Run the [bundled deterministic Bell check](scripts/bell_state_inprocess.py)
   when a service-free smoke test is needed:
   `python scripts/bell_state_inprocess.py`. Use
   `python scripts/bell_state_inprocess.py --help` to inspect its interface;
   it performs no network call or file write.

## Engine-specific operating rules

- `ReferenceWavefunctionSimulator` stores a flat canonical vector and favors
  readable reference behavior. `NumpyWavefunctionSimulator` stores an
  n-dimensional tensor and is the default `PyQVM` backend without noise.
  Compare the NumPy tensor after reversing axes and flattening when comparing
  it with the reference vector.
- Direct simulators can apply gates and compute expectations, but stochastic
  measurement/sampling needs `rs`. Instantiate them with a
  `numpy.random.RandomState`, or prefer `PyQVM(seed=...)` so all stochastic
  actions share one deterministic stream.
- `ReferenceDensitySimulator` stores a dense matrix and supports the
  experimental post-gate noise names `relaxation`, `dephasing`,
  `depolarizing`, `phase_flip`, `bit_flip`, and `bitphase_flip`. Its current
  `expectation` method raises `NotImplementedError`; compute `Tr(rho O)` with
  a lifted Pauli matrix for a local diagnostic, or route full observable and
  Experiment work to [noise-experiments](../noise-experiments/SKILL.md).
- A direct simulator's `do_program` is gate-only. `PyQVM` adds classical
  memory/control-flow plumbing, measurement, and ordinary `Program`
  execution, but still rejects several instructions and parameterized
  `DEFGATE`s. Treat a failure as a backend capability issue, not automatically
  as a malformed program. See [api-reference.md](references/api-reference.md)
  and [troubleshooting.md](references/troubleshooting.md).

## Numerical and resource guardrails

- PyQuil's canonical basis vector order is `00, 01, 10, 11, ...`, with qubit
  `0` as the least-significant/rightmost bit. Thus index `1` is bitstring `01`
  and means q0=1. Measurement arrays and user-selected qubit lists can use a
  different column presentation; never infer labels from array positions alone.
- A complex128 statevector needs `16 * 2**n` bytes; a dense complex128 density
  matrix needs `16 * 4**n` bytes, before temporary lifted matrices. Estimate
  memory before allocating and stop early for an exponential-size request.
- Use [api-reference.md](references/api-reference.md) for verified signatures
  and [state-and-observables.md](references/state-and-observables.md) for
  concrete shapes and matrix-ordering recipes. Use
  [troubleshooting.md](references/troubleshooting.md) for recovery when a
  state is invalid, random state is absent, noise is incompatible, or a QVM
  boundary was mistaken for local execution.

## Handoff checks

Before claiming a simulation result, record the engine and version, qubit
count, seed policy, whether noise was applied, state shape, basis convention,
and whether any service was contacted. Assert normalization and the expected
ordering for at least one basis state. For Bell-like checks, compare vector,
probabilities, `XX`/`YY`/`ZZ` expectations, and sampled bitstring columns across
reference and PyQVM paths rather than comparing only a pretty-printed string.
