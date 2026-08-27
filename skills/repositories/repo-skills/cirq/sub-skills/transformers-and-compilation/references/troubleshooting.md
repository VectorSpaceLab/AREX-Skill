# Troubleshooting transformers, target compilation, and routing

## Target gateset conversion leaves unsupported operations

Symptoms:

- The output of `optimize_for_target_gateset` still contains original gates.
- Provider or local device validation rejects an operation after compilation.
- Later code fails because it assumed only CZ/SYC/sqrt-iSWAP-family gates remain.

Likely causes and fixes:

| Cause | Fix |
| --- | --- |
| `ignore_failures=True` left failed conversions unchanged. | Re-run with `ignore_failures=False` to get the first unsupported operation as an error. |
| The gate has no unitary or no decomposition known to the selected gateset. | Provide a custom decomposition, decompose earlier with `expand_composite`, or choose a target gateset that accepts the operation. |
| A protected tag prevented conversion. | Remove the ignored tag from operations that must be compiled, or compile protected regions separately with explicit intent. |
| `additional_gates` was used too broadly. | Only mark operations as additional gates if the downstream target truly accepts them. |
| Multi-qubit composite operations remained nested. | Use `expand_composite` or deep mode where appropriate before final target compilation. |

Debug pattern:

```python
compiled = cirq.optimize_for_target_gateset(
    circuit,
    gateset=gateset,
    ignore_failures=False,
)
bad = [op for op in compiled.all_operations() if op not in gateset]
assert not bad, bad
```

## Tags to ignore are not honored

Symptoms:

- A tagged operation is rewritten, moved, merged, or removed.
- A protected subcircuit is still transformed.

Checklist:

1. Confirm the tag values match exactly. `"no_compile"`, `("no_compile",)`, and a custom tag object are different values unless equal/hash-compatible.
2. Pass the same `TransformerContext(tags_to_ignore=(...))` into every pass in the pipeline.
3. For custom transformers, pass `tags_to_ignore` to Cirq transformer primitives or explicitly skip tagged operations.
4. For deep transforms, remember that a tagged `CircuitOperation` with an ignored tag prevents recursion into its body.
5. Routing is topology-level; ignored tags do not stop necessary swaps from being inserted around a non-adjacent operation.

If a built-in pass appears to cross a protected operation, inspect whether it flushed accumulated state before the operation. For example, phase-ejection passes may emit a Z before a protected op instead of commuting through it.

## Deep subcircuit behavior is surprising

Symptoms:

- Operations inside a `CircuitOperation` do not change.
- A nested body is transformed when it should be preserved.
- Routing raises an arity error for a `CircuitOperation`.

Fixes:

- Use `context = cirq.TransformerContext(deep=True)` only when nested bodies should be transformed.
- Use transformers with deep support or transformer primitives with `deep=context.deep`.
- Tag a `CircuitOperation` and include that tag in `tags_to_ignore` to preserve the entire nested body.
- Before routing, either unroll nested operations explicitly or pass a deep context to routing when nested multi-qubit operations need to be exposed.

## Routing fails or inserts unexpected swaps

Symptoms:

- `RouteCQC` raises about operations on three or more qubits.
- Routing raises due to an impossible mapping or unavailable physical qubits.
- The routed circuit is much deeper than expected.
- A non-adjacent two-qubit operation remains after routing.

Likely causes and fixes:

| Cause | Fix |
| --- | --- |
| Circuit contains non-measurement operations on more than two qubits. | Decompose with `expand_composite` or target-specific preprocessors before routing. |
| Device graph is disconnected or too small. | Use a connected graph with enough physical qubits, or provide a hard-coded mapper within one connected component. |
| Logical mapping does not match named-topology nodes. | Convert topology nodes to actual Cirq qubits and build an explicit mapper. |
| Circuit interactions cross disconnected physical components. | Narrow the logical circuit or choose a larger connected placement. |
| Routing output is compared to the original on the same qubits. | Account for `initial_mapping` and `swap_mapping`; routed equivalence is up to final permutation. |
| Lookahead heuristic chose many swaps. | Try a better initial mapper, a named-topology placement, or a different `lookahead_radius`; heuristic routing is not globally optimal. |

For directed graphs, check adjacency in either direction when validating topology, then decompose gates to the direction-aware target if needed.

## Named topology placement explodes or returns no placements

Symptoms:

- `get_placements` raises because there are too many possible placements.
- No placements are found for a requested topology.
- A placement validates but the resulting qubits do not match the user's intended orientation.

Fixes:

- Reduce `max_placements` only as a safety cap; it does not make an impossible placement possible.
- Use a smaller `LineTopology` or `TiltedSquareLattice` when the device graph cannot contain the requested subgraph.
- Pre-filter the device graph to allowed/reserved/calibrated qubits before calling `get_placements`.
- Validate with `is_valid_placement` before turning a placement into a hard-coded mapper.
- Remember that placements may be deduplicated by physical qubit set, so orientation-specific assignments may need manual mapping.

## Moment structure changed unexpectedly

Symptoms:

- Parallel gates become serial or serial gates become parallel.
- Empty moments disappear.
- Provider timing/scheduling expectations no longer match the original circuit.

Likely causes and fixes:

| Cause | Fix |
| --- | --- |
| `drop_empty_moments` removed intentional placeholders. | Do not run it when empty moments encode scheduling intent, or preserve timing elsewhere. |
| Target gateset postprocessors merged/stratified moments. | Use `preserve_moment_structure=True` when available. |
| `reorder_operations=True` was enabled. | Disable reordering unless depth reduction is more important than moment layout. |
| Virtual Z gates disappear on some hardware-style targets. | Treat Z phase handling as logical compilation, not as a physical pulse unless provider guidance says otherwise. |

## Sycamore target import or validation fails

Symptoms:

- `import cirq_google` fails.
- `cirq_google.SycamoreTargetGateset` is unavailable.
- Local device validation rejects measurements or unsupported gates.

Fixes:

- If `cirq_google` is not installed, use `CZTargetGateset` or another core target for local compilation, or install the provider package in the environment used for this task.
- Use `cirq_google.SycamoreTargetGateset` only for local gateset compilation; do not create Engines or samplers in this sub-skill.
- Check that measurements are terminal if using a Google device validator.
- Route to the provider/serialization sub-skill when the task requires cloud credentials, processor discovery, serializer payloads, or job submission.

## Safe debugging order

1. Print operation histogram before and after each pass.
2. Run with `ignore_failures=False` for target compilation.
3. Use `TransformerLogger` to see stage-level input/output circuits.
4. Check ignored tags and deep settings once at context creation.
5. Validate gateset membership after compilation.
6. Validate adjacency after routing.
7. Only then route to provider submission or simulation.
