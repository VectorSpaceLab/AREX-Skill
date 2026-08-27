# Processor and ISA troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ValueError: too many values to unpack` while converting a graph | A `MultiGraph`/multiedge iterator or non-pair edge shape was supplied | Collapse to a simple `nx.Graph`; decide which duplicate edges survive; validate `all(len(edge) == 2 ...)`. |
| Directed graph converts but orientation is missing | `graph_to_compiler_isa` and reverse conversion model undirected connectivity | Use `nx.Graph` and treat `(a,b)`/`(b,a)` as one edge; do not infer directional gate support. |
| An isolated graph node is missing after ISA → graph | `compiler_isa_to_graph` and `qcs_isa_to_graph` are edge-list based | Add intended nodes explicitly to the graph after conversion; retain ISA qubit entries as the source of truth. |
| Unexpected dead qubits between sparse labels | Graph conversion creates every integer from `0` to `max(graph.nodes)` and marks absent labels dead | Relabel to contiguous non-negative integers or intentionally inspect the generated dead gap. Do not use dead entries in a program. |
| `GraphGateError: Unsupported graph qubit operation` | 1Q name is outside `I`, `RX`, `RZ`, `MEASURE`, `WILDCARD` | Replace with a supported name or construct/edit a `CompilerISA` with a verified target-device schema. |
| `GraphGateError: Unsupported graph edge operation` | 2Q name is outside `CZ`, `ISWAP`, `CPHASE`, `XY`, `WILDCARD` | Use a supported operation or route custom gate decomposition to compilation/program-authoring. A gate name in a Quil program is not automatically an ISA gate. |
| `QCSISAParseError: Unsupported ... operation` | QCS fixture contains an operation not handled by pyQuil's QCS transformer | Remove/rewrite only if the task permits; otherwise preserve the source ISA and report unsupported conversion rather than silently dropping it. |
| `QCSISAParseError` about missing node/edge | Operation site references resources not declared in `architecture` | Repair or reject the fixture; do not add undeclared topology implicitly. |
| `IndexError` for malformed QCS 2Q site | Current transformer constructs but fails to raise its arity error for a site with fewer than two IDs | Pre-validate `len(site.node_ids) == operation.node_count`; reject the fixture before transformation and report the malformed operation. |
| A QCS operation with three IDs appears to convert | Current code uses the first two IDs after the missing raise | Treat this as malformed and reject it with pre-validation; never accept a partial site. |
| An ISA edge exists but cannot be used | `edge.dead` is true or `edge.gates` is empty | Check dead flags and operation lists per edge; remove the edge from the usable topology or repair the authoritative ISA. |
| An ISA qubit exists but is unusable | `qubit.dead` is true, often due to no supported operations | Do not count the qubit as operational. A topology node's existence alone is insufficient. |
| Edge key/order assertion fails | Numeric endpoint ordering was confused with string sorting, or input orientation was retained | Use `make_edge_id(a, b)` and compare integer-sorted `Edge.ids`; e.g. `15-16`, not lexical assumptions about `10` versus `2`. |
| `CompilerISA.parse_obj`, `.dict`, or `.parse_file` emits warnings | These RPCQ compatibility methods are deprecated in this version | Use direct dataclass constructors/private conversion only where the compiler compatibility boundary requires it; keep warning handling explicit. Do not replace a QCS SDK ISA with a legacy class without a conversion. |
| Compiler rejects a program using a custom processor | Program operations, compiler target ISA, and QAM do not share a gate/topology contract | Inspect `processor.to_compiler_isa()`, resource labels, dead flags, and gate names; use the same processor when constructing the compiler and a compatible QAM. Route lifecycle details to `../compile-execute/`. |
| QVM mimic has a different topology than intended | Convenience name or generated complete/square graph was used instead of the custom processor | Build the processor from the exact graph/fixture and attach it to the chosen local QVM assembly; compare `qubit_topology()` and ISA sets before compiling. |
| `PyQVM` construction fails or behaves unexpectedly with sparse labels | In-process QVM dimensions and program labels are not aligned with the processor | Use contiguous integer labels for the local mimic or explicitly adapt the QAM/program boundary; this sub-skill does not rewrite program addressing. Route addressing to `../program-authoring/`. |
| `get_qcs_quantum_processor` fails before returning an ISA | QCS credentials, configuration, processor ID, permissions, endpoint, or network are unavailable | Stop at the service boundary. Use an offline supplied fixture or custom graph for conversion checks. Never claim that a live QPU was queried. Route configuration/execution recovery to `../compile-execute/`. |
| QCS fetch times out or DNS/connection fails | Backend/network problem, not a topology conversion problem | Verify service configuration separately, retry only when permitted, and record that metadata could not be fetched. The smoke helper intentionally never attempts this path. |
| Noise model is rejected when attached | Processor IDs/gates and noise model descriptors are incompatible, or the noise data is invalid | Check model resource coverage and validation under `../noise-experiments/`; this sub-skill only confirms processor metadata compatibility. |

## Minimum diagnosis record

When reporting a processor mismatch, include:

- processor class and whether its source was a local graph, CompilerISA, or QCS
  fixture;
- sorted qubit IDs and canonical edge IDs;
- dead qubits/edges and gate names per relevant resource;
- whether isolated nodes were preserved intentionally;
- compiler/QAM class and processor ID relationship;
- whether any QCS/QVM/quilc/network action was attempted;
- exact exception class and operation/site that caused it.

Do not “fix” a malformed operation by dropping it silently. A conversion that
returns an object is not proof that every source operation was represented.
