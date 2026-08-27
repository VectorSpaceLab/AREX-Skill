---
name: development-and-testing
description: "Guide TorchRL code changes, tests, docs, CI labels, deprecations,
  and contributor policy for maintainer-safe edits."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# TorchRL Development and Testing

Use this sub-skill when the user wants to modify TorchRL code, add or change a public API, write tests, update docs or tutorials, add a benchmark, decide CI labels, handle CUDA/optional backend test markers, maintain Hydra config parity, or prepare a maintainer-quality PR.

Do not use this sub-skill as the primary source for runtime API recipes. Route API usage and debugging to the workflow sub-skills first, then return here for edit policy, testing, documentation, and CI decisions.

## Immediate routing

- Environment, transform, spec, rollout, or `step_mdp` implementation details: route to the envs/transforms workflow owner, then apply this sub-skill for tests/docs.
- Collector, replay buffer, storage, sampler, evaluator, distributed collection, or service-backed replay changes: route to the collector/replay workflow owner, then apply this sub-skill for backend and CI scope.
- Actor, critic, distribution, recurrent module, policy wrapper, or model component changes: route to the modules/policies workflow owner, then apply this sub-skill for TensorDict keys and coverage.
- Loss, value estimator, target updater, trainer, algorithm, SOTA script, or Hydra training config changes: route to the objectives/training workflow owner, then apply this sub-skill for parity and SOTA/docs checks.
- LLM, VLA, service registry, render/checkpoint integration, or optional serving backend changes: route to the LLM/VLA/services workflow owner, then apply this sub-skill for optional-dependency labels and isolation.

## Required references

Read these in order for development tasks:

1. [Contributor guidance](references/contributor-guidance.md) for code style, imports, TensorDict-first design, logging, timing, type hints, and compile-friendly patterns.
2. [Test and CI selection](references/test-and-ci-selection.md) for focused pytest selection, GPU marker policy, optional dependency labels, SOTA smoke expectations, and helper scripts.
3. [Config, docs, and deprecations](references/config-docs-and-deprecations.md) for Hydra config/class parity, docs reference entries, tutorials, benchmarks, and two-release deprecation policy.
4. [Troubleshooting](references/troubleshooting.md) when a change passes locally but fails or disappears in CI.

## Safe helper scripts

- `scripts/list_relevant_tests.py`: suggest likely test files and CI focus areas from touched paths.
- `scripts/check_gpu_marker_policy.py`: statically flag CUDA-only skip conditions that are missing `pytest.mark.gpu`.

Both scripts are standalone and only inspect files or paths explicitly passed to them.

## Minimum maintainer checklist

Before claiming a TorchRL code change is ready:

1. Confirm all new `.py` files start with `from __future__ import annotations`.
2. Keep imports module-top; no wildcard imports; use the optional-dependency exception only with a module-top `_has_<name>` probe.
3. Use `torchrl.implement_for` for version dispatch rather than hand-rolled version checks.
4. Use TorchRL logging and `torchrl.timeit`; do not add `print()` to library code or `time.time()` timing blocks.
5. Preserve TensorDict-first public APIs and use accurate type hints, `NestedKey` for TensorDict keys, and `Literal[...]` for fixed string modes.
6. Add or extend focused tests in existing test files when possible; include nested-key tests when accepting `NestedKey`.
7. Add `pytest.mark.gpu` to CUDA-only tests that also use CUDA/Triton skip conditions.
8. Update reference docs for every new public class/function; add runnable examples in public docstrings.
9. For hot paths, check compile/cudagraph friendliness and add or update a benchmark when behavior is performance-relevant.
10. If a class has a Hydra `*Config` companion, keep constructor kwargs, config fields, factory popping/forwarding, defaults, and doc cross-references in parity.
