# Provider API reference: hardware, samplers, serializers, and widgets

This reference covers provider-facing public APIs in the optional Cirq packages. It assumes the circuit object already exists. Use `core-circuits-and-ops` for circuit construction and `transformers-and-compilation` when a circuit must be rewritten for a provider gateset or topology before packaging.

## Package boundaries

| Package import | Primary scope | Offline-safe uses | Live-service boundary |
| --- | --- | --- | --- |
| `cirq_google` | Google Quantum AI Engine, devices, target gatesets, program serializers, workflow objects. | Import package, inspect signatures, use static devices, compile to Google target gatesets, serialize circuits to Google program protos. | Engine client operations, processor/job/program listing, sampler `run`/`run_sweep`, calibration/device queries from Engine. |
| `cirq_ionq` | IonQ API service, sampler, target gatesets, serializer, result objects. | Import package, compile to IonQ target gatesets, serialize circuits with `cirq_ionq.Serializer`. | `Service` calls, `Sampler` execution, calibrations, job creation/listing/results. |
| `cirq_aqt` | AQT remote sampler and local simulator. | Import package, run `AQTSamplerLocalSimulator`, inspect AQT-compatible gate encoding. | `AQTSampler`, resource discovery, remote submit/result polling. |
| `cirq_pasqal` | Pasqal qubits/devices/sampler and Cirq JSON-based remote serialization. | Import package, create qubits/devices, validate circuits, serialize circuits with Cirq JSON. | `PasqalSampler.run`/`run_sweep` and remote result polling. |
| `cirq_web` | Browser/notebook visualization widgets. | Import package, create widget objects, check HTML representation, generate local HTML files. | Opening a browser is optional; no cloud service is required. |

Provider clients and samplers can often be constructed without immediately submitting a job, but live boundary methods should still be treated as credentialed network calls.

## Google Quantum AI (`cirq_google`)

### Engine and sampler entry points

```python
cirq_google.Engine(
    project_id,
    proto_version=None,
    service_args=None,
    verbose=None,
    timeout=None,
    context=None,
    compress_run_context=False,
)

cirq_google.get_engine_sampler(processor_id, project_id=None)
```

Operational notes:

- `Engine(project_id=...)` is the main client for the Quantum Engine API. It needs Google Cloud project access, enabled service/API access, application-default or equivalent credentials, and processor permissions for live calls.
- `get_engine_sampler(processor_id, project_id=None)` is a convenience for a `ProcessorSampler`; sampler execution is live.
- Engine methods that create/list/get programs, jobs, processors, calibrations, reservations, or devices are live API calls. Stop before those unless the user explicitly authorizes cloud access.
- `timeout` applies to polling; unset polling can wait indefinitely for long jobs.
- `compress_run_context=True` can reduce payload size for large sweep/run-context submissions but does not remove credential requirements.

### Static devices, gates, and target gatesets

Common public device/layout objects:

- `cirq_google.Sycamore`: static Sycamore layout.
- `cirq_google.Sycamore23`: smaller Sycamore subset.
- `cirq_google.Willow105`: static Willow-family layout.

Common Google gates and tags:

- `cirq_google.SYC`: Sycamore gate.
- `cirq_google.WILLOW`: Willow gate.
- `cirq_google.PhysicalZTag`: marks a Z gate as a physical Z operation instead of a virtual phase update.
- Other provider-specific gates/tags include calibration, wait, reset, analog detuning, and internal gate objects.

Target gatesets:

```python
cirq_google.SycamoreTargetGateset(*, atol=1e-8, tabulation=None)
cirq_google.GoogleCZTargetGateset(atol=1e-8, eject_paulis=False, additional_gates=())
```

Using a target gateset locally does not contact Google services. Use it for offline compilation checks, then route to provider submission only after the circuit has acceptable gates, qubits, terminal measurements, and moment structure.

### Serialization and workflow objects

```python
cirq_google.CircuitSerializer(
    op_serializer=None,
    op_deserializer=None,
    tag_serializer=None,
    tag_deserializer=None,
    **kwargs,
)
```

- `cirq_google.CIRCUIT_SERIALIZER` and `cirq_google.CircuitSerializer()` serialize Cirq circuits into Google API program protos without contacting the service.
- `CircuitSerializer.serialize(circuit)` is an offline way to catch unsupported Google-program serialization features.
- `CircuitOperation` can condense repeated subcircuits and reduce serialized payload size.
- The package exposes workflow objects such as `QuantumExecutable`, `QuantumExecutableGroup`, `BitstringsMeasurement`, runtime/result records, `QuantumRuntimeConfiguration`, `ProcessorRecord`, `EngineProcessorRecord`, `SimulatedProcessorRecord`, and local-device simulated processor records. Workflow execution through Engine records can be live; simulated/local records remain offline when they use local devices/samplers.

## IonQ (`cirq_ionq`)

### Service and sampler

```python
cirq_ionq.Service(
    remote_host=None,
    api_key=None,
    default_target=None,
    api_version='v0.4',
    max_retry_seconds=3600,
    job_settings=None,
    verbose=False,
)

cirq_ionq.Sampler(service, target, timeout_seconds=None, seed=None)
```

Credential and endpoint lookup:

