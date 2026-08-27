# Troubleshooting: providers, credentials, unsupported gates, and visualization

Use this reference when a provider workflow fails before or during packaging. Start with offline checks and stop before live service calls unless the user has explicitly authorized them.

## Quick triage table

| Symptom | Likely cause | Offline action | Live-service action only if authorized |
| --- | --- | --- | --- |
| `ModuleNotFoundError: cirq_google` or another provider package | Optional provider package is not installed in the active Python environment. | Install or select the provider package; run `scripts/inspect_provider_imports.py` after install. | None. |
| `Engine` authentication/permission error | Missing Google credentials, disabled API, wrong project, missing IAM/processor access. | Verify circuit with static devices and `CIRCUIT_SERIALIZER`; record required project/processor credentials. | Confirm project id, processor id, API enablement, billing/IAM, and ADC/service credentials. |
| IonQ `EnvironmentError` about API key | `api_key` omitted and `CIRQ_IONQ_API_KEY` / `IONQ_API_KEY` unset. | Use `cirq_ionq.Serializer` for offline validation without a service. | Provide a key through secure runtime configuration; do not print it. |
| AQT token/workspace/resource error | Token absent, workspace/resource id wrong, or user lacks resource access. | Use `AQTSamplerLocalSimulator` for local checks. | Use token-based resource discovery only with permission. |
| Pasqal sampler assertion or HTTP error | Device missing, invalid remote host/token, or service unavailable. | Validate with `PasqalDevice`/`PasqalVirtualDevice` and Cirq JSON. | Confirm remote host, token, device, and polling expectations. |
| Provider rejects a gate | Circuit contains gates outside the provider gateset or target topology. | Compile using `transformers-and-compilation` with provider target gateset and `ignore_failures=False`. | Submit only after offline serializer/device validation succeeds. |
| `read_json` cannot resolve a type | Missing provider import or custom resolver. | Import the package that defines the object or prepend a custom resolver. | None. |
| `cirq_web` widget shows blank or errors | Missing frontend assets, headless browser, WebGL/browser limitation, or notebook display issue. | Check `_repr_html_()` for structural HTML; generate local HTML if requested. | Browser opening is user-environment dependent, not a provider service issue. |

## Missing provider package or dependency

Provider integrations are optional packages. If imports fail:

1. Identify the missing import: `cirq_google`, `cirq_ionq`, `cirq_aqt`, `cirq_pasqal`, or `cirq_web`.
2. Confirm the task actually needs that provider. Route pure circuit/simulation work elsewhere.
3. Install or switch to an environment containing that optional package.
4. Run the bundled import/signature helper to verify that public entry points are available.

Do not proceed to live-service debugging until imports and offline serialization/validation are working.

## Credential and token issues

### Google Quantum AI

Live Google Engine calls require:

- Google Cloud project id.
- Quantum API access and billing/project setup.
- User or service credentials available to the runtime.
- IAM permissions and processor access.
- Processor id or a documented simulated processor target.

Offline alternatives:

- `cirq_google.Sycamore`, `Sycamore23`, or `Willow105` static device validation.
- `cirq_google.SycamoreTargetGateset` or `GoogleCZTargetGateset` compilation.
- `cirq_google.CIRCUIT_SERIALIZER.serialize(circuit)` payload validation.

Stop if the user cannot provide project/processor details or permission to contact Google services.

### IonQ

Credential lookup accepts direct `api_key` or environment variables `CIRQ_IONQ_API_KEY` / `IONQ_API_KEY`. Endpoint lookup accepts direct `remote_host` or `CIRQ_IONQ_REMOTE_HOST` / `IONQ_REMOTE_HOST`.

Offline alternatives:

- `cirq_ionq.IonQTargetGateset`, `AriaNativeGateset`, or `ForteNativeGateset` compilation.
- `cirq_ionq.Serializer().serialize_single_circuit(circuit)`.

Stop if `target` (`qpu` or `simulator`), retry/timeout, repetitions, and live-call permission are missing.

### AQT

AQT remote calls require:

