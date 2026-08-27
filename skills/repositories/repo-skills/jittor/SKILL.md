---
name: jittor
description: "Guide Jittor package workflows for tensor programming, training,
  data/model I/O, custom ops, runtime validation, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Jittor repo skill

Use this repo skill when a task involves the Jittor Python package or repository. It is a router, not a full manual.

Before relying on this skill for a checkout or installed package, read [references/repo-provenance.md](references/repo-provenance.md) to compare the source commit, package version, and evidence paths. For setup and the first import check, read [references/installation-and-runtime.md](references/installation-and-runtime.md), then run [`scripts/check_jittor_env.py`](scripts/check_jittor_env.py) against the active Python environment.

## Install baseline

For normal package use, either install the published package or install from a checkout:

```bash
python -m pip install jittor
# or, from a checkout
python -m pip install -e .
```

The public metadata and docs for this repo assume a working C++ compiler and the runtime dependencies listed in the package metadata.

### Minimal import check

```bash
python scripts/check_jittor_env.py
```

That smoke should import `jittor`, run one tiny CPU operation, and report whether CUDA is actually available to Jittor.

## Route map

- Use [sub-skills/runtime-and-installation/SKILL.md](sub-skills/runtime-and-installation/SKILL.md) for install choices, compiler and cache setup, backend flags, lazy execution debugging, and bounded performance or profiling checks.
- Use [sub-skills/core-api-and-autograd/SKILL.md](sub-skills/core-api-and-autograd/SKILL.md) for `Var`, arithmetic, gradients, `Module`, `Function`, synchronization, and save/load basics.
- Use [sub-skills/nn-training-workflows/SKILL.md](sub-skills/nn-training-workflows/SKILL.md) for layers, losses, optimizers, schedulers, train/eval loops, accumulation, and checkpoint handling.
- Use [sub-skills/datasets-models-and-io/SKILL.md](sub-skills/datasets-models-and-io/SKILL.md) for datasets, transforms, model zoo constructors, pretrained weights, and checkpoint interoperability.
- Use [sub-skills/custom-op-console-and-tools/SKILL.md](sub-skills/custom-op-console-and-tools/SKILL.md) for `jt.code`, custom ops, C++ console embedding, and safe utility CLI or conversion workflows.

## Shared references

- [references/api-map.md](references/api-map.md) summarizes the top-level public modules and their owning sub-skill.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json) is the structured router metadata used during managed import.
- [references/troubleshooting.md](references/troubleshooting.md) is the cross-cutting symptom-to-route map for install/import/runtime problems.
- [scripts/jittor_cache_doctor.py](scripts/jittor_cache_doctor.py) inspects the cache layout without deleting anything.
- [scripts/check_jittor_env.py](scripts/check_jittor_env.py) is the baseline environment check.

## Operating rules

1. Prefer the smallest route that matches the task family.
2. Treat CPU importability as the baseline; do not claim CUDA, ROCm, MPI, or other accelerator support unless the matching smoke or native verification has passed.
3. If a task spans multiple route families, start with the most infrastructure-sensitive sub-skill, usually runtime-and-installation.
4. Use bundled skill files only; do not tell future agents to reopen docs, examples, tests, or scripts from the original repository checkout.
5. If the current checkout no longer matches the provenance snapshot, refresh the skill before reusing it.

## Quick routing hints

- Tensor, gradient, or execution semantics: core-api-and-autograd.
- Layers, optimizers, schedulers, or training loops: nn-training-workflows.
- Datasets, transforms, model zoo, or checkpoint I/O: datasets-models-and-io.
- Custom operators, console embedding, or utility CLI flags: custom-op-console-and-tools.
- Install, compiler, cache, profiling, backend flags, or timing: runtime-and-installation.

## Why this skill is organized this way

Jittor has a broad surface area, but most user questions cluster into a few repeated families: runtime setup, core tensor semantics, training, data/model I/O, and advanced extension tooling. The sub-skills keep those families separate so a later agent can answer a natural request without rereading the full repository.
