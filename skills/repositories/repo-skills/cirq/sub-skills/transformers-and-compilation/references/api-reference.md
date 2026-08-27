# API reference: Cirq transformers, gatesets, routing, and topologies

This reference covers public APIs used to transform, compile, and route Cirq circuits. It assumes the circuit object itself already exists; use `core-circuits-and-ops` for circuit construction basics.

## Transformer API

### Transformer callable contract

A Cirq transformer is any callable compatible with the `cirq.TRANSFORMER` protocol:

```python
def transformer_like(
    circuit: cirq.AbstractCircuit,
    *,
    context: cirq.TransformerContext | None = None,
    **keyword_options,
) -> cirq.AbstractCircuit:
    ...
```

Operational expectations:

- Input circuits are not mutated in-place.
- The return value is the transformed circuit.
- Additional transformer-specific arguments are keyword-only and should have defaults when used with `@cirq.transformer`.
- Transformer functions and transformer classes are both supported.

### `cirq.transformer`

```python
cirq.transformer(cls_or_func=None, *, add_deep_support=False)
```

Use this decorator for custom transformer functions/classes. It verifies the transformer shape and adds transformer logging around the call. Set `add_deep_support=True` when the transformer should recurse into nested `cirq.CircuitOperation` bodies whenever `context.deep` is true.

### `cirq.TransformerContext`

Constructor shape:

```text
cirq.TransformerContext(logger=<no-op default>, tags_to_ignore=(), deep=False)
```

Fields:

| Field | Use |
| --- | --- |
| `logger` | A `cirq.TransformerLogger` instance records each stage's input/output circuit and transformer logs. The default logger is no-op. |
| `tags_to_ignore` | Hashable tags marking operations that should be skipped by transformers that honor the context. Use this for no-compile regions. |
| `deep` | If true, transformers that support deep mode recurse into `CircuitOperation` subcircuits unless the `CircuitOperation` has an ignored tag. |

Important nuance: routing with `RouteCQC` inserts swaps and maps qubits; ignored tags do not protect operations from topology-level routing decisions, though deep routing can unroll `CircuitOperation`s before routing.

## Built-in transformer entry points

| API | Typical use | Notes |
| --- | --- | --- |
| `cirq.drop_empty_moments(circuit, *, context=None)` | Remove moments containing no operations. | Honors `deep` and ignored tags through transformer primitives. |
| `cirq.drop_negligible_operations(circuit, *, context=None, atol=...)` | Drop operations with negligible effect. | Useful after merges/decompositions. Be careful around protected calibration pulses. |
| `cirq.merge_single_qubit_gates_to_phxz(circuit, *, context=None, merge_tags_fn=None, atol=1e-8)` | Replace runs of single-qubit unitaries with `cirq.PhasedXZGate`. | Good postprocess step for Google-style single-qubit rotations. |
| `cirq.merge_single_qubit_moments_to_phxz(circuit, *, context=None, atol=1e-8)` | Merge adjacent all-single-qubit moments into one PhasedXZ moment. | Used by target gatesets to preserve alternating 1q/2q moment structure. |
| `cirq.eject_z(circuit, *, context=None, atol=0.0, eject_parameterized=False)` | Push Z rotations later, absorb them into compatible gates/measurements when possible. | Decorated with deep support. Ignored tags cause tracked phases to be flushed before protected operations. |
| `cirq.expand_composite(circuit, *, context=None, no_decomp=lambda op: False)` | Expand composite operations using `cirq.decompose`. | `no_decomp` is a keep predicate; use it to stop at accepted primitive gates. |
| `cirq.optimize_for_target_gateset(circuit, *, context=None, gateset=None, ignore_failures=True, max_num_passes=1)` | Compile to a `CompilationTargetGateset`, or decompose generally when no gateset is supplied. | Set `ignore_failures=False` when you need a hard failure on unsupported operations. `max_num_passes=None` iterates until no moment/op count change, but the optimizer remains heuristic. |

Other useful composition helpers include `cirq.create_transformer_with_kwargs(transformer, **kwargs)`, `cirq.map_operations`, `cirq.map_operations_and_unroll`, `cirq.merge_k_qubit_unitaries`, `cirq.synchronize_terminal_measurements`, `cirq.align_left`, and `cirq.align_right`.