- Access token.
- Workspace id.
- Resource id.
- Optional remote host override.

Offline alternatives:

- `cirq_aqt.AQTSamplerLocalSimulator(simulate_ideal=True)` for ideal local behavior.
- `simulate_ideal=False` for local AQT noise-model behavior.

Resource discovery (`fetch_resources`, `print_resources`) is a network call and should not be used as an offline check.

### Pasqal

Pasqal remote sampler calls require:

- Remote host.
- Access token if the service requires it.
- A `PasqalDevice` or `PasqalVirtualDevice` for validation in `run_sweep`.

Offline alternatives:

- Build `TwoDQubit`/`ThreeDQubit` layouts or named-qubit generic devices.
- `device.validate_circuit(circuit)`.
- `cirq.to_json` / `cirq.read_json` round-trip after importing `cirq_pasqal`.

## Unsupported gates and target constraints

Provider rejection usually means the circuit is valid Cirq but not valid for the target provider.

Common checks:

- **Google:** use grid qubits on the selected static/device layout; compile to `SycamoreTargetGateset` or `GoogleCZTargetGateset`; keep measurements terminal; check moment structure and circuit duration assumptions.
- **IonQ:** use `LineQubit`s; terminal measurements; resolved parameters; compile to `IonQTargetGateset` or a native gateset; avoid mixed native/QIS batches.
- **AQT:** use `LineQubit`s and AQT-compatible `XX`, `Z`, `PhasedXPowGate`, and measurement operations; local simulator catches many encoding issues.
- **Pasqal:** use device-owned qubits; terminal measurements; no unsupported invert masks; obey `PasqalVirtualDevice` control-radius and moment restrictions.

When conversion is needed, route to `transformers-and-compilation` and require `ignore_failures=False` during debug so unsupported operations do not remain silently.

## Serialization resolver failures

Failure forms:

- `Could not resolve type ... during deserialization`.
- Error about user-specified `cirq_type` in `_json_dict_`.
- A provider object serializes in one environment but cannot read in another.

Fixes:

1. Import the provider package before `cirq.read_json`.
2. For custom classes, define `_json_namespace_`, `_json_dict_`, and `_from_json_dict_` if needed.
3. Pass `resolvers=[custom_resolver, *cirq.DEFAULT_RESOLVERS]` to `read_json`.
4. Align provider package versions across writer and reader when exchanging provider-specific gates/devices.
5. Do not serialize service clients, samplers, token-bearing objects, or live job handles.

## `cirq_web` frontend and browser limitations

Symptoms:

- HTML repr exists but nothing displays in a notebook.
- Browser does not open.
- WebGL/JavaScript console errors appear.
- Frontend assets are missing from the installed package.

Actions:

- Use `_repr_html_()` as a browserless structural check.
- If file output is required, generate an HTML file and report the path to the user; do not require browser opening in headless sessions.
- If HTML contains widget markup but rendering fails, treat it as a browser/frontend environment issue, not a quantum circuit issue.
- Do not install or run Node/npm/frontend development checks for normal package-user workflows.

## Safe stop conditions

Stop and ask or hand off rather than guessing when:

- A task would contact a cloud service and the user did not explicitly permit network access.
- A token/project/processor/target/resource is missing.
- The expected cost, queue time, repetitions, timeout, or retry policy is unknown.
- Offline serializer/device validation fails and the required compilation route is unclear.
- Provider terms, account access, or hardware authorization is uncertain.

## Native offline checks to propose

- Provider import/signature check with `scripts/inspect_provider_imports.py`.
- Cirq JSON round-trip of a tiny circuit.
- Google `CIRCUIT_SERIALIZER.serialize` on a compiled grid-qubit circuit.
- IonQ `Serializer().serialize_single_circuit` on a compiled line-qubit circuit.
- AQT `AQTSamplerLocalSimulator` sample of an AQT-compatible line-qubit circuit.
- Pasqal `PasqalVirtualDevice.validate_circuit` plus Cirq JSON round-trip.
- `cirq_web.Circuit3D(...)._repr_html_()` structural check.
