# Qiskit module map

This file gives a quick, public overview of the main package surfaces. Read it when you need a mental model before drilling into a sub-skill.

| Module | What it owns | Useful entry points | Typical route |
| --- | --- | --- | --- |
| `qiskit.circuit` | Quantum circuits, registers, bits, gates, control flow, and circuit-library objects | `QuantumCircuit`, `QuantumRegister`, `ClassicalRegister`, `AncillaRegister`, `Instruction`, `Gate`, `control-flow` builders | `sub-skills/circuit/SKILL.md` |
| `qiskit.transpiler` | Compilation pipelines, `Target`, coupling maps, layouts, routing, optimization, scheduling, and preset pass managers | `transpile`, `generate_preset_pass_manager`, `Target.from_configuration`, `CouplingMap`, `Layout`, `PassManager` | `sub-skills/transpiler/SKILL.md` |
| `qiskit.primitives` | Sampler and estimator primitives plus PUB/result container classes | `StatevectorSampler`, `StatevectorEstimator`, `PrimitiveResult`, `PubResult`, `DataBin`, `BitArray` | `sub-skills/primitives/SKILL.md` |
| `qiskit.qasm2` / `qiskit.qasm3` / `qiskit.qpy` | Text and binary serialization, import/export, version and compatibility behavior | `load`, `loads`, `dump`, `dumps`, `load_experimental`, `loads_experimental`, `QPY_VERSION` | `sub-skills/serialization/SKILL.md` |
| `qiskit.quantum_info` | States, operators, channels, random generators, predicates, and fidelity/entropy-style measures | `Statevector`, `Operator`, `SparsePauliOp`, `Pauli`, `Clifford`, `random_unitary`, `diamond_norm` | `sub-skills/quantum-info/SKILL.md` |
| `qiskit.visualization` | Circuit drawers, histograms, state plots, backend maps, pass-manager drawings, and timeline views | `circuit_drawer`, `plot_histogram`, `plot_distribution`, `plot_state_city`, `plot_gate_map` | `sub-skills/visualization/SKILL.md` |
| `qiskit.providers` / `qiskit.providers.basic_provider` / `qiskit.providers.fake_provider` | Backend abstractions, job status, options, local simulators, and fake backends for transpiler workflows | `BackendV2`, `Options`, `BasicProvider`, `BasicSimulator`, `GenericBackendV2` | `sub-skills/providers/SKILL.md` |
| `qiskit.capi` | Public C headers, shared library location, and ctypes bindings for Qiskit's C API | `get_include`, `get_lib`, `qiskit.capi.*` symbols | `sub-skills/c-api/SKILL.md` |

The package root `qiskit` re-exports the most common circuit, transpiler, primitives, providers, serialization, quantum-info, and visualization entry points. Use the specific submodule pages when you need non-trivial arguments, optional dependencies, or failure modes.
