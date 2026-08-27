# Core Circuits and Operations Troubleshooting

## Unresolved symbols or parameterized objects

Symptoms:

- `cirq.is_parameterized(circuit)` is still true after a resolver is applied.
- `cirq.unitary(...)`, QASM export, or a downstream simulator refuses symbolic
  values.
- A custom gate's `_unitary_` returns arrays containing SymPy expressions.

Fixes:

```python
print(cirq.parameter_names(circuit))
resolved = cirq.resolve_parameters(circuit, cirq.ParamResolver({'theta': 0.25}))
assert not cirq.is_parameterized(resolved)
```

Use parameter names consistently. If a custom gate stores symbols, implement
`_resolve_parameters_(self, resolver, recursive)` or decompose into built-in
parameterized operations so Cirq can resolve it.

## Measurement-key collisions

Symptoms:

- `circuit.all_measurement_key_names()` has fewer names than expected.
- Result interpretation combines unrelated measurements under one key.
- Reused `CircuitOperation`s contain inner measurements with the same key.

Fixes:

```python
from collections import Counter

counter = Counter()
for _, op in circuit.findall_operations(cirq.is_measurement):
    counter.update(cirq.measurement_key_names(op))
print([key for key, count in counter.items() if count > 1])
```

Give unrelated measurements unique keys. For nested circuits, use
`with_measurement_key_mapping({'old': 'new'})` or `with_key_path(('scope',))` on
`CircuitOperation`. A single multi-qubit measurement intentionally has one key;
that is not a collision by itself.

## Non-unitary operations or channels passed to `unitary`

Symptoms:

- `cirq.has_unitary(op)` is false.
- `cirq.unitary(circuit)` fails or returns the default sentinel.
- The circuit includes measurement, reset, noisy channels, mixtures,
  classically controlled operations, or parameterized gates.

Fixes:

```python
for op in circuit.all_operations():
    if not cirq.has_unitary(op):
        print('not unitary:', op)
```

Remove measurements/channels for pure unitary inspection, resolve parameters,
or inspect the appropriate protocol instead: `cirq.kraus`, `cirq.mixture`,
`cirq.decompose`, or `cirq.circuit_diagram_info`. Route noisy simulation and
channel behavior to the simulation/noise sub-skill.

## Qid shape or qudit mismatch

Symptoms:

- Applying a gate to `LineQid`/`GridQid` raises a dimension or shape error.
- A custom qudit gate works in diagrams but fails in protocol checks.
- The unitary matrix shape does not match the qid dimensions.

Fixes:

```python
print(cirq.qid_shape(gate))
print(tuple(q.dimension for q in operation.qubits))
```

For qubit-only gates, use `LineQubit`/`GridQubit` or dimension-2 qids. For qudit
gates, implement `_qid_shape_` and return matrices sized by
`prod(qid_shape) x prod(qid_shape)`. Do not implement only `_num_qubits_` for a
non-binary-dimensional gate.

## Unsupported JSON custom object resolver

Symptoms:

- `cirq.read_json(...)` raises `Could not resolve type ... during deserialization`.
- `cirq.to_json(...)` complains about `cirq_type` in a user `_json_dict_`.
- A custom object serializes but reads back as an unexpected type.

Fixes:

- Implement `_json_dict_` with ordinary JSON-compatible fields; do not include a
  manual `cirq_type` key.
- Implement `_from_json_dict_` when constructor arguments need conversion.
- Pass a resolver before the defaults:

```python
def resolver(cirq_type):
    if cirq_type == 'MyGate':
        return MyGate
    return None

obj = cirq.read_json(json_text=text, resolvers=[resolver, *cirq.DEFAULT_RESOLVERS])
```

For portable skill examples, prefer built-in Cirq classes unless custom resolver
logic is the point of the task.

## QASM limitations

Symptoms:

- `cirq.qasm(circuit)` returns the default sentinel or raises for an operation.
- QASM import rejects syntax, opaque gates, barriers, arbitrary classical logic,
  or a nonstandard include.
- QASM output loses Cirq-specific structure such as tags or custom objects.

Fixes:

- Use `circuit.to_qasm(version='2.0')` or `version='3.0'` intentionally.
- Keep exported circuits to QASM-supported gates and terminal measurements.
- Implement `_qasm_` on custom gates only when the target QASM dialect can
  represent them.
- Use JSON, not QASM, when exact Cirq object fidelity is required.
- Treat QASM import as optional and subset-limited; the importer may require an
  optional parsing dependency.

## Append/insert strategy confusion

Symptoms:

- Operations appear earlier than the append location.
- A list of operations occupies several moments instead of one.
- A layer that should be separate is merged with previous compatible operations.

Fixes:

- Remember the default `InsertStrategy.EARLIEST` compacts operations.
- Use `InsertStrategy.NEW` for a fresh moment per operation.
- Use `Moment.from_ops(...)` to force compatible operations into one moment.
- Use `InsertStrategy.NEW_THEN_INLINE` for a fresh layer from an operation tree.
- Print `circuit.to_text_diagram()` after each construction phase while
  debugging.

## Custom parameterized gate protocol failure

Symptoms:

- A custom gate with a SymPy parameter prints correctly but fails `unitary`.
- `resolve_parameters` changes built-in gates but not the custom gate.
- `decompose` cannot lower the custom gate into known operations.

Fixes:

1. Implement `_num_qubits_` or `_qid_shape_`.
2. Implement `_resolve_parameters_` if the object stores parameters directly.
3. In `_unitary_`, return a numeric `numpy.ndarray` only after parameters are
   numeric; otherwise return `NotImplemented`.
4. Implement `_decompose_(self, qubits)` into built-in parameterized operations
   when symbolic support is needed.
5. Add `_circuit_diagram_info_` for readable diagrams and debugging.

## Diagram ordering or readability surprises

Symptoms:

- Qubits appear in an unexpected order.
- Tags appear or disappear in text diagrams.
- Floating exponents are rounded unexpectedly.

Fixes:

```python
print(circuit.to_text_diagram(qubit_order=[q0, q1], include_tags=True, precision=4))
print(circuit.to_text_diagram(use_unicode_characters=False))
```

Pass an explicit `qubit_order`, set `include_tags`, and adjust `precision` for
stable diagnostics in generated reports.
