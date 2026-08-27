# Test Selection

Use this guide when the user asks for a safe local maintenance test lane or when source changes need focused validation.

## Test selection principles

- Prefer small, deterministic, GPU-aware checks.
- Keep the lane as narrow as possible: package import, one subsystem, one example, or one source-build probe.
- Avoid large benchmark suites, long distributed jobs, or large model downloads unless explicitly requested.
- Match the lane to the change surface: compiler, runtime, deployment, debug, or build logic.

## Common lane types

| Change surface | Good lane | Why |
| --- | --- | --- |
| Package metadata / import behavior | Environment probe + minimal import | Fastest way to catch wheel and feature-gate regressions. |
| Dynamo compiler code | Focused compile smoke or small `tests/py/dynamo/...` subset | Verifies the compiler path without a large matrix. |
| Runtime settings / allocator / CUDA graphs | Tiny runtime smoke or benchmark template | Confirms execution semantics and feature gates. |
| Deployment / launcher / artifact saving | Artifact save/load or CLI help check | Verifies file/path semantics without a full serving stack. |
| Source build flags | `source_build_probe.py` plus a tiny build command | Confirms prerequisites before a long build. |

## Reading CI suites

Use the bundled `list_ci_suites.py` helper or inspect `tests/ci/suites.py` when you need the repo's own suite naming. Do not guess suite names from memory if the repository defines them explicitly.

## Example maintainer response

A good answer should say something like:

> For a Dynamo converter change, start with the tiny compile probe, then run the narrow `tests/py/dynamo/models/...` subset that exercises the changed op. Avoid the full GPU matrix unless the compile smoke or regression reproduces a backend problem.
