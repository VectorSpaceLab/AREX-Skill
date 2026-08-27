# Cirq Package Overview

## Purpose

Read this when deciding which Cirq package, optional dependency, or sub-skill route fits a task. This reference is intentionally package-user focused and does not require the original source checkout.

## Package family

Cirq is a Python framework for writing, transforming, simulating, serializing, and submitting quantum circuits. The public package family is split into a core package plus provider/visualization packages:

| Distribution | Import | Main role | Notes |
| --- | --- | --- | --- |
| `cirq` | `cirq` plus providers | Metapackage that installs the Cirq family from PyPI. | Best first install for most users who want all supported packages. |
| `cirq-core` | `cirq` | Core circuits, gates, protocols, simulators, sweeps, noise, transformers, devices, interop. | Use when no hardware-provider packages are needed. |
| `cirq-google` | `cirq_google` | Google Quantum AI devices, Engine, target gatesets, serializers, calibration, workflow helpers. | Live execution requires Google Cloud credentials/project/processor access. |
| `cirq-ionq` | `cirq_ionq` | IonQ API service, sampler, target gatesets, serializer, native gates. | Live execution requires IonQ credentials. |
| `cirq-aqt` | `cirq_aqt` | AQT sampler/device helpers and local simulator wrapper. | Live execution requires AQT access token/workspace/resource. |
| `cirq-pasqal` | `cirq_pasqal` | Pasqal qubits/devices/noise/sampler helpers. | Live execution requires Pasqal service access. |
| `cirq-web` | `cirq_web` | HTML/browser-oriented 3D circuit and Bloch sphere widgets. | Rendering may depend on notebook/browser frontend support. |

All packages in this generated skill were inspected at version `1.8.0.dev0`.

## Python and dependency stance

- Cirq supports Python 3.11 and later.
- `cirq-core` depends on scientific Python packages such as NumPy, SciPy, pandas, SymPy, NetworkX, Matplotlib, attrs, duet, and tqdm.
- Some `cirq.contrib` integrations have optional dependencies such as QASM/LaTeX/quimb-related packages. Do not treat optional contrib imports as part of the base install unless the task explicitly uses those integrations.
- Provider packages add HTTP/gRPC/protobuf/credential-related dependencies, but importing provider packages should not by itself submit jobs.
- No CUDA, ROCm, MPS, TPU, or vendor accelerator runtime is required for local Cirq circuit construction or CPU simulation in this skill.

## Routing by task

| Task shape | Start with |
| --- | --- |
| Build circuits, choose qubit classes, work with gates/operations/moments, debug measurement keys, serialize a simple circuit | `sub-skills/core-circuits-and-ops/` |
| Run a local simulation, sample measurements, sweep parameters, inspect histograms/state vectors/density matrices, add noise/channels | `sub-skills/simulation-study-and-noise/` |
| Optimize, decompose, transform, route, or compile a circuit to a gateset/topology/provider constraint | `sub-skills/transformers-and-compilation/` |
| Implement algorithm examples, Pauli observables, expectation values, QFT/phase estimation/Grover/QAOA-like checks | `sub-skills/algorithms-and-observables/` |
| Use Google/IonQ/AQT/Pasqal packages, provider serializers, credentials, local provider mocks, or `cirq_web` widgets | `sub-skills/hardware-providers-and-serialization/` |

## Minimal environment check

After installation, a safe check is:

```python
import cirq
q = cirq.LineQubit(0)
circuit = cirq.Circuit(cirq.X(q), cirq.measure(q, key="m"))
print(cirq.Simulator(seed=1234).run(circuit, repetitions=4))
```

For a broader local diagnostic, run the bundled helper `scripts/check_cirq_environment.py` from the root of this generated skill. It performs only local imports, a tiny CPU simulation, and a JSON roundtrip.
