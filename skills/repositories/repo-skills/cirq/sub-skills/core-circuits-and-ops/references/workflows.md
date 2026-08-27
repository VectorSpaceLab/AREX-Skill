# Core Circuit Workflows

Use these workflows for construction and debugging tasks that stop at the Cirq
object model. If the task asks to run the circuit or interpret samples, route to
the simulation sub-skill after the circuit object is well formed.

## 1. Choose qubit identifiers before building operations

1. Use `NamedQubit` for abstract circuits that are not placed on hardware.
2. Use `LineQubit` for simple examples, 1-D layouts, and compact demos.
3. Use `GridQubit` for 2-D layouts or when later hardware/device placement is
   likely.
4. Use `LineQid` or `GridQid` only when the gate actually supports non-binary
   dimensions through `qid_shape`.

```python
abstract = cirq.NamedQubit('data')
q0, q1 = cirq.LineQubit.range(2)
grid = cirq.GridQubit.rect(2, 2)
```

Check early:

```python
assert all(q.dimension == 2 for q in [q0, q1])
```

## 2. Build a parameterized circuit with explicit keys

```python
import cirq
import sympy

q0, q1 = cirq.LineQubit.range(2)
theta = sympy.Symbol('theta')

circuit = cirq.Circuit(
    cirq.H(q0),
    cirq.CNOT(q0, q1),
    cirq.Z(q1) ** theta,
    cirq.measure(q0, key='m0'),
    cirq.measure(q1, key='m1'),
)

print(circuit.to_text_diagram())
print(circuit.all_measurement_key_names())
```

Guidelines:

- Prefer explicit measurement keys (`m0`, `m1`, `readout`, `ancilla_check`) over
  default keys derived from qubit names.
- Keep parameter names stable and human-readable.
- Keep measurements terminal unless a classically controlled operation or a
  deliberate mid-circuit measurement workflow requires otherwise.

## 3. Append and insert without timing surprises

When operation timing matters, make the strategy explicit.

```python
q = cirq.LineQubit.range(3)
circuit = cirq.Circuit()

# Compact placement: compatible operations may share a moment.
circuit.append([cirq.H(q[0]), cirq.H(q[1])], strategy=cirq.InsertStrategy.EARLIEST)

# Force a fresh layer for a barrier-like construction point.
circuit.append(cirq.CNOT(q[0], q[1]), strategy=cirq.InsertStrategy.NEW)

# Start a new measurement layer and then inline compatible measurements.
circuit.append(
    [cirq.measure(q[i], key=f'm{i}') for i in range(3)],
    strategy=cirq.InsertStrategy.NEW_THEN_INLINE,
)
```

If a list of operations lands in more or fewer moments than expected, print the
circuit after each append and switch to `Moment.from_ops(...)` or
`InsertStrategy.NEW` for explicit timing.

## 4. Search and rewrite operation objects

Use `findall_operations` for targeted inspection:

```python
measurements = list(circuit.findall_operations(cirq.is_measurement))
for moment_index, op in measurements:
    print(moment_index, op, cirq.measurement_key_names(op))
```

For small rewrites, rebuild an OP tree or use Cirq mapping helpers rather than
mutating operation internals:

```python
def retag_measurements(op):
    if cirq.is_measurement(op):
        return op.with_tags('readout')
    return op

retagged = circuit.map_operations(retag_measurements)
```

## 5. Resolve parameters before numeric protocols or execution

```python
resolver = cirq.ParamResolver({'theta': 0.25})
resolved = cirq.resolve_parameters(circuit, resolver)

if cirq.is_parameterized(resolved):
    raise ValueError('still has unresolved symbols')
```

Use this before:

- `cirq.unitary(...)` on parameterized gates or circuits.
- QASM export when the target format cannot express the remaining symbols.
- Simulation and sampling workflows.

## 6. Diagnose unitary and decomposition support

Separate the question "is this object unitary?" from "can Cirq break this down?"

```python
unitary_part = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1))
assert cirq.has_unitary(unitary_part)
matrix = cirq.unitary(unitary_part)

for op in circuit.all_operations():
    if not cirq.has_unitary(op):
        print('not unitary:', op)
```

For custom or composite gates:

```python
class MySwap(cirq.Gate):
    def _num_qubits_(self):
        return 2

    def _decompose_(self, qubits):
        a, b = qubits
        yield cirq.CNOT(a, b)
        yield cirq.CNOT(b, a)
        yield cirq.CNOT(a, b)

    def _circuit_diagram_info_(self, args):
        return ('MySwap', 'MySwap')
```

If `cirq.decompose(...)` gets stuck, either implement `_decompose_`, add a
fallback decomposer, or route to the transformer/compilation sub-skill for a
full decomposition pipeline.

## 7. Use CircuitOperation for reusable subcircuits

```python
q0, q1 = cirq.LineQubit.range(2)
body = cirq.FrozenCircuit(cirq.H(q0), cirq.CNOT(q0, q1))
block = cirq.CircuitOperation(body)

outer = cirq.Circuit(
    block.repeat(2),
    block.with_qubit_mapping({q0: q1, q1: q0}),
)
```

When the body has measurements:

```python
measured_body = cirq.FrozenCircuit(cirq.measure(q0, key='inner'))
safe_block = cirq.CircuitOperation(measured_body).with_measurement_key_mapping(
    {'inner': 'inner_first'}
)
```

Use `mapped_circuit(deep=True)` to inspect what a nested operation represents.

## 8. Serialize safely

JSON roundtrip for Cirq-native objects:

```python
json_text = cirq.to_json(circuit)
restored = cirq.read_json(json_text=json_text)
assert restored == circuit
```

Custom object roundtrip checklist:

1. Implement `_json_dict_` without adding a manual `cirq_type` key.
2. Implement `_from_json_dict_(cls, **kwargs)` as a class method if constructor
   arguments do not match the JSON dictionary directly.
3. Provide a resolver such as `lambda cirq_type: MyGate if cirq_type == 'MyGate' else None`.
4. Call `cirq.read_json(json_text=text, resolvers=[resolver, *cirq.DEFAULT_RESOLVERS])`.

QASM export:

```python
print(circuit.to_qasm(version='3.0'))
```

If QASM export returns the default sentinel or fails, the circuit likely contains
unsupported operations, custom gates without `_qasm_`, nonterminal measurements,
or symbolic values the target QASM version cannot express. Use JSON for full
Cirq fidelity.

## 9. Use the bundled inspection helper

The helper constructs a parameterized circuit and checks key hygiene:

```text
python scripts/inspect_circuit.py --help
python scripts/inspect_circuit.py --qubits 3 --json
```

Run it from this sub-skill directory or pass the script path from a copied skill
installation. It imports only `cirq` and `sympy`, performs no network calls, and
does not access an original source checkout.
