# Cirq Core Circuits and Operations API Reference

This reference is for the `cirq` package namespace and the core circuit object
model. It avoids simulation, provider services, and compilation pipelines except
where those APIs expose core object protocols.

## Mental model

Cirq programs are built from nested, mostly immutable objects:

```text
Qid / Qubit  -> identifies a quantum object and its dimension
Gate         -> reusable effect independent of concrete qubits
Operation    -> gate or effect applied to specific qids
Moment       -> operations that occupy one abstract time slice
Circuit      -> ordered moments; mutable construction container
FrozenCircuit -> immutable circuit snapshot, usable in CircuitOperation
CircuitOperation -> a circuit packaged as an operation for nesting/reuse
```

An operation may appear in a `Moment` only if it does not overlap another
operation's qids in that moment.

## Qids and qubits

Use qubit classes according to the meaning of the indices:

| Class or factory | Use when | Notes |
| --- | --- | --- |
| `cirq.LineQubit(x)` | 1-D indexed qubits. | Sorts by integer coordinate. |
| `cirq.LineQubit.range(*range_args)` | Consecutive line qubits. | Accepts Python `range`-style arguments, for example `range(3)` or `range(2, 5)`. |
| `cirq.GridQubit(row, col)` | 2-D grid/device-style qubits. | Common for grid hardware layouts and diagrams. |
| `cirq.GridQubit.rect(rows, cols, top=0, left=0)` | Rectangular grid of qubits. | Returns row-major `GridQubit`s. |
| `cirq.GridQubit.square(diameter, top=0, left=0)` | Square grid. | Convenience wrapper for a square rectangle. |
| `cirq.NamedQubit(name)` | Abstract algorithm qubits before placement. | Sorts by name. |
| `cirq.NamedQubit.range(*args, prefix=...)` | Named families such as `a0`, `a1`. | Requires a keyword prefix. |
| `cirq.LineQid`, `cirq.GridQid` | Qudits or non-binary dimensions. | Dimension must match gate/operation `qid_shape`. |

Useful checks:

```python
q0, q1 = cirq.LineQubit.range(2)
grid = cirq.GridQubit.rect(2, 3, top=1, left=4)
ancilla = cirq.NamedQubit('ancilla')

assert cirq.qid_shape(cirq.X(q0)) == (2,)
```

When using qudits, prefer gates that implement `_qid_shape_` instead of only
`_num_qubits_`; otherwise Cirq treats the gate as qubit-only with shape `(2,)`
per target.

## Gates and operations

Core signatures:

```python
cirq.Gate.on(self, *qubits) -> cirq.Operation
cirq.Gate.on_each(self, *targets) -> list[cirq.Operation]
cirq.Gate.controlled(
    self,
    num_controls=None,
    control_values=None,
    control_qid_shape=None,
) -> cirq.Gate
cirq.Operation.with_qubits(self, *new_qubits) -> cirq.Operation
cirq.Operation.with_tags(self, *new_tags) -> cirq.Operation
cirq.Operation.controlled_by(self, *control_qubits, control_values=None) -> cirq.Operation
cirq.Operation.with_classical_controls(self, *conditions) -> cirq.Operation
```

Patterns:

```python
q0, q1 = cirq.LineQubit.range(2)

op_a = cirq.X.on(q0)          # Explicit Gate.on
op_b = cirq.X(q0)             # Gate call shorthand
ops = cirq.H.on_each(q0, q1)  # Same gate on many qids

controlled_gate = cirq.X.controlled()
controlled_op = cirq.X(q1).controlled_by(q0)
tagged_op = cirq.CZ(q0, q1).with_tags('keep')
classical_op = cirq.X(q1).with_classical_controls('m0')
```

Gate and operation objects should be treated as immutable. Create modified
copies with methods such as `with_qubits`, `with_tags`, and `controlled_by`.

## Circuits, moments, and insert strategies

Verified signatures:

```python
cirq.Circuit(*contents, strategy=cirq.InsertStrategy.EARLIEST, tags=())
cirq.Circuit.append(moment_or_operation_tree, strategy=cirq.InsertStrategy.EARLIEST) -> None
cirq.Circuit.insert(index, moment_or_operation_tree, strategy=cirq.InsertStrategy.EARLIEST) -> int
cirq.Circuit.findall_operations(predicate) -> Iterator[tuple[int, cirq.Operation]]
cirq.Circuit.to_text_diagram(
    *, use_unicode_characters=True, transpose=False, include_tags=True,
    precision=3, qubit_order=cirq.QubitOrder.DEFAULT
) -> str
cirq.Moment(*contents, _flatten_contents=True, tags=())
cirq.Moment.from_ops(*ops, tags=()) -> cirq.Moment
```

`Circuit` constructors, `append`, and `insert` accept OP trees: operations,
moments, iterables, and generators that can be flattened into operations and/or
moments.

```python
q = cirq.LineQubit.range(3)
circuit = cirq.Circuit()
circuit.append(cirq.H(qi) for qi in q)
circuit.append([cirq.CNOT(q[0], q[1]), cirq.CNOT(q[1], q[2])])
print(circuit.to_text_diagram())
```

Insert strategies:

| Strategy | Placement behavior | Typical use |
| --- | --- | --- |
| `InsertStrategy.EARLIEST` | Default. Slides each operation as early as possible without qid conflicts before the requested insertion point. | Compact circuits. |
| `InsertStrategy.NEW` | Puts every inserted operation into a fresh new moment. | Preserve explicit one-op-per-moment timing. |
| `InsertStrategy.INLINE` | Tries to insert into the previous moment; creates a new moment only on conflict. | Add compatible operations to a just-created layer. |
| `InsertStrategy.NEW_THEN_INLINE` | Starts a new moment for the first operation, then continues inline. | Create a new layer from an operation tree. |
| `InsertStrategy.LATEST` | Available in the API; places operations as late as possible in its insertion window. | Use only when you intentionally want late placement. |

