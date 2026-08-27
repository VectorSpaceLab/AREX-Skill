# Processor/ISA workflows

## A. Build and validate a custom topology

Use this for a local processor definition or a QVM mimic. It does not contact
QCS, QVM, or quilc.

```python
import networkx as nx
from pyquil.quantum_processor import NxQuantumProcessor
from pyquil.quantum_processor.transformers import compiler_isa_to_graph

# Include isolated nodes explicitly.
topology = nx.Graph()
topology.add_nodes_from([0, 1, 2])
topology.add_edge(0, 1)
processor = NxQuantumProcessor(
    topology,
    gates_1q=["RX", "RZ", "MEASURE"],
    gates_2q=["CZ"],
)
isa = processor.to_compiler_isa()
assert processor.qubits() == [0, 1, 2]
assert processor.edges() == [(0, 1)]
assert set(isa.qubits) == {"0", "1", "2"}
assert set(isa.edges) == {"0-1"}
assert not isa.qubits["2"].dead
assert {gate.operator for gate in isa.edges["0-1"].gates} == {"CZ"}

round_trip = compiler_isa_to_graph(isa)
assert set(round_trip.edges) == {(0, 1)}
# The transformer is edge based; restore/check isolated nodes deliberately.
round_trip.add_nodes_from(processor.qubits())
assert set(round_trip.nodes) == {0, 1, 2}
```

Use `scripts/topology_isa_smoke.py` for the same check plus JSON-safe summary.
If the chosen gate set is narrower than a program's operations, that is a
compiler-target mismatch, not a simulation result. Route program construction
to `../../program-authoring/` and compile/run to `../../compile-execute/`.

## B. Build from an existing `CompilerISA`

When a compiler ISA or fixture is authoritative:

```python
from pyquil.external.rpcq import CompilerISA
from pyquil.quantum_processor import CompilerQuantumProcessor

isa = CompilerISA.parse_obj(payload)  # compatibility API; deprecated warning
processor = CompilerQuantumProcessor(isa)
print(processor.qubits())
print(processor.qubit_topology().edges)
```

For long-lived code, keep the source payload in the current RPCQ-shaped schema
(`1Q`/`2Q`) and consider constructing `CompilerISA`, `Qubit`, `Edge`, and
`GateInfo` directly rather than depending on deprecated public parsers. Before
using the processor, inspect `dead` and gate lists; `CompilerQuantumProcessor`
does not infer missing edges or resurrect dead resources.

A fixture can be converted to a QCS compiler target with the compatibility
helper only at the compiler boundary. Do not make `dict(by_alias=True)` output
a claim that a QCS endpoint was queried.

## C. Convert/inspect a QCS ISA offline

If a task supplies a QCS ISA JSON fixture, load it into the installed QCS SDK
model and transform it without fetching:

```python
import json
from qcs_sdk.qpu.isa import InstructionSetArchitecture
from pyquil.quantum_processor import QCSQuantumProcessor

with open("provided-isa.json", encoding="utf-8") as handle:
    qcs_isa = InstructionSetArchitecture.from_raw(handle.read())
processor = QCSQuantumProcessor("fixture-id", qcs_isa)
compiler_isa = processor.to_compiler_isa()
graph = processor.qubit_topology()
```

Validate every operation's `node_count` against every site's `node_ids` before
transformation. Catch `QCSISAParseError`, and also catch `IndexError` for the
current malformed 2Q short-site behavior. Compare architecture node/edge sets
with compiler ISA sets and inspect `dead` flags. This workflow can prove that a
fixture parses and converts; it cannot prove that the named QPU exists,
calibrations are current, or credentials work.

## D. Choose a service-free mimic or service-backed target

| Need | Processor choice | Execution boundary |
|---|---|---|
| Local topology/ISA reasoning | `NxQuantumProcessor` or `CompilerQuantumProcessor` | No service required for metadata |
| Local in-process QVM-like execution | Custom processor + `PyQVM` assembly | No QVM HTTP; simulation limitations still apply |
| QVM with compiler/QAM services | custom processor or QCS-derived processor + `QVMCompiler`/`QVM` | quilc/QVM endpoints and compatible clients required |
| Real QPU | `QCSQuantumProcessor` + `QPUCompiler`/`QPU` with same processor ID | QCS credentials, network, reservations/endpoints as applicable |

The source docs describe `get_qc("processor-id", as_qvm=True)` as a QVM
mimic of a named QPU, but that convenience call first fetches QCS ISA metadata.
For an offline/deterministic task, do not call it; construct from a supplied
fixture or local graph. A custom graph only defines a target shape and gate set.
It does not emulate hardware fidelity, timing, calibration, queueing, or QPU
availability.

## E. Attach a noise model without crossing ownership

A `QCSQuantumProcessor` can store `noise_model=...`; custom QVM assembly may
also derive a noise model from a `CompilerISA`. This sub-skill checks only that
the processor and model refer to compatible qubit IDs and operations. Build and
validate channels, readout matrices, decoherence, and experiment interpretation
under `../../noise-experiments/`. A topology/ISA conversion cannot validate that a
noise model is CPTP or that an experiment ran.

## F. Handoff to compilation/QAM

Before handing off a custom processor:

1. Freeze the intended qubit labels and edge set.
2. Check the ISA gate set against the program's intended native operations.
3. Check all intended resources are not dead and no required edge is omitted.
4. Build the compiler with this same `AbstractQuantumProcessor`.
5. Build a QAM compatible with the desired path and qubit count/labels.
6. Compile before run on a service-backed path; keep actual lifecycle actions in
   `../../compile-execute/`.
7. Report which checks were local metadata checks and which backend actions were
   not attempted.