## Target gatesets

### `cirq.CompilationTargetGateset`

A `CompilationTargetGateset` is a `cirq.Gateset` plus a decomposition/transformer policy that `optimize_for_target_gateset` can execute:

1. Run `gateset.preprocess_transformers`.
2. Decompose operations using `cirq.decompose` and `gateset.decompose_to_target_gateset`.
3. Run `gateset.postprocess_transformers`.

`cirq.TwoQubitCompilationTargetGateset` supplies common behavior for 1q/2q target gatesets: expand composites, merge connected components, decompose to target 2q interactions, merge single-qubit moments to `PhasedXZGate`, drop negligible operations, and drop empty moments.

### `cirq.CZTargetGateset`

```python
cirq.CZTargetGateset(
    *,
    atol=1e-8,
    allow_partial_czs=False,
    additional_gates=(),
    preserve_moment_structure=True,
    reorder_operations=False,
)
```

Default accepted operation families include `cirq.CZ`/`cirq.CZPowGate` depending on `allow_partial_czs`, `cirq.PhasedXZGate`, `cirq.MeasurementGate`, and `cirq.GlobalPhaseGate`. Use `additional_gates` to preserve extra accepted gates. `reorder_operations=True` can only be used when moment structure preservation is disabled.

### `cirq.SqrtIswapTargetGateset`

Use this for circuits constrained to sqrt-iSWAP-like two-qubit interactions. It follows the same `CompilationTargetGateset` pattern and is often useful for simulator or hardware targets where iSWAP-family gates are native.

### `cirq_google.SycamoreTargetGateset`

```python
cirq_google.SycamoreTargetGateset(*, atol=1e-8, tabulation=None)
```

This optional gateset compiles to the Sycamore gate plus accepted single-qubit rotations, measurement, and global phase operations. Importing and using this gateset locally does not contact Google services. Live provider validation, credentials, jobs, and samplers are outside this sub-skill.

## Routing APIs

### `cirq.RouteCQC`

```python
router = cirq.RouteCQC(device_graph)
routed = router(
    circuit,
    *,
    lookahead_radius=8,
    tag_inserted_swaps=False,
    initial_mapper=None,
    context=None,
)
```

`device_graph` is a NetworkX graph whose nodes are physical qubits. Calling the router returns a circuit over physical qubits with inserted swaps so each two-qubit operation is adjacent on the graph. The router assumes operations have at most two qubits, except measurements; decompose larger gates first.

For mapping details:

```python
routed_circuit, initial_mapping, swap_mapping = router.route_circuit(circuit)
```

The routed circuit is equivalent to the original circuit up to the initial logical-to-physical mapping and the final swap-induced qubit permutation.

### Initial mappers

- `cirq.LineInitialMapper(device_graph)` is the default strategy. It maps disjoint logical interaction lines onto high-degree physical paths starting near the graph center.
- `cirq.HardCodedInitialMapper({...})` can pin logical qubits to chosen physical qubits when calibration, layout, or named-topology placement matters.
- Custom mappers can implement `cirq.AbstractInitialMapper.initial_mapping(circuit)`.

## Named topologies and placements

Named topologies describe reusable topology graphs independent of a provider service:

- `cirq.LineTopology(n_nodes)` for contiguous 1D chains.
- `cirq.TiltedSquareLattice(width, height)` for Google-style tilted square lattices.
- Topologies expose `.graph`, `.name`, and `.n_nodes`.
- Conversion helpers include `nodes_to_linequbits`, `nodes_as_linequbits`, `nodes_to_gridqubits`, and `nodes_as_gridqubits` depending on topology type.

Placement helpers:

```python
placements = cirq.get_placements(big_graph, small_topology.graph, max_placements=100_000)
valid = cirq.is_valid_placement(big_graph, small_topology.graph, placements[0])
```

`big_graph` is usually a device graph; `small_topology.graph` is the desired logical subtopology. Use `draw_placements` only when plotting is appropriate; it is not needed for noninteractive validation.
