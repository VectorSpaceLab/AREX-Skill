# Concepts and Runtime Boundaries

Read this reference when a task combines authoring, simulation, compilation,
noise, experiments, and hardware-shaped metadata. The key question is not only
which API to call, but what evidence the call can produce.

## Object flow

```text
Program / Quil text
  -> local serialization and validation
  -> compiler (quilc or QPU compiler)
  -> executable / native Quil
  -> QAM (PyQVM, QVM, or QPU)
  -> QAMExecutionResult / raw readout / duration
```

`Program.out()` and `Program(quil_text)` exercise the authoring/serialization
layer. They do not prove that a compiler accepts the program. `QuantumComputer`
connects a compiler, a quantum abstract machine, and a quantum processor
metadata object; these components must describe the same target.

## Service-free and service-backed paths

- `PyQVM(n_qubits, seed=...)` is PyQuil's in-process QAM-shaped virtual machine.
  It is useful for local execution, measurement, control flow, and deterministic
  smoke tests. Its supported instruction set and numerical backend still have
  limits.
- `ReferenceWavefunctionSimulator` and `NumpyWavefunctionSimulator` are
  in-process gate simulators. They are useful for statevector calculations but
  do not replace QAM/compiler semantics.
- `pyquil.api.WavefunctionSimulator` is a client for QVM HTTP wavefunction,
  expectation, and measurement endpoints. A missing QVM produces a connection
  error; an import or object construction is not a service pass.
- `get_qc("...-qvm")` normally assembles a QVM-oriented `QuantumComputer`,
  while a QPU name requires QCS configuration and access. `qc.compile()` and
  `qc.run()` are service/backend operations unless the chosen objects are
  explicitly local/in-process.

## Model and metadata boundaries

A `NoiseModel`, `PauliTerm`, `Experiment`, `CompilerISA`, or NetworkX topology
is a local model or target description. Applying a noise model to a Program
creates transformed Quil; it does not execute that Quil. An ISA may contain
fidelity/duration metadata, but it does not establish that the corresponding
processor is live, reserved, reachable, or calibrated.

## Evidence checklist

For every result record:

1. PyQuil version and selected engine/target.
2. Qubit count and canonical qubit/shot column ordering.
3. Seed, noise model, memory map, and shot policy when relevant.
4. Whether a compiler, QVM, QPU, QCS, or external binary was contacted.
5. Which assertions were local construction checks versus backend observations.
6. Missing prerequisites and the exact next action instead of a guessed result.

PyQuil 4.18.0 supports Python `>=3.11, <3.13` in its package metadata. Keep
public guidance generic: never copy a local environment path, editable-install
location, or secret-bearing configuration into a runtime skill.
