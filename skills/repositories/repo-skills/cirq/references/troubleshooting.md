# Cirq Cross-cutting Troubleshooting

## Purpose

Read this for install/import/version/provider issues that affect more than one Cirq workflow. For workflow-specific failures, use the nearest sub-skill troubleshooting reference.

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'cirq'` | Cirq is not installed in the active Python environment. | Install `cirq` for the full family or `cirq-core` for local core workflows. Then run `python -c "import cirq; print(cirq.__version__)"`. |
| Provider import fails, such as `No module named 'cirq_google'` | Only `cirq-core` is installed, or a provider distribution is missing. | Install the needed distribution (`cirq-google`, `cirq-ionq`, `cirq-aqt`, `cirq-pasqal`, or `cirq-web`) or install the `cirq` metapackage. |
| Cirq imports from an unexpected version | Multiple Python environments or stale editable installs. | Check `python -m pip show cirq-core cirq-google` and run the root helper `scripts/check_cirq_environment.py --text`. Make sure the Python used by the agent is the same Python used to install Cirq. |
| Resolver errors around NumPy/SciPy/pandas/Matplotlib | Unsupported Python version or incompatible package pins. | Use Python 3.11+ supported by Cirq and reinstall into a clean environment. Avoid mixing old scientific packages from another stack. |
| Optional `cirq.contrib` import fails | Optional contrib dependencies were not installed. | Install only the optional package needed by that workflow. Do not install broad extras unless the task truly requires them. |

## Local execution surprises

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `cirq.Simulator.run` returns measurement samples but no final state | `run`/`sample` are sampler-style APIs. | Use `simulate` or `simulate_sweep` from `simulation-study-and-noise` for state access. |
| `cirq.unitary(circuit)` fails | Circuit contains measurement, reset, noisy channels, or unresolved symbols. | Remove non-unitary operations or switch to density/noise simulation. Resolve symbols before unitary checks. |
| Results change between runs | Random simulator/sampler seed is not fixed, or noisy sampling is stochastic. | Set `seed=` on simulators/samplers and record repetitions. |
| Memory grows quickly | State-vector simulation scales as `2**n` amplitudes and density matrices scale worse. | Reduce qubits, use sampling-only checks, exploit structure, or switch to a Clifford/stabilizer path when applicable. |

## Provider and credential failures

Provider packages can be imported and inspected offline, but live quantum-service calls require credentials, projects/accounts, targets/processors, and service availability.

| Provider | Credential/service signal | Recovery |
| --- | --- | --- |
| Google Quantum AI | Google Cloud credentials, project id, processor id, Engine access, IAM permissions. | Use `hardware-providers-and-serialization` for offline serialization/target-gateset validation first. Stop before live calls until credentials and processor access are confirmed. |
| IonQ | API key and optional remote host/default target. | Validate circuit shape and IonQ serializer/gateset locally, then provide credentials only in the execution environment. |
| AQT | Access token, workspace, resource, remote host. | Prefer `AQTSamplerLocalSimulator` for local behavior checks; do not call remote resources without token/workspace confirmation. |
| Pasqal | Access token, remote host, compatible Pasqal device/qubits. | Validate device/qubit constraints locally; stop before remote calls without service access. |

Never paste API keys or cloud credentials into generated skill files, prompts, logs, or test artifacts. Prefer environment variables or the provider's documented credential mechanism in the user's execution environment.

## Serialization and compatibility

- Use `cirq.to_json`/`cirq.read_json` for Cirq objects that have registered resolvers.
- Custom classes need a `cirq_type`/JSON resolver strategy; otherwise JSON roundtrip may fail even when Python `repr` works.
- QASM support is a subset and may not preserve every Cirq gate, tag, calibration, or provider-specific operation.
- Provider serializers usually accept only supported gatesets/devices. If serialization fails because a gate is unsupported, route to `transformers-and-compilation` to compile or decompose first.

## Root diagnostic helper

Run the bundled root helper from the generated skill root:

```bash
python scripts/check_cirq_environment.py --text
python scripts/check_cirq_environment.py --skip-providers --text
```

The helper only imports packages, performs a tiny CPU simulation, and JSON-roundtrips a small circuit. It does not contact cloud services.
