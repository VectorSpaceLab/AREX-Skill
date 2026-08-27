---
name: transformers-and-compilation
description: "Use Cirq transformers, target gatesets, and routing workflows to
  compile circuits to gate and topology constraints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Cirq transformers and compilation

Use this sub-skill when a task needs Cirq circuit transformations rather than raw circuit construction, simulation, provider submission, or algorithm design.

## Use this when

- Applying or composing `@cirq.transformer` functions/classes.
- Configuring `cirq.TransformerContext`, transformer logging, ignored tags, or deep `CircuitOperation` handling.
- Cleaning or rewriting circuits with built-in transformers such as `drop_empty_moments`, `merge_single_qubit_gates_to_phxz`, `eject_z`, `expand_composite`, or `optimize_for_target_gateset`.
- Compiling to `cirq.CompilationTargetGateset` implementations such as `cirq.CZTargetGateset`, `cirq.SqrtIswapTargetGateset`, or offline `cirq_google.SycamoreTargetGateset`.
- Routing circuits with `cirq.RouteCQC`, `cirq.LineInitialMapper`, hard-coded initial mappings, named topologies, or physical device graphs.

## Route elsewhere

- Circuit construction, qubits, gates, measurements, custom gates, or JSON/QASM basics: `core-circuits-and-ops`.
- Running local simulators, sweeps, noise, histograms, or performance studies: `simulation-study-and-noise`.
- Provider credentials, cloud jobs, samplers, serializers, or device submission: `hardware-providers-and-serialization`.
- Algorithm-level motivation and observable expectation workflows: `algorithms-and-observables`.

## Reference map

- Start with [API reference](references/api-reference.md) for signatures, target gatesets, and routing objects.
- Use [Transformer workflows](references/transformer-workflows.md) for pass ordering, custom transformers, no-compile tags, and deep subcircuits.
- Use [Routing and targets](references/routing-and-targets.md) for device graphs, `RouteCQC`, named topologies, placements, and provider-gateset cross-links.
- Use [Troubleshooting](references/troubleshooting.md) when transformed circuits still contain unsupported gates, tags are not honored, routing fails, or moment structure changes unexpectedly.

## Bundled safe helper

Run the deterministic helper when you need a quick offline sanity check of the installed Cirq transformer stack:

```bash
python scripts/inspect_transformer_pipeline.py --help
python scripts/inspect_transformer_pipeline.py --target cz
python scripts/inspect_transformer_pipeline.py --target sycamore
```

The helper builds a tiny local circuit, applies a short transformer pipeline, compiles to a target gateset, and performs a local unitary equivalence check. It never contacts provider services.

## Operating guardrails

- Treat compilation as a pipeline: choose target constraints first, order passes deliberately, and validate after each major boundary when possible.
- Prefer `ignore_failures=False` while debugging target-gateset conversion so unsupported operations do not remain silently.
- Use `TransformerContext(tags_to_ignore=...)` for protected/no-compile operations and `TransformerContext(deep=True)` only when nested `CircuitOperation` bodies must be transformed.
- Route topology first, then compile routed gates to the target gateset required by the physical device or provider workflow.
- For live hardware submission or credentialed provider validation, stop here and route to `hardware-providers-and-serialization` after offline compilation checks.
