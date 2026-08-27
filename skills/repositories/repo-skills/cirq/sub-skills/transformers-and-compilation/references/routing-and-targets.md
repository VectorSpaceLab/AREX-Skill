# Routing and target workflows

Use this reference when a circuit must satisfy topology constraints, provider-style gatesets, or named-topology placements before a downstream run.

## Decide the compile target

| Target need | Recommended path | Boundary |
| --- | --- | --- |
| Only gate-family constraints such as CZ plus single-qubit rotations | `cirq.optimize_for_target_gateset(..., gateset=cirq.CZTargetGateset())` | No routing needed unless adjacency matters. |
| Sqrt-iSWAP or other two-qubit interaction family | Use the matching `CompilationTargetGateset` and verify operation membership afterward. | Choose target based on the downstream simulator/device constraints. |
| Google Sycamore-style local compile | `import cirq_google as cg`; use `cg.SycamoreTargetGateset()` and, when needed, a device graph from offline device metadata. | This is a local package workflow only. No Engine, sampler, project, or credentials. |
| Physical adjacency constraints | Route with `cirq.RouteCQC(device_graph)` before final gateset optimization. | Routing inserts SWAPs and changes the logical-to-physical qubit mapping. |
| Cloud submission or provider serializer payloads | First compile/rout locally here, then route to `hardware-providers-and-serialization`. | Provider services are outside this sub-skill. |

## Route with `RouteCQC`

Minimal topology routing pattern:

```python
import networkx as nx
import cirq

logical = cirq.LineQubit.range(4)
circuit = cirq.Circuit(
    cirq.CNOT(logical[0], logical[3]),
    cirq.CNOT(logical[1], logical[2]),
)

physical = cirq.LineQubit.range(4)
device_graph = nx.path_graph(physical)
router = cirq.RouteCQC(device_graph)

routed_circuit, initial_mapping, swap_mapping = router.route_circuit(
    circuit,
    tag_inserted_swaps=True,
)
```

What the outputs mean:

- `routed_circuit`: a circuit over physical qubits with inserted swaps so every two-qubit operation is adjacent on `device_graph`.
- `initial_mapping`: logical qubit to physical qubit placement chosen before routing.
- `swap_mapping`: final physical permutation induced by inserted swaps.

Equivalence is not a simple same-qubit unitary comparison after routing. Account for both the initial placement and the final swap permutation.

## Route then compile to a provider-style target

For a Google-style offline workflow:

```python
import cirq
import cirq_google as cg

router = cirq.RouteCQC(cg.Sycamore.metadata.nx_graph)
routed = router(circuit)
compiled = cirq.optimize_for_target_gateset(
    routed,
    gateset=cg.SycamoreTargetGateset(),
    ignore_failures=False,
)

# Offline structural check only; live submission belongs elsewhere.
cg.Sycamore.validate_circuit(compiled)
```

Order matters:

1. Decompose non-1q/2q operations before routing if `RouteCQC` cannot handle them.
2. Route to the device graph so adjacency constraints are satisfied.
3. Compile inserted swaps and original gates to the target gateset.
4. Validate operation families and adjacency against local device metadata when available.
5. Hand off to provider submission only after local constraints pass.

## Initial mapping choices

`RouteCQC` uses `LineInitialMapper` by default when no mapper is supplied. It builds a logical interaction graph from the circuit, starts near the center of the physical graph, and greedily places line-like components on high-degree physical neighbors.

Use a hard-coded mapper when layout is part of the requirement:

```python
initial_mapper = cirq.HardCodedInitialMapper(
    {
        logical[0]: physical[0],
        logical[1]: physical[1],
        logical[2]: physical[2],
        logical[3]: physical[3],
    }
)
routed = router(circuit, initial_mapper=initial_mapper)
```

Use a custom `AbstractInitialMapper` implementation when calibration, reserved qubits, or application topology must control placement beyond a fixed dictionary.

## Named topologies and placements

Named topologies describe logical subgraphs that can be placed onto a larger device graph:

```python
topology = cirq.LineTopology(5)
logical_graph = topology.graph
logical_qubits = topology.nodes_as_linequbits()
```

For grid-like Google-style layouts:

```python
topology = cirq.TiltedSquareLattice(width=4, height=2)
qubit_mapping = topology.nodes_to_gridqubits(offset=(3, 2))
```

To find placements of a small topology in a larger graph:

```python
placements = cirq.get_placements(device_graph, topology.graph, max_placements=10_000)
if not placements:
    raise ValueError("No valid placement for requested topology")
placement = placements[0]
assert cirq.is_valid_placement(device_graph, topology.graph, placement)
```

Then convert the placement into a hard-coded mapper for routing if the circuit's logical qubits correspond to topology nodes.

## Device graphs

Acceptable `device_graph` inputs are NetworkX graphs with physical qubit nodes, usually `LineQubit`, `GridQubit`, or provider device qubits. Checklist:

- The graph should contain every physical qubit that an initial mapper may choose.
- The graph should be connected for automatic line mapping; disconnected components need an explicit mapping strategy and may still fail if interactions cross components.
- Directed graphs are routed as undirected for swap planning; inserted SWAPs can be directionally decomposed for unidirectional CNOT constraints.
- Do not confuse a named topology's node labels with provider qubits. Convert or map them deliberately.

## Moment structure and target gatesets

`CompilationTargetGateset` implementations can preserve or alter moment structure:

- `CZTargetGateset(..., preserve_moment_structure=True)` keeps the original moment layering as much as the decomposition allows.
- `preserve_moment_structure=False` allows postprocess passes such as stratification and operation reordering when enabled.
- `reorder_operations=True` is only valid when moment preservation is disabled.
- Provider devices may treat moments as scheduling boundaries; preserve structure when timings or parallelism matter.

## Quick validation snippets

Check whether compiled operations are accepted by a target gateset:

```python
bad_ops = [op for op in compiled.all_operations() if op not in gateset]
if bad_ops:
    raise ValueError(f"Unsupported operations remain: {bad_ops}")
```

Check adjacency after routing:

```python
bad_pairs = []
for op in routed_circuit.all_operations():
    if len(op.qubits) != 2:
        continue
    q0, q1 = op.qubits
    adjacent = device_graph.has_edge(q0, q1) or device_graph.has_edge(q1, q0)
    if not adjacent:
        bad_pairs.append(op)
if bad_pairs:
    raise ValueError(f"Non-adjacent operations remain: {bad_pairs}")
```

If a provider device exposes an offline validator, use it only after routing and target-gateset compilation. If validation asks for credentials or live service access, route to provider guidance instead.
