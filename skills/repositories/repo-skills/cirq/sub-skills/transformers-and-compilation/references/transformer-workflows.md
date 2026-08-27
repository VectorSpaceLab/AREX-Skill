# Transformer workflows

Use these patterns to choose pass ordering, preserve protected regions, debug transformer behavior, and compile circuits to target gate constraints.

## Workflow 1: build a deliberate transformer pipeline

A safe local pipeline is usually:

1. **Decide constraints.** Identify whether the target is only a gateset, a topology plus gateset, or a provider device. Topology constraints require routing before final target-gateset validation.
2. **Mark protected operations.** Add tags such as `"no_compile"` or a calibration-specific tag to operations that must not be rewritten by ordinary transforms.
3. **Create one context.** Share a `cirq.TransformerContext` across related passes so ignored tags, deep behavior, and logging are consistent.
4. **Normalize composites.** Use `expand_composite` or the gateset preprocessors to expose operations that need conversion.
5. **Optimize/decompose.** Use targeted transforms (`eject_z`, single-qubit merges, `optimize_for_target_gateset`) in an order that matches the target.
6. **Clean up.** Drop empty/negligible operations and preserve or intentionally relax moment structure.
7. **Validate.** Check that the final operations are accepted by the gateset/device and, where possible, compare unitary or terminal-measurement behavior.

Example skeleton:

```python
context = cirq.TransformerContext(tags_to_ignore=("no_compile",), deep=True)

working = cirq.expand_composite(circuit, context=context)
working = cirq.eject_z(working, context=context)
working = cirq.merge_single_qubit_gates_to_phxz(working, context=context)
compiled = cirq.optimize_for_target_gateset(
    working,
    context=context,
    gateset=cirq.CZTargetGateset(),
    ignore_failures=False,
)
compiled = cirq.drop_empty_moments(compiled, context=context)
```

## Workflow 2: compile to a target gateset

Use `optimize_for_target_gateset` when the accepted operations matter more than individual low-level passes.

```python
gateset = cirq.CZTargetGateset(
    allow_partial_czs=False,
    preserve_moment_structure=True,
)
compiled = cirq.optimize_for_target_gateset(
    circuit,
    gateset=gateset,
    ignore_failures=False,
    max_num_passes=1,
)
```

Guidance:

- Start with `ignore_failures=False` while developing. The default `True` leaves unsupported operations in place and can hide a failed compile.
- Keep `max_num_passes=1` unless repeated passes are needed. `max_num_passes=None` can reduce some circuits further but remains heuristic.
- Use `additional_gates` in `CZTargetGateset` only for operations the downstream target truly accepts.
- If the target has topology constraints, route first and then optimize routed gates to the provider/target gateset.

## Workflow 3: inspect transformer actions with logging

Use one `TransformerLogger` inside the shared context:

```python
context = cirq.TransformerContext(logger=cirq.TransformerLogger())
compiled = cirq.optimize_for_target_gateset(
    circuit,
    context=context,
    gateset=cirq.CZTargetGateset(),
)
context.logger.show()
```

Logging records each transformer's initial and final circuit. This is most useful when a target gateset's preprocessors/postprocessors change more than expected.

## Workflow 4: create a custom transformer

For a function transformer:

```python
@cirq.transformer(add_deep_support=True)
def remove_custom_identities(
    circuit: cirq.AbstractCircuit,
    *,
    context: cirq.TransformerContext | None = None,
    atol: float = 1e-8,
) -> cirq.Circuit:
    def rewrite(op: cirq.Operation, _moment_index: int):
        if op.gate == cirq.I:
            return []
        return op

    return cirq.map_operations_and_unroll(
        circuit,
        rewrite,
        tags_to_ignore=context.tags_to_ignore if context else (),
        deep=context.deep if context else False,
    ).unfreeze(copy=False)
```

For a class transformer, decorate the class and implement `__call__(self, circuit, *, context=None, ...)`. Add default keyword arguments for extra options.

Custom transformer checklist:

- Preserve ignored tags by passing `tags_to_ignore` to transformer primitives or checking tags explicitly.
- Decide whether deep subcircuits should be handled by the decorator (`add_deep_support=True`) or by the transformer primitive (`deep=context.deep`). Do not accidentally recurse twice.
- Return a new circuit or frozen/unfrozen copy; do not mutate the caller's circuit in-place.
- Add a logger message through `context.logger.log(...)` only when `context` is not `None`.

## Workflow 5: protect no-compile operations with tags

Any hashable operation tag can be a no-compile tag when it appears in `TransformerContext.tags_to_ignore`:

```python
protected = cirq.X(q0).with_tags("no_compile")
context = cirq.TransformerContext(tags_to_ignore=("no_compile",))
result = cirq.eject_z(cirq.Circuit(cirq.Z(q0), protected), context=context)
```

Rules of thumb:

- Built-in transformers that use Cirq transformer primitives generally honor ignored tags.
- Some transforms still need to flush accumulated state before a protected operation. For example, `eject_z` cannot commute tracked Z phase through a no-compile operation, so it emits any required phase before the tag.
- Routing changes global placement/topology. `tags_to_ignore` does not make a non-adjacent two-qubit operation executable without swaps.
- A tagged `CircuitOperation` is skipped by deep transformers, even when `context.deep=True`.

## Workflow 6: transform nested `CircuitOperation`s

Default behavior treats a `CircuitOperation` as a top-level operation. To transform its body, use a context with `deep=True` and a transformer that supports deep mode.

```python
sub = cirq.FrozenCircuit(cirq.I(q0), cirq.CNOT(q0, q1))
wrapped = cirq.CircuitOperation(sub)
circuit = cirq.Circuit(wrapped)

context = cirq.TransformerContext(deep=True)
cleaned = cirq.drop_negligible_operations(circuit, context=context)
```

Deep-mode expectations:

- Untagged nested subcircuits can be transformed.
- Tagged `CircuitOperation`s with an ignored tag are not entered.
- Transformers without decorator or primitive deep support may still leave nested bodies unchanged.
- `RouteCQC.route_circuit` can unroll nested circuit operations when `context.deep=True`; otherwise multi-qubit `CircuitOperation`s may fail the routing arity check.

## Workflow 7: validate a compile without provider services

Credential-free checks:

- Use `op in gateset` or `gateset.validate(op)` style checks for operations after compilation.
- Use unitary equivalence for small measurement-free circuits.
- Use terminal-measurement equivalence assertions for circuits ending in measurement.
- If optional `cirq_google` is available, instantiate `SycamoreTargetGateset` and local device metadata without creating an Engine, sampler, or job.

Stop and route to provider guidance when the user asks for cloud processor selection, credentials, serializer payload submission, sampler runs, reservations, calibration lookup, or job management.
