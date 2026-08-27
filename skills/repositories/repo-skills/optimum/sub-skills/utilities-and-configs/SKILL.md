---
name: utilities-and-configs
description: "Operate Optimum utility APIs for dummy inputs, normalized configs,
  preprocessing processors, run configs, and save/load support."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Optimum utilities and configs

Use this sub-skill when a task needs Optimum support APIs rather than a backend-specific exporter, FX, or GPTQ workflow: dummy tensors for tracing/export probes, normalized access to heterogeneous Transformers configs, preprocessing task processors, benchmark/run config validation, and shared save/load base classes.

## Operating map

| Need | Use |
| --- | --- |
| Generate local dummy inputs for text, decoder, cache, bbox, vision, audio, labels, or diffusion-style inputs | [references/dummy-inputs.md](references/dummy-inputs.md) |
| Normalize nonstandard model configs and use `NormalizedConfig.with_args` | [references/normalized-configs.md](references/normalized-configs.md) |
| Select task preprocessors, understand dataset caveats, validate run configs, or reason about base save/load classes | [references/preprocessing-and-runs.md](references/preprocessing-and-runs.md) |
| Diagnose optional dependencies, task names, dtype/shape issues, and config local-vs-Hub errors | [references/troubleshooting.md](references/troubleshooting.md) |
| Run a no-download local smoke check for normalized configs, text/vision dummy inputs, labels, and optional `BaseConfig` serialization | [scripts/utils_smoke.py](scripts/utils_smoke.py) |

## Start here

1. Confirm the task is utility/config support. If the user asks for backend exporter registration, CLI routing, or accelerated pipeline backend setup, route to [`../exporters-and-cli/SKILL.md`](../exporters-and-cli/SKILL.md). If they ask for FX graph transformations, route to [`../fx-graph-workflows/SKILL.md`](../fx-graph-workflows/SKILL.md). If they ask for GPTQ quantization workflows, route to [`../gptq-quantization/SKILL.md`](../gptq-quantization/SKILL.md).
2. For exporter or tracing dummy inputs, build or retrieve a normalized config first, then instantiate the narrowest `DummyInputGenerator` subclass that supports the model input name.
3. For unusual config attribute names, use `NormalizedConfig.with_args(...)` rather than monkey-patching the Transformers config.
4. Treat preprocessing processors and benchmark runs as optional-dependency surfaces: they can require `torchvision`, Pillow, `datasets`, model preprocessors, local datasets, or backend-specific subclasses.
5. Prefer local, bounded checks. Do not trigger model downloads, dataset downloads, training, quantization, Hub pushes, or destructive writes unless the user explicitly asks and provides a budget/credentials.

## Fast verification

From this sub-skill directory or with an explicit path to the script:

```bash
python scripts/utils_smoke.py --help
python scripts/utils_smoke.py
python scripts/utils_smoke.py --framework np --skip-base-config
python scripts/utils_smoke.py --check-task-processors
```

The smoke script is intentionally no-download. It uses tiny in-memory config objects and a temporary directory for the optional `BaseConfig` round trip.
