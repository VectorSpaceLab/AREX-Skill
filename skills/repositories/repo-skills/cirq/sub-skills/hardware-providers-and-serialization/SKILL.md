---
name: hardware-providers-and-serialization
description: "Use Cirq provider packages, provider-safe serialization, and
  browser visualization workflows without accidental live hardware calls."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Cirq hardware providers and serialization

Use this sub-skill when a task touches Cirq provider packages, hardware-facing samplers, provider serializers, credentials, JSON persistence, or `cirq_web` visualization. Default to offline inspection and validation; make live service calls only when the user explicitly supplies credentials, project/processor/target details, and permission to contact the service.

## Use this when

- Working with `cirq_google.Engine`, `get_engine_sampler`, Google devices such as `Sycamore` or `Willow105`, Google target gatesets, serializers, or workflow objects.
- Preparing IonQ circuits with `cirq_ionq.Service`, `cirq_ionq.Sampler`, IonQ serializers, or IonQ target gatesets.
- Using AQT `AQTSampler`, `AQTSamplerLocalSimulator`, workspace/resource/token concepts, or AQT-local validation.
- Using Pasqal `PasqalSampler`, `PasqalDevice`, `PasqalVirtualDevice`, `TwoDQubit`, or `ThreeDQubit`.
- Rendering provider-adjacent visualizations with `cirq_web.Circuit3D`, widgets, or offline HTML representations.
- Persisting or exchanging Cirq objects with `cirq.to_json`, `cirq.read_json`, provider JSON resolvers, or custom serialization hooks.

## Route elsewhere

- Generic qubits, gates, operations, circuit construction, parameters, diagrams, or JSON basics: `core-circuits-and-ops`.
- Local simulator-only studies, noisy simulation, histograms, sweeps, or result analysis: `simulation-study-and-noise`.
- Decomposing unsupported gates, routing to a topology, or compiling to target gatesets before provider packaging: `transformers-and-compilation`.
- Algorithm design or observable expectation workflows before hardware packaging: `algorithms-and-observables`.

## Reference map

- Start with [Provider API reference](references/provider-api-reference.md) for public package boundaries, key signatures, devices, samplers, serializers, target gatesets, and widget objects.
- Use [Provider and visualization workflows](references/provider-and-visualization-workflows.md) for offline packaging, credential gates, live-run stop conditions, and `cirq_web` usage.
- Use [Serialization](references/serialization.md) for `cirq.to_json`, `cirq.read_json`, custom resolvers, provider resolver registration, and distinctions between Cirq JSON and provider API serialization.
- Use [Troubleshooting](references/troubleshooting.md) for missing optional packages, absent credentials, project/target errors, unsupported gates, resolver failures, and browser/frontend limitations.

## Bundled safe helper

Run the deterministic helper to inspect installed provider packages and perform an optional JSON/widget smoke check without network or credentials:

```bash
python scripts/inspect_provider_imports.py --help
python scripts/inspect_provider_imports.py
python scripts/inspect_provider_imports.py --check-widget-html
```

The helper imports provider packages, reports sanitized public signatures, can round-trip a tiny circuit with Cirq JSON, and never creates live cloud jobs, opens sockets, prints token values, or reads any source checkout.

## Operating guardrails

- Treat cloud access as opt-in. Stop before `run`, `run_sweep`, `create_job`, `list_*`, `get_*`, resource discovery, or sampler execution unless the user explicitly authorizes a live service call.
- Separate three phases: circuit construction, offline provider validation/serialization, then credentialed submission. Route construction and compilation to their sub-skills before submission.
- Never store API tokens, project secrets, or credential file contents in Cirq JSON, notebooks, logs, or bundled scripts.
- Prefer provider serializers, device validation, and target gatesets for offline rejection of unsupported gates; use the transformers sub-skill when conversion is needed.
- For `cirq_web`, assume a local browser or notebook display is optional. Validate by generating an HTML representation, not by requiring WebGL, Node, npm, or a browser automation stack.
