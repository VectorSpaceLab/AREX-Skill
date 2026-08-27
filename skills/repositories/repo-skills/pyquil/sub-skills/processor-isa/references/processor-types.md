# Processor types and compatibility

## Common interface

`AbstractQuantumProcessor` is an ABC describing topology and compiler
representation. Implementations provide:

| Method | Result | Use |
|---|---|---|
| `qubits()` | sorted `list[int]` | Declared processor qubit IDs |
| `qubit_topology()` | `networkx.Graph` | Undirected connectivity view |
| `to_compiler_isa()` | `pyquil.external.rpcq.CompilerISA` | Target-device metadata |

The abstract base does not execute programs. Treat a returned graph or ISA as a
snapshot and inspect it before passing it to a compiler.

## `NxQuantumProcessor`

```python
import networkx as nx
from pyquil.quantum_processor import NxQuantumProcessor

qproc = NxQuantumProcessor(
    topology=nx.Graph([(0, 1)]),
    gates_1q=["RX", "RZ", "MEASURE"],
    gates_2q=["CZ"],
)
```

Installed signatures are:

```text
NxQuantumProcessor(topology: networkx.Graph,
                   gates_1q: list[str] | None = None,
                   gates_2q: list[str] | None = None) -> None
qproc.qubits() -> list[int]
qproc.edges() -> list[tuple[Any, ...]]
qproc.qubit_topology() -> networkx.Graph
qproc.to_compiler_isa() -> CompilerISA
```

`qubit_topology()` returns the same graph object supplied at construction.
`qubits()` sorts `topology.nodes`; `edges()` canonicalizes each endpoint by
sorting it and then sorts the edge list. The constructor stores gate lists; the
conversion occurs when `to_compiler_isa()` is called.

The graph transformer currently expects edge iteration yielding pairs. A plain
undirected `nx.Graph` is the supported shape. An `nx.DiGraph` happens to work
for simple pairs but directed meaning is not represented in the resulting
undirected compiler graph. A `MultiGraph` edge iterator includes edge keys when
requested by NetworkX APIs and is not a safe input contract; collapse it to a
simple graph after deciding which duplicate edges to retain.

### Gate vocabulary

The graph transformer recognizes these exact names:

| Scope | Names | Resulting operation shape |
|---|---|---|
| 1Q | `I` | `GateInfo(operator="I", parameters=[], arguments=["_"])` |
| 1Q | `RX` | five fixed angles: `0`, `±pi`, `±pi/2` |
| 1Q | `RZ` | symbolic `theta` |
| 1Q | `MEASURE` | measured target and no-target variants |
| 1Q | `WILDCARD` | wildcard gate |
| 2Q | `CZ` | no parameters |
| 2Q | `ISWAP` | no parameters |
| 2Q | `CPHASE` | symbolic `theta` |
| 2Q | `XY` | symbolic `theta` |
| 2Q | `WILDCARD` | wildcard gate |

With `None` or an empty list, the transformer uses defaults (the implementation
uses `gates_1q or DEFAULT_1Q_GATES` and the corresponding 2Q expression):
`I`, `RX`, `RZ`, `MEASURE` and `CZ`, `XY`. To request no operations, do not
assume an empty list is distinct from omitted defaults; verify the installed
behavior and prefer a deliberately constructed `CompilerISA` when an empty
operation set is required.

Unknown names raise `GraphGateError`, a `ValueError` subclass, with either
`Unsupported graph qubit operation: ...` or `Unsupported graph edge operation:
...`. The 1Q list is applied uniformly to every ISA qubit and the 2Q list
uniformly to every graph edge; per-resource variation requires editing or
constructing an ISA rather than using `NxQuantumProcessor`'s uniform lists.

## `CompilerQuantumProcessor`

```python
from pyquil.quantum_processor import CompilerQuantumProcessor
qproc = CompilerQuantumProcessor(isa)
```

The constructor accepts one `CompilerISA`. `to_compiler_isa()` returns the same
ISA object, so treat it as mutable shared state. `qubits()` sorts integer values
from the ISA's qubit dictionary keys/entries. `qubit_topology()` calls
`compiler_isa_to_graph`, which builds an `nx.Graph` from ISA edge IDs. It does
not preserve isolated qubits, dead flags, gate lists, or direction.

## `QCSQuantumProcessor`

```python
from pyquil.quantum_processor import QCSQuantumProcessor
qproc = QCSQuantumProcessor("processor-id", qcs_isa, noise_model=None)
```

Installed signature:

```text
QCSQuantumProcessor(quantum_processor_id: str,
                    isa: qcs_sdk.qpu.isa.InstructionSetArchitecture,
                    noise_model: NoiseModel | None = None)
get_qcs_quantum_processor(quantum_processor_id: str,
                          client_configuration: QCSClient | None = None,
                          timeout: float = 10.0)
```

`QCSQuantumProcessor.qubits()` reads `isa.architecture.nodes`,
`qubit_topology()` calls `qcs_isa_to_graph`, and `to_compiler_isa()` calls
`qcs_isa_to_compiler_isa`. The QCS object is an installed SDK model, not the
legacy RPCQ `CompilerISA`. `get_qcs_quantum_processor` invokes the QCS SDK
fetch path and can need credentials/network; use only when that boundary is
intentional. The timeout parameter is part of pyQuil's wrapper signature, but
the current source passes the client and processor ID to the SDK fetch call;
do not claim a live timeout or successful query without an actual service
probe.

`noise_model` may be stored on the processor for a noisy QVM assembly. It does
not change topology conversion and does not make a QPU noisy; noise model
construction and experiment semantics are owned by
`../noise-experiments/SKILL.md`.

## Compiler/QAM alignment

A `QuantumComputer` has a QAM, compiler, and processor. The compiler target is
made from `quantum_processor.to_compiler_isa()` and serialized through the
RPCQ compatibility conversion to a compiler target device. The QAM must accept
an executable compiled for the same target. For a QPU, the QPU and QPUCompiler
also use the same processor ID; for a QVM topology mimic, use the matching QVM
compiler and QVM/PyQVM dimensions. A successful metadata conversion is not a
successful compile or execution.
