# Provider and visualization workflows

Use these workflows to keep hardware packaging deterministic. They deliberately separate local validation from credentialed submission.

## Universal provider decision flow

1. **Identify the target provider and backend.** Record package, target (`qpu`, `simulator`, processor id, workspace/resource, or remote host), and whether a live service call is allowed.
2. **Build the circuit elsewhere.** For qubits/gates/measurements/parameters, route to `core-circuits-and-ops`; for algorithms, route to `algorithms-and-observables`.
3. **Resolve parameters and measurement layout.** Provider serializers commonly reject unresolved symbols and non-terminal measurements.
4. **Compile before packaging.** If the circuit contains unsupported gates or invalid topology, route to `transformers-and-compilation` and compile/routemap to the provider target gateset/device.
5. **Run offline checks.** Use provider devices, serializers, target gatesets, local simulators, or JSON round-trips to catch obvious errors without credentials.
6. **Stop at the live boundary.** Ask for explicit approval, credentials, project/processor/target/resource details, repetitions, budget, and timeout before live calls.
7. **Submit only when authorized.** Once live calls are authorized, keep job ids, result interpretation, and retries visible to the user.

A task that says “package this for hardware but I do not have credentials” should finish after offline validation and produce the exact remaining live-service requirements.

## Google Quantum AI offline packaging

Use this when a user wants Google-ready circuits without yet submitting to Engine.

```python
import cirq
import cirq_google

q0 = cirq.GridQubit(5, 5)
q1 = cirq.GridQubit(5, 6)
circuit = cirq.Circuit(
    cirq.X(q0) ** 0.5,
    cirq_google.SYC(q0, q1),
    cirq.measure(q0, q1, key='m'),
)

# Static device/layout validation; this does not contact Google services.
cirq_google.Sycamore.validate_circuit(circuit)

# Offline Google program serialization; this does not create a cloud job.
program_proto = cirq_google.CIRCUIT_SERIALIZER.serialize(circuit)
assert program_proto.language.gate_set
```

If validation fails:

- Non-grid or inactive qubit layout: choose valid `cirq.GridQubit`s and check the processor/static device layout.
- Unsupported gates: compile with a Google target gateset in `transformers-and-compilation`.
- Non-terminal measurement: move measurements to the final moment unless the provider workflow explicitly supports otherwise.
- Program too long or repeated subcircuits: consider `cirq.CircuitOperation` to reduce serialized representation and reduce moment depth where possible.

Live Google stop condition:

- Do not create an `Engine` sampler or call Engine processor/job/program methods unless the user provides a Google Cloud project id, processor id or simulated processor target, credentials/IAM access, repetitions, timeout policy, and explicit permission to contact Google services.

## Google Engine live-run skeleton

Use only after live access is authorized:

```python
import cirq_google

engine = cirq_google.Engine(project_id=PROJECT_ID)
sampler = engine.get_sampler(processor_id=PROCESSOR_ID)
# sampler.run(circuit, repetitions=REPETITIONS)  # live service call
```

Keep the `run` line separated in review so the user can see exactly where the cloud call begins.

## IonQ offline packaging

IonQ supports an offline serializer that validates many API constraints.

```python
import cirq
import cirq_ionq

q0, q1 = cirq.LineQubit.range(2)
circuit = cirq.Circuit(
    cirq.H(q0),
    cirq.CNOT(q0, q1),
    cirq.measure(q0, q1, key='m'),
)

# Optional compilation when non-IonQ gates are present.
compiled = cirq.optimize_for_target_gateset(
    circuit,
    gateset=cirq_ionq.IonQTargetGateset(),
    ignore_failures=False,
)

payload = cirq_ionq.Serializer().serialize_single_circuit(compiled)
assert payload.input['qubits'] >= 1
```

Offline constraints to check:

- Use `cirq.LineQubit`s.
- Resolve parameterized gates before serialization.
- Keep measurements terminal.
- Do not mix API/QIS gates and native gates within the same batch.
- Measurement keys must not contain ASCII unit or record separator characters.

Live IonQ stop condition:

- Do not instantiate a real workflow that calls `Service.run`, `create_job`, `get_job`, or a sampler until the user has an IonQ API key, target (`qpu` or `simulator`), retry/timeout preference, repetitions, and explicit permission to contact IonQ.