Inspection:

```python
for moment_index, op in circuit.findall_operations(cirq.is_measurement):
    print(moment_index, op, cirq.measurement_key_names(op))

all_ops = list(circuit.all_operations())
keys = circuit.all_measurement_key_names()
```

## Measurement keys and measurement operations

Verified signature:

```python
cirq.measure(*target, key=None, invert_mask=(), confusion_map=None) -> cirq.GateOperation
```

`cirq.measure(q0, q1, key='m')` creates one `MeasurementGate` operation over all
targets. If `key` is omitted, Cirq uses a comma-separated string derived from
the target qids. Prefer explicit stable keys in generated circuits.

Useful key APIs:

```python
op = cirq.measure(q0, key='m0')
assert cirq.is_measurement(op)
assert cirq.measurement_key_names(op) == frozenset({'m0'})

circuit = cirq.Circuit(op)
assert circuit.all_measurement_key_names() == frozenset({'m0'})
```

Avoid using the same measurement key for unrelated measurement operations unless
the downstream sampler/result interpretation explicitly expects one shared key.
For nested circuits, use `CircuitOperation.with_measurement_key_mapping(...)` or
`CircuitOperation.with_key_path(...)` to make inner keys unique.

## Parameters and parameter resolution

Verified signatures:

```python
cirq.ParamResolver(param_dict=None)
cirq.resolve_parameters(val, param_resolver, recursive=True)
cirq.is_parameterized(val) -> bool
```

Example:

```python
import sympy

q = cirq.LineQubit(0)
theta = sympy.Symbol('theta')
circuit = cirq.Circuit(cirq.X(q) ** theta, cirq.measure(q, key='m'))

assert cirq.is_parameterized(circuit)
resolved = cirq.resolve_parameters(circuit, cirq.ParamResolver({'theta': 0.25}))
assert not cirq.is_parameterized(resolved)
```

Many protocols and execution paths require numeric parameters. Check for
remaining symbols before calling `unitary`, QASM export, or simulation-oriented
APIs.

## Protocols for object inspection and custom gates

Important signatures:

```python
cirq.unitary(val, default=np.array([]))
cirq.has_unitary(val, *, allow_decompose=True) -> bool
cirq.decompose(
    val, *, intercepting_decomposer=None, fallback_decomposer=None, keep=None,
    on_stuck_raise=..., preserve_structure=False, context=None
) -> list[cirq.Operation]
cirq.inverse(val, default=([],))
cirq.qid_shape(val, default=...)
cirq.circuit_diagram_info(val, args=None, default=...)
```

Use `has_unitary` before `unitary` when an object may be a measurement, channel,
classically controlled operation, or still parameterized. Use `default=None` if
you want a sentinel instead of an exception or default empty value.

Minimal custom gate pattern:

```python
import numpy as np

class MyZLike(cirq.Gate):
    def _num_qubits_(self):
        return 1

    def _unitary_(self):
        return np.diag([1, -1])

    def _circuit_diagram_info_(self, args):
        return 'Z?'

q = cirq.LineQubit(0)
print(cirq.Circuit(MyZLike().on(q)))
```

Parameterized custom gates should either resolve parameters inside `_unitary_`
before returning a numeric matrix, return `NotImplemented` while unresolved, or
implement `_decompose_` into built-in parameterized operations. For qudits,
implement `_qid_shape_` and ensure the returned unitary dimension equals the
product of the qid dimensions.

## CircuitOperation and nested circuits

Verified constructor signature:

```python
cirq.CircuitOperation(
    circuit: cirq.FrozenCircuit,
    repetitions=1,
    qubit_map=None,
    measurement_key_map=None,
    param_resolver=None,
    repetition_ids=None,
    parent_path=(),
    extern_keys=frozenset(),
    use_repetition_ids=None,
    repeat_until=None,
)
```

Common methods:

```python
sub = cirq.FrozenCircuit(cirq.H(q0), cirq.CNOT(q0, q1))
block = cirq.CircuitOperation(sub)
block2 = block.repeat(2)
block3 = block.with_qubit_mapping({q0: q1, q1: q0})
expanded_once = block2.mapped_circuit(deep=False)
expanded_deep = block2.mapped_circuit(deep=True)
```

Freeze a subcircuit before wrapping it. If the frozen subcircuit contains
measurements, remap keys or add a key path before reusing it multiple times.

## JSON, QASM, and Quirk basics

Verified signatures:

```python
cirq.to_json(obj, file_or_fn=None, *, indent=2, separators=None, cls=cirq.CirqEncoder)
cirq.read_json(file_or_fn=None, *, json_text=None, resolvers=None)
cirq.qasm(val, *, args=None, qubits=None, default=([],))
```

JSON is the preferred self-contained object roundtrip for Cirq-native circuits,
gates, moments, operations, and many built-in values:

```python
text = cirq.to_json(circuit)
restored = cirq.read_json(json_text=text)
assert restored == circuit
```

For custom classes, implement `_json_dict_` and `_from_json_dict_`, and pass a
resolver that maps the serialized `cirq_type` string to the class. Prepend the
custom resolver before the default resolvers.

QASM export is protocol-based:

```python
qasm_2 = cirq.qasm(circuit)  # default version is currently OpenQASM 2.0
qasm_3 = circuit.to_qasm(version='3.0')
```

QASM import lives in the optional contrib importer and supports only a subset of
OpenQASM. Quirk conversion uses `cirq.quirk_url_to_circuit(...)` or
`cirq.quirk_json_to_circuit(...)`; not every Quirk gate has a Cirq conversion.
