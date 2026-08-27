---
name: conversion-and-profiling
description: "Convert, benchmark, and profile CVNets models."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Conversion and Profiling

Use this sub-skill when the user wants to convert a CVNets model to CoreML, benchmark throughput, or generate a loss landscape.

This sub-skill owns the export and profiling path around `main_conversion.py`, `main_benchmark.py`, and `main_loss_landscape.py`. It does not own the training loop, dataset design, or the architecture-selection problem except where those choices affect exportability.

## Read these first

- `../../references/api-reference.md` — public conversion and benchmark entry points.
- `../../references/model-overview.md` — whether the chosen family is exportable.
- `../../references/configuration.md` — conversion, benchmark, and loss-landscape keys.
- `references/workflows.md` — command patterns for CoreML export, throughput, and loss landscape.
- `references/troubleshooting.md` — export, optional dependency, and profiling failures.
- `scripts/cvnets_convert.py` — bundled conversion wrapper.
- `scripts/cvnets_benchmark.py` — bundled benchmark wrapper.
- `scripts/cvnets_loss_landscape.py` — bundled loss-landscape wrapper.

## Owns

- PyTorch-to-CoreML conversion and the JIT/JIT-optimized artifacts that go with it.
- Benchmark throughput settings and JIT-vs-plain-model choices.
- Loss-landscape grid settings and the training-engine path used to evaluate them.
- Export-related optional dependency checks and Mac/CoreML caveats.

## Excludes

- Choosing the model family; route to `models-and-architectures`.
- Training, resume, finetuning, and evaluation orchestration; route to `training-and-evaluation`.
- Config/dataset/tokenizer layout questions; route to `data-and-config`.

## Workflow

1. Confirm the model family and the config first; exportability depends on both.
2. Check whether the model exposes an export-friendly path before trying the conversion wrapper.
3. Use `scripts/cvnets_convert.py` for CoreML export, `scripts/cvnets_benchmark.py` for throughput, and `scripts/cvnets_loss_landscape.py` for loss-landscape runs.
4. Treat full CoreML deployment as an optional/macOS-sensitive path unless the user explicitly asked for it.
5. If the problem is actually a model-family or config issue, switch back to the owning sub-skill rather than debugging export in isolation.

## Common signals

- `main_conversion.py` may emit CoreML, traced JIT, and optimized JIT outputs together.
- `main_benchmark.py` can benchmark either the raw PyTorch model or the JIT-optimized path.
- `main_loss_landscape.py` reuses the training engine with a grid over a trained model and validation loader.
- `coremltools` and its support packages are optional; the repo can still run non-export workflows without them.

## When to switch away

- If the export fails because the checkpoint or family is wrong, switch to `models-and-architectures`.
- If the export fails because the config or data layout is wrong, switch to `data-and-config`.
- If the export is only one step in a larger train/eval issue, switch to `training-and-evaluation`.