## IonQ live-run skeleton

Use only after live access is authorized:

```python
import cirq_ionq as ionq

service = ionq.Service(api_key=IONQ_API_KEY, default_target='simulator')
# result = service.run(circuit=compiled, repetitions=REPETITIONS)  # live service call
```

If an API key is available in an environment variable, do not print its value.

## AQT local and remote workflows

Use `AQTSamplerLocalSimulator` for credential-free checks.

```python
import cirq
import cirq_aqt

q0, q1 = cirq.LineQubit.range(2)
circuit = cirq.Circuit(
    cirq.PhasedXPowGate(phase_exponent=0.25, exponent=0.5).on(q0),
    cirq.XX(q0, q1) ** 0.25,
    cirq.measure(q0, q1, key='m'),
)

sampler = cirq_aqt.AQTSamplerLocalSimulator(simulate_ideal=True)
result = sampler.run(circuit, repetitions=5)
assert 'm' in result.measurements
```

AQT local simulation is not a remote resource availability check. It validates that the circuit can be encoded and sampled by the AQT-local path.

Live AQT stop condition:

- Do not call `AQTSampler.fetch_resources`, `print_resources`, `AQTSampler.run`, or `run_sweep` with a remote host until the user supplies a token, workspace id, resource id, repetition count, timeout/polling expectations, and explicit permission to contact AQT.

## Pasqal offline validation

Use Pasqal devices directly before any remote sampler call.

```python
import cirq
import cirq_pasqal

qubits = cirq_pasqal.TwoDQubit.square(2)
device = cirq_pasqal.PasqalVirtualDevice(control_radius=2.0, qubits=qubits)

circuit = cirq.Circuit(
    cirq.H(qubits[0]),
    cirq.CZ(qubits[0], qubits[1]),
    cirq.measure(*qubits, key='m'),
)

device.validate_circuit(circuit)
json_text = cirq.to_json(circuit)
assert 'Pasqal' in json_text or 'TwoDQubit' in json_text
```

If validation fails:

- `Unsupported qubit type`: choose the device's required qubit type.
- `not part of the device`: construct the circuit using exactly the device's qubits.
- `too far away`: adjust the layout/control radius or route to a compatible connectivity pattern.
- `Cannot do simultaneous gates`: rebuild with one non-measurement operation per moment.
- `Non-empty moment after measurement`: move all measurement to the final moment.

Live Pasqal stop condition:

- Do not call `PasqalSampler.run` or `run_sweep` until the user supplies a remote host, token if required, device choice, repetitions, polling expectations, and explicit permission to contact Pasqal.

## `cirq_web` visualization workflow

Use `cirq_web` when the deliverable is a local or notebook visualization, not a provider submission.

```python
import cirq
import cirq_web

q0, q1 = cirq.LineQubit.range(2)
circuit = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1), cirq.measure(q0, q1, key='m'))
widget = cirq_web.Circuit3D(circuit)
html = widget._repr_html_()
assert '<script' in html and '<div' in html
```

For a local HTML artifact, use widget file generation only when the user requests a file. Browser opening is optional and may fail in headless environments even when the HTML content is valid.

## Offline validation checklist

Before telling the user a circuit is provider-ready, verify as much as possible without credentials:

- Required optional package imports succeed.
- Provider-specific qubit type and device topology are correct.
- Measurements are terminal if required by the provider.
- Parameters are resolved or the provider explicitly supports the symbolic expression subset.
- Target gateset compilation succeeds with `ignore_failures=False` when unsupported gates should be hard errors.
- Provider serializer/device validation succeeds locally.
- Cirq JSON round-trip succeeds for persistence workflows.
- Tokens and credential values are neither printed nor serialized.

## Handoff for credentialed execution

When offline validation is complete but live execution is blocked, return a short handoff:

- Provider and package.
- Circuit or payload status: validated / serialized / compiled / unresolved.
- Required secrets or account access, without values.
- Required ids: project, processor, target, workspace/resource, or remote host.
- Suggested first live call and why it is safe to run next.
- Timeout/retry/repetition choices still needing approval.