- `api_key` may be passed directly or loaded from `CIRQ_IONQ_API_KEY` / `IONQ_API_KEY`.
- `remote_host` may be passed directly or loaded from `CIRQ_IONQ_REMOTE_HOST` / `IONQ_REMOTE_HOST`; otherwise it defaults to the public IonQ API version endpoint.
- `default_target` can be `qpu` or `simulator`; without a default, calls must specify `target`.
- `max_retry_seconds` bounds retry/polling time for API calls.

Live boundaries include `Service.run`, `run_batch`, `create_job`, `create_batch_job`, `get_job`, `list_jobs`, calibration queries, and sampler execution.

### Gatesets and serializer

Useful public objects:

- `cirq_ionq.IonQTargetGateset(*, atol=1e-8)`: compiles general one- and two-qubit unitary gates to IonQ API gates.
- `cirq_ionq.AriaNativeGateset(*, atol=1e-8)` and `cirq_ionq.ForteNativeGateset(*, atol=1e-8)`: native IonQ device gatesets.
- Native gates include `GPIGate`, `GPI2Gate`, `MSGate`, and `ZZGate`.
- `cirq_ionq.Serializer(atol=1e-8)` serializes circuits for the IonQ API without itself performing network calls.

Serializer constraints to validate offline:

- Circuits cannot be empty.
- Measurements must be terminal.
- Qubits must be `cirq.LineQubit` instances with nonnegative contiguous-style indices.
- Parameterized gates must be resolved before serialization.
- Unsupported gates should be routed to `cirq.optimize_for_target_gateset(..., gateset=cirq_ionq.IonQTargetGateset())` or to a native gateset workflow.
- Batch submissions cannot mix IonQ API/QIS gates and native gates in the same batch.

## AQT (`cirq_aqt`)

### Remote sampler and local simulator

```python
cirq_aqt.AQTSampler(
    workspace,
    resource,
    access_token,
    remote_host='https://arnica.aqt.eu/api/v1/',
)

cirq_aqt.AQTSamplerLocalSimulator(
    workspace='',
    resource='',
    access_token='',
    remote_host='',
    simulate_ideal=False,
)
```

Operational notes:

- Remote AQT usage requires a workspace id, resource id, and access token.
- `AQTSampler.fetch_resources(access_token, remote_host=...)` and `print_resources(...)` contact the AQT API; do not run them in offline validation.
- `AQTSamplerLocalSimulator` is credential-free and can be used as a drop-in local sampler for AQT-compatible circuits. `simulate_ideal=True` disables the AQT noise model; the default uses a local AQT-specific noisy simulation.
- AQT circuits are encoded as a sequential list of operations. Supported operation strings include `MS`, `Z`, `R`, and `Meas`, corresponding to `cirq.XXPowGate`, `cirq.ZPowGate`, `cirq.PhasedXPowGate`, and measurement.
- AQT local simulation appends or expects measurement behavior around key `m`; keep measurement interpretation explicit.

## Pasqal (`cirq_pasqal`)

### Qubits and devices

```python
cirq_pasqal.PasqalDevice(qubits)
cirq_pasqal.PasqalVirtualDevice(control_radius, qubits)
cirq_pasqal.TwoDQubit.square(diameter, x0=0, y0=0)
cirq_pasqal.ThreeDQubit.cube(diameter, x0=0, y0=0, z0=0)
```

Device rules:

- `PasqalDevice` is a generic device using `cirq.NamedQubit` objects and assumes broad connectivity handled by the provider side.
- `PasqalVirtualDevice` uses physically placed qubits (`ThreeDQubit`, `TwoDQubit`, `cirq.GridQubit`, or `cirq.LineQubit`), a nonnegative `control_radius`, and controlled-gate distance checks.
- The generic Pasqal gateset includes identity, measurement, phased-X, X/Y/Z powers, H, CNOT, CZ, CCX, and CCZ subject to device restrictions.
- `PasqalVirtualDevice` removes some multi-controlled operations and does not allow simultaneous non-measurement gates in one moment.
- Measurements must be terminal, and Pasqal measurement invert masks are not supported.

### Sampler

```python
cirq_pasqal.PasqalSampler(remote_host, access_token='', device=None)
```

- The sampler uses remote HTTP submission and polling when `run`/`run_sweep` is called.
- Offline validation should instantiate and use devices directly, call `device.validate_circuit(circuit)`, and serialize with `cirq.to_json` if a payload shape check is needed.
- A sampler with no `device` is not a substitute for validation; `run_sweep` asserts that a Pasqal device is present.

## `cirq_web`

```python
cirq_web.Circuit3D(circuit, resolvers=(DefaultResolver,), padding_factor=1)
```

Public objects include `Widget`, `BlochSphere`, and `Circuit3D`.

Operational notes:

- `Circuit3D(circuit)` creates a browser/notebook visualization object for a circuit.
- `_repr_html_()` returns an HTML snippet suitable for notebook display; this is a browserless smoke check.
- `generate_html_file(...)` writes a local HTML file and can optionally try to open a browser. Treat browser opening as optional and environment-dependent.
- Widget display depends on bundled frontend assets and browser/WebGL support; no cloud credentials are involved.

## Core JSON entry points

```python
cirq.to_json(obj, file_or_fn=None, *, indent=2, separators=None, cls=cirq.CirqEncoder)
cirq.read_json(file_or_fn=None, *, json_text=None, resolvers=None)
```

Use the dedicated [Serialization](serialization.md) reference for round-trips, custom resolvers, provider resolver registration, and the difference between Cirq JSON and provider API payload formats.
