---
name: fastvideo
description: "Guides FastVideo video, image, and audio generation, config-first inference, serving, training, distillation, evaluation, and performance workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# FastVideo

Use this skill when a task involves the `fastvideo` Python package, its
`VideoGenerator` API, registered video/image/audio diffusion models, the
`fastvideo` CLI, attention/quantization optimizations, OpenAI-compatible or
WebSocket serving, preprocessing, training, distillation, LoRA, checkpoint
conversion, or evaluation.

## First route

1. Read [provenance](references/repo-provenance.md) when checking version
   alignment or deciding whether a refresh is needed. The structured
   [routing metadata](references/repo-routing-metadata.json) is consumed by
   managed repo-skill routing and is not a user configuration file.
2. Read [troubleshooting](references/troubleshooting.md) before installing,
   changing backends, or diagnosing a failed run.
3. Choose exactly one focused route:
   - [setup-and-configuration](sub-skills/setup-and-configuration/SKILL.md) for
     installation, platform/backend selection, model registry, presets, and
     configuration structure.
   - [inference](sub-skills/inference/SKILL.md) for Python/CLI generation,
     model inputs, offload, attention, quantization, compile, and output files.
   - [serving](sub-skills/serving/SKILL.md) for HTTP, WebSocket streaming,
     health checks, continuation state, and server configuration.
   - [training-and-data](sub-skills/training-and-data/SKILL.md) for dataset
     layouts, preprocessing, modular training, and legacy recipe boundaries.
   - [distillation-and-adapters](sub-skills/distillation-and-adapters/SKILL.md)
     for DMD/self-forcing/QAD, LoRA, and checkpoint conversion decisions.
   - [evaluation-and-performance](sub-skills/evaluation-and-performance/SKILL.md)
     for metrics, benchmarking, quality checks, and performance interpretation.

For a task spanning routes, read the route that owns the executable step first,
then follow its sibling link. Do not mix the new modular trainer with the legacy
training stack without an explicit reason.

## Public install baseline

FastVideo 0.2.0 supports Python 3.10–3.12 in the documented path. For NVIDIA,
create an isolated environment and choose the torch backend explicitly:

```bash
uv venv --python 3.12 --seed
# Activate the environment created by your shell/platform, then install:
UV_TORCH_BACKEND=cu126 uv pip install fastvideo
```

Use `UV_TORCH_BACKEND=cu130` for a CUDA 13 installation. Apple Silicon uses
MPS and the platform-specific install path; do not install Linux-only CUDA
extensions there. ARM NVIDIA systems may need an editable source install so
the kernel can compile. Read the setup route before selecting an install.

Minimal package and CLI checks:

```bash
python -c "import fastvideo; from fastvideo import VideoGenerator, PipelineConfig, SamplingParam; print(fastvideo.__version__)"
fastvideo --version
fastvideo --help
```

Do not treat package import as proof that a model, GPU kernel, remote checkpoint,
or full training workflow is usable. Check the backend, model support, memory,
weights access, and optional dependency requirements for the selected route.

## Shared operating rules

- Prefer typed `GenerationRequest` plus `VideoGenerator.generate()` for new
  integrations. `generate_video()` remains a deprecated compatibility path.
- The CLI is config-first: use `fastvideo generate --config FILE` and dotted
  `--request.*` or `--generator.*` overrides, not flat ad-hoc flags.
- Keep model initialization settings under `GeneratorConfig`; keep per-request
  sampling and input settings under `GenerationRequest`.
- Set attention backend before constructing the generator and reinstantiate
  after changing it. A backend installed on the machine is not necessarily
  compatible with every model or GPU.
- Use deterministic seeds, fixed shapes, and a discarded warmup when comparing
  performance or eager versus compiled execution.
- Treat remote model/data downloads, credentials, multi-GPU jobs, training,
  distillation, and quality regressions as explicit operations requiring a
  suitable budget and hardware.

## Runtime files

All linked references and helpers are bundled inside this skill. The focused
routes own detailed API/configuration material and safe helpers; this root file
is intentionally a router rather than a copy of the package manual.
