---
name: processor-isa
description: "Inspect, construct, and validate pyQuil quantum-processor
  topologies and compiler/QCS instruction-set architectures without confusing
  local metadata with backend execution."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Processor topology and ISA

Use this sub-skill when the task is about the hardware-shaped metadata that a
pyQuil compiler targets: qubit connectivity, supported native gates, dead
resources, `CompilerISA`, QCS `InstructionSetArchitecture`, or a custom
processor used to assemble a QVM/QPU-shaped `QuantumComputer`.

## Route first

- Use [processor-types.md](references/processor-types.md) for the processor
  class hierarchy, exact accessors, gate vocabulary, and compiler/QAM
  compatibility boundaries.
- Use [isa-conversion.md](references/isa-conversion.md) for conversion
  direction, JSON-shaped RPCQ data, QCS parsing, dead-resource semantics, and
  malformed-input behavior.
- Use [workflows.md](references/workflows.md) for custom-topology construction,
  offline fixture inspection, and choosing a local QVM mimic versus a service
  target.
- Use [troubleshooting.md](references/troubleshooting.md) when conversion,
  connectivity, gate-set, credentials, or backend compatibility fails.
- Run [scripts/topology_isa_smoke.py](scripts/topology_isa_smoke.py) for a
  deterministic, network-free sanity check. It deliberately includes an
  isolated qubit and reports the known graph round-trip limitation.

For program syntax and qubit placeholders, route to
[program-authoring](../program-authoring/SKILL.md). For compilation, QAM
execution, QVM/QPU services, and result handling, route to
[compile-execute](../compile-execute/SKILL.md). For numerical local state
simulation, route to [simulation](../simulation/SKILL.md). For construction of
noise channels or experiment noise, route to
[noise-experiments](../noise-experiments/SKILL.md); only the processor/noise
attachment boundary belongs here.

## Operating model

A processor object is metadata, not a job. `AbstractQuantumProcessor` requires
three operations:

1. `qubits() -> list[int]`: sorted qubit identifiers.
2. `qubit_topology() -> networkx.Graph`: connectivity graph.
3. `to_compiler_isa() -> CompilerISA`: compiler target representation.

Use `NxQuantumProcessor` when the topology and uniform gate lists are authored
locally, `CompilerQuantumProcessor` when a `CompilerISA` is already the source
of truth, and `QCSQuantumProcessor` when an installed QCS SDK ISA has already
been obtained. `get_qcs_quantum_processor(id, client_configuration=None,
timeout=10.0)` is the credential/network-fetching convenience function; do not
use it for offline validation.

## Safe construction sequence

1. Pick numeric, non-negative qubit labels and create a simple undirected
   `networkx.Graph`. Add isolated nodes explicitly with `add_node`; creating a
   graph only from edges omits them.
2. Construct `NxQuantumProcessor(graph, gates_1q=..., gates_2q=...)`.
   Supported names are listed in [processor-types.md](references/processor-types.md).
   Start with a constrained set rather than assuming every Quil gate is native.
3. Inspect `qubits()`, `edges()` (on `NxQuantumProcessor`), graph nodes/edges,
   and the returned ISA's `qubits`/`edges` dictionaries before compiling.
4. Call `to_compiler_isa()` and validate that every intended 1Q/2Q operation is
   present on the intended resource. Catch `GraphGateError` for unsupported
   operation names.
5. Use the smoke helper or an equivalent assertion set. Preserve the original
   graph as the topology authority: `compiler_isa_to_graph` reconstructs edges
   but does not add isolated ISA qubits as graph nodes.
6. Only then hand the processor to a matching compiler/QAM assembly. Metadata
   validation does not prove that `quilc`, QVM, QPU, or QCS is reachable.

## Compatibility rules

The `QuantumComputer` exposes its compiler's
`quantum_processor`. Its compiler serializes `to_compiler_isa()` into the
compiler target device. Therefore the compiler, QAM, processor labels, ISA
operations, and (for a QPU) processor id must describe the same target. A
custom topology can support a QVM mimic, but it does not grant QPU access.
Keep compile/run instructions in [compile-execute](../compile-execute/SKILL.md).

For a service-free mimic, use the in-process `PyQVM` path owned by the
simulation/compile-execute skills and keep qubit labels compatible with its
integer indexing. A QVM-backed or QPU-backed compiler/executor still needs its
respective service, endpoint, and configuration. An optional
`QCSQuantumProcessor.noise_model` is only an attachment consumed by a suitable
noisy QVM path; model construction belongs to
[noise-experiments](../noise-experiments/SKILL.md).

## Resource semantics

`graph_to_compiler_isa` creates ISA qubits for every integer in
`range(max(graph.nodes) + 1)`. Labels absent from the graph become `dead=True`;
non-contiguous labels therefore create explicit dead gaps. An explicitly
isolated graph node receives the requested 1Q gates and is not dead, but the
current edge-list-based reverse transformer drops it from the returned graph.
An ISA qubit or edge with `dead=True` (often with no gates) must not be treated
as usable connectivity. An edge can be present yet unusable if its gate list is
empty/dead.

Do not infer live calibration, fidelity, duration, reservation, or endpoint
health from an ISA alone. QCS conversion can carry fidelity/duration metadata
where the source ISA supplies it, but that remains a description snapshot.

For concrete invariants and JSON-safe output, run:

```bash
python scripts/topology_isa_smoke.py
python scripts/topology_isa_smoke.py --help
```

The helper performs no network calls, reads no credentials, starts no service,
and writes no files.
