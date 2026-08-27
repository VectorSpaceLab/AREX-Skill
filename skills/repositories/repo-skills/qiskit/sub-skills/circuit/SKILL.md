---
name: circuit
description: "Guides agents building and editing QuantumCircuit objects,
  registers, bits, gates, control flow, measurements, resets, and
  circuit-library compositions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Qiskit circuit workflows

Use this sub-skill when the task is about constructing or editing quantum circuits with `qiskit.circuit`: `QuantumCircuit`, registers, bits, parameters, gate composition, control flow, measurements, resets, and circuit-library building blocks.

## Read next

- `references/workflows.md` for build, compose, control-flow, and circuit-library recipes.
- `references/troubleshooting.md` for `CircuitError`, parameter binding, and control-flow mistakes.
- `../../references/module-map.md` for the top-level package boundaries.
- `../../scripts/check_qiskit_environment.py --sections core` for a source-free circuit sanity check.

## Include here

- Circuit construction and mutation with `QuantumCircuit`.
- Register and bit handling with `QuantumRegister`, `ClassicalRegister`, `AncillaRegister`, `Qubit`, and `Clbit`.
- Gate application, inversion, control, append/compose, and circuit-library helpers.
- Classical control-flow builders and conditions on circuit internals.
- Measurement, reset, barrier, and lightweight circuit introspection.

## Exclude or route elsewhere

- Backend-targeted compilation, `Target`, `CouplingMap`, and pass-manager workflows belong in `../transpiler/SKILL.md`.
- Primitive execution, `Sampler`, `Estimator`, and result containers belong in `../primitives/SKILL.md`.
- OpenQASM/QPY import-export belongs in `../serialization/SKILL.md`.
- State/operator mathematics belongs in `../quantum-info/SKILL.md`.
- Drawing output formats and plot styling belong in `../visualization/SKILL.md`.

## Default route

If the user has not yet built a valid abstract circuit, start here before moving to transpilation or execution. A good first answer is usually a minimal `QuantumCircuit` example and then a circuit-specific recipe from the workflows reference.

## What to remember

- Circuit methods often mutate in place unless the API explicitly says otherwise.
- `measure_all()` creates or reuses a classical register; `remove_final_measurements()` is useful before operator/state analysis or transpilation experiments.
- Control-flow objects carry their own classical-resource constraints. A condition that fits one circuit may not fit another.
- Circuit composition and library gates are usually more useful than manually editing low-level instruction tuples.
