---
name: providers
description: "Guides agents using Qiskit BackendV2, Options, Job abstractions,
  BasicProvider, BasicSimulator, and GenericBackendV2 fake backends."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Qiskit provider and backend workflows

Use this sub-skill when the task involves Qiskit backend/provider interfaces, local simulators, fake backends, job/status/options objects, or backend-facing validation.

## Read next

- `references/workflows.md` for `BasicProvider`, `BasicSimulator`, `GenericBackendV2`, `BackendV2`, and `Options` usage.
- `references/troubleshooting.md` for backend lookup, basis-gate, coupling-map, options, and Aer/noise fallback issues.
- `../transpiler/SKILL.md` when a backend is only being used as a transpilation target.
- `../../scripts/check_qiskit_environment.py --sections providers transpiler` for a source-free provider and fake-backend smoke check.

## Include here

- `qiskit.providers.Backend`, `BackendV2`, `Job`, `JobV1`, `JobStatus`, and `Options`.
- `qiskit.providers.basic_provider.BasicProvider`, `BasicSimulator`, and `BasicProviderJob`.
- `qiskit.providers.fake_provider.GenericBackendV2` and fake-backend targets.
- Backend option validation, `run()` inputs, backend filtering, and simulator/fake-backend selection.

## Exclude or route elsewhere

- Detailed compilation strategy belongs in `../transpiler/SKILL.md`.
- Primitive sampler/estimator usage belongs in `../primitives/SKILL.md`.
- Circuit construction belongs in `../circuit/SKILL.md`.
- Visualization of backend maps or layouts belongs in `../visualization/SKILL.md`.
- External provider packages such as IBM Runtime or Aer belong to their own package-specific guidance when the task is not about the core Qiskit provider interface.

## Default route

Start here when the user asks how to select a backend, run a circuit with `BasicSimulator`, build a fake backend, set backend options, implement a provider/backend, or interpret provider-related errors.

## What to remember

- `GenericBackendV2` can supply realistic targets for transpilation and can run via Aer if installed, otherwise with `BasicSimulator` without noise.
- `BasicProvider().get_backend("basic_simulator")` is the simplest local backend lookup path.
- Backend options may have validators; do not silently pass invalid shots or mode values.
