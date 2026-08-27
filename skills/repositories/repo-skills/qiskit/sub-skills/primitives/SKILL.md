---
name: primitives
description: "Guides agents using StatevectorSampler, StatevectorEstimator,
  primitive jobs, PUBs, and primitive result containers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Qiskit primitives workflows

Use this sub-skill when the task is about Qiskit's primitive interfaces: sampling circuits, estimating expectation values, binding parameter sweeps, and reading primitive result containers.

## Read next

- `references/workflows.md` for sampler/estimator recipes and result-access patterns.
- `references/troubleshooting.md` for data-shape mistakes, missing measurements, and result-indexing errors.
- `../../references/module-map.md` for the package map.
- `../../scripts/check_qiskit_environment.py --sections primitives` for a source-free primitive smoke check.

## Include here

- `StatevectorSampler`, `StatevectorEstimator`, PUBs, and `run()` usage.
- Primitive job/result container classes such as `PrimitiveResult`, `PubResult`, `SamplerPub`, `EstimatorPub`, `DataBin`, and `BitArray`.
- Parameter sweeps, shots, and precision settings for the reference implementations.
- Interpreting measured counts, expectation values, and metadata from primitive results.

## Exclude or route elsewhere

- Backend classes, provider implementation, and fake backends belong in `../providers/SKILL.md`.
- Abstract circuit construction belongs in `../circuit/SKILL.md`.
- Serialization of circuits belongs in `../serialization/SKILL.md`.
- State/operator mathematics belongs in `../quantum-info/SKILL.md`.
- Output rendering belongs in `../visualization/SKILL.md`.

## Default route

Start here when the user wants to sample from a circuit, estimate an observable, or understand the nested data containers returned by a primitive job. If the problem starts with a backend class rather than a sampler or estimator, route to providers first.

## What to remember

- Sampler results are organized around measured bit arrays; estimator results are organized around expectation values.
- PUBs may be provided directly or via the convenience tuples accepted by `run()`.
- The shape of the result container mirrors the shape of the observable and parameter sweeps.
- Measured circuits are usually required for sampling, while estimators work with unmeasured circuits and observables.
