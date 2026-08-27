# Serialization: Cirq JSON, provider payloads, and resolvers

Cirq has a general JSON protocol for Cirq objects and several provider-specific serializers for service payloads. Do not treat these formats as interchangeable.

## General Cirq JSON

```python
cirq.to_json(obj, file_or_fn=None, *, indent=2, separators=None, cls=cirq.CirqEncoder)
cirq.read_json(file_or_fn=None, *, json_text=None, resolvers=None)
```

Use cases:

- Persisting circuits, gates, moments, operations, devices, parameter sweeps, and many Cirq value objects.
- Exchanging circuits between local tools.
- Testing that custom gates/devices can be reconstructed.

Minimal round-trip:

```python
import cirq

q = cirq.LineQubit(0)
circuit = cirq.Circuit(cirq.X(q) ** 0.5, cirq.measure(q, key='m'))
json_text = cirq.to_json(circuit)
loaded = cirq.read_json(json_text=json_text)
assert loaded == circuit
```

File usage:

```python
cirq.to_json(circuit, 'circuit.json')
loaded = cirq.read_json('circuit.json')
```

Guardrails:

- Store circuits and provider-safe value objects, not API tokens, credential paths, service clients, or live job handles.
- Import provider packages before reading provider objects so their JSON resolvers are registered.
- If `read_json` fails with an unresolved `cirq_type`, add the right provider import or custom resolver.
- Round-trip equality can fail when an object intentionally omits runtime-only state; do not serialize samplers or service clients as durable objects.

## Provider resolver registration

Cirq provider packages register their public JSON resolvers when imported:

```python
import cirq
import cirq_google
import cirq_ionq
import cirq_pasqal

obj = cirq.read_json(json_text=json_text)
```

Notes:

- `cirq_google`, `cirq_ionq`, and `cirq_pasqal` register resolver dictionaries on import.
- AQT samplers and local simulator clients are intentionally not JSON-serializable runtime objects; serialize circuits or local results instead.
- Provider package versions should match between the writer and reader when exchanging provider-specific gates/devices.

## Custom JSON-compatible objects

A custom class should implement `_json_dict_` and optionally `_from_json_dict_`. Non-Cirq classes should provide a JSON namespace and a resolver.

```python
class MyTaggedGate(cirq.SingleQubitGate):
    def __init__(self, label: str):
        self.label = label

    @classmethod
    def _json_namespace_(cls):
        return 'my_package'

    def _json_dict_(self):
        # Do not include 'cirq_type'; Cirq adds it automatically.
        return {'label': self.label}

    @classmethod
    def _from_json_dict_(cls, label, **kwargs):
        return cls(label)


def my_resolver(cirq_type: str):
    if cirq_type == 'my_package.MyTaggedGate':
        return MyTaggedGate
    return None

resolvers = [my_resolver, *cirq.DEFAULT_RESOLVERS]
loaded = cirq.read_json(json_text=json_text, resolvers=resolvers)
```

Resolver troubleshooting:

- If `read_json` says it could not resolve a type, check the exact `cirq_type` string in the JSON and map it in a resolver.
- If `_json_dict_` contains `cirq_type`, remove it; Cirq generates that field from the class and namespace.
- If a non-Cirq class lacks `_json_namespace_`, serialization can fail because Cirq cannot build a stable type name.
- If an object uses shared references, consider Cirq's serializable-by-key pattern rather than duplicating state manually.

## Google program serialization

Google API serialization is separate from general Cirq JSON.

```python
import cirq_google

proto = cirq_google.CIRCUIT_SERIALIZER.serialize(circuit)
# or
serializer = cirq_google.CircuitSerializer()
proto = serializer.serialize(circuit)
```

Use this for offline payload validation before an Engine submission. It catches unsupported program features for the Google API proto format without contacting Google services.

Important distinctions:

- The result is a Google API program proto, not a JSON string.
- The serializer is used by Engine contexts during live submissions.
- Custom operation or tag serialization requires custom `op_serializer`, `op_deserializer`, `tag_serializer`, or `tag_deserializer` objects.
- Cirq JSON may successfully store an object that the Google API serializer cannot submit to a processor.

## IonQ API serialization

IonQ serialization is a service-payload format, not a durable Cirq JSON replacement.

```python
import cirq_ionq

payload = cirq_ionq.Serializer().serialize_single_circuit(circuit)
```

The returned object includes:

- `input`: gateset, qubit count, and serialized non-measurement operations.
- `metadata`: measurement key/target mapping, because IonQ API payloads do not carry measurement gates directly.
- `compilation`, `error_mitigation`, `noise`, and `dry_run` settings for job creation.

Offline failures usually mean one of the following:

- Empty circuit.
- Non-terminal measurements.
- Non-`LineQubit` qubits or invalid line-qubit indices.
- Unresolved symbolic gates.
- Unsupported gates that need `IonQTargetGateset`, `AriaNativeGateset`, or `ForteNativeGateset` compilation.
- Batch circuits mixing QIS/API gates and native gates.

## AQT operation serialization

AQT remote submission uses an AQT-specific sequential operation encoding. Public workflows normally use `AQTSampler` or `AQTSamplerLocalSimulator` rather than manually building the JSON.

Provider-relevant operation forms:

- `cirq.XXPowGate` -> `MS`.
- `cirq.ZPowGate` -> `Z`.
- `cirq.PhasedXPowGate` -> `R`.
- Measurement -> `Meas`.

For offline checks, prefer:

```python
sampler = cirq_aqt.AQTSamplerLocalSimulator(simulate_ideal=True)
result = sampler.run(circuit, repetitions=5)
```

Do not use remote resource discovery or remote sampler calls during offline validation.

## Pasqal serialization

Pasqal sampler submission serializes resolved Cirq circuits with the general Cirq JSON protocol, then posts that JSON to a remote service. Offline validation should use devices first:

```python
device.validate_circuit(circuit)
json_text = cirq.to_json(circuit)
round_tripped = cirq.read_json(json_text=json_text)
```

Import `cirq_pasqal` before reading JSON containing Pasqal devices or qubits so their resolvers are registered.

## `cirq_web` HTML representation

`cirq_web` widgets are display objects. Their `_repr_html_()` method returns an HTML snippet for notebooks or browser rendering:

```python
import cirq_web

widget = cirq_web.Circuit3D(circuit)
html = widget._repr_html_()
assert '<div' in html and '<script' in html
```

HTML representation is not a quantum service payload. It may contain generated element ids and embedded widget assets. Do not rely on exact HTML string equality across versions; check for expected structural markers.

## Serialization validation checklist

- For persistence: `cirq.to_json` then `cirq.read_json` succeeds, with required provider imports/resolvers loaded.
- For Google: `cirq_google.CIRCUIT_SERIALIZER.serialize(circuit)` succeeds.
- For IonQ: `cirq_ionq.Serializer().serialize_single_circuit(circuit)` succeeds after gateset compilation and parameter resolution.
- For AQT: `AQTSamplerLocalSimulator` can encode and sample the circuit locally if the task is AQT-compatible.
- For Pasqal: `device.validate_circuit(circuit)` and Cirq JSON round-trip succeed.
- For widgets: `_repr_html_()` or local HTML generation succeeds without requiring a browser to open.
- In every case: secrets are not serialized, printed, logged, or embedded in notebooks.
