---
name: core-circuits-and-ops
description: "Build, inspect, mutate, serialize, and debug Cirq circuits and
  core operation objects."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Core Circuits and Operations

Use this sub-skill when the task is about Cirq's core object model: qubits/qids,
gates, operations, moments, circuits, circuit diagrams, measurement keys, tags,
controls, symbolic parameters, custom gates, and basic object serialization.

## Stay in this sub-skill for

- Choosing or constructing `LineQubit`, `GridQubit`, `NamedQubit`, `LineQid`, or
  `GridQid` objects.
- Building and mutating `Gate`, `Operation`, `Moment`, `Circuit`,
  `FrozenCircuit`, and `CircuitOperation` objects.
- Using `Circuit.append`, `Circuit.insert`, `InsertStrategy`, OP trees,
  `findall_operations`, measurement keys, operation tags, controls, and
  classically controlled operations.
- Resolving symbolic parameters with `ParamResolver` and `resolve_parameters`.
- Using core protocols such as `unitary`, `has_unitary`, `decompose`, `inverse`,
  `qid_shape`, and `circuit_diagram_info` for debugging custom or built-in
  objects.
- Basic JSON, QASM, and Quirk interop at the circuit-object level.

## Route away when

- The user needs sampling, state vectors, density matrices, result histograms,
  parameter sweeps as execution, or noise simulation: use
  `simulation-study-and-noise`.
- The user needs circuit transformers, optimization, decomposition pipelines,
  routing, target gatesets, or placement: use `transformers-and-compilation`.
- The user needs cloud/hardware provider serializers, live services, credentials,
  or provider-specific package behavior: use `hardware-providers-and-serialization`.
- The user needs algorithm recipes, Pauli observables, expectation values, or
  textbook algorithm interpretation: use `algorithms-and-observables`.

## Operating routine

1. Identify whether the task is object construction, mutation, inspection,
   parameters, protocols, or interop.
2. For exact signatures and object-model facts, read
   [references/api-reference.md](references/api-reference.md).
3. For common build/debug recipes, read
   [references/workflows.md](references/workflows.md).
4. For known failure modes, read
   [references/troubleshooting.md](references/troubleshooting.md).
5. For a safe local smoke helper, run
   [scripts/inspect_circuit.py](scripts/inspect_circuit.py) with `--help`, then
   run it with optional `--json` or `--qubits N`.

## Bundled assets

- [references/api-reference.md](references/api-reference.md) — verified public
  API signatures and compact examples for core Cirq objects.
- [references/workflows.md](references/workflows.md) — task-oriented recipes for
  construction, mutation, parameter resolution, custom gates, and interop.
- [references/troubleshooting.md](references/troubleshooting.md) — symptom-based
  fixes for unresolved parameters, duplicate measurement keys, protocol failures,
  qid-shape mismatches, JSON resolver issues, QASM limits, and insert strategy
  surprises.
- [scripts/inspect_circuit.py](scripts/inspect_circuit.py) — deterministic helper
  that builds a small parameterized circuit, prints diagrams, validates
  measurement-key uniqueness, and optionally performs a JSON roundtrip.
