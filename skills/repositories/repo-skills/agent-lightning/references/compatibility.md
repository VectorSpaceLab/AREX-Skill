# Compatibility and installation notes

## Purpose

Use this reference when you need a public install command, a backend/dependency overview, or a quick reminder of which Agent Lightning workflows are CPU-safe and which are optional.

## Verified package baseline

- Distribution: `agentlightning`
- Version: `0.3.1`
- Python requirement: `>=3.10`
- Console script: `agl`

## Recommended install paths

### General use

```bash
python -m pip install --upgrade agentlightning
```

### Source checkout development

```bash
git clone https://github.com/microsoft/agent-lightning
cd agent-lightning
uv sync --group dev
```

For local package inspection or development, editable installation from a checkout is also valid. Use the repository's documented `uv` groups when optional capabilities are needed.

## Dependency groups and extras

### Common extras

- `apo` — prompt-optimization workflows; requires `poml` and an OpenAI-compatible backend for full use.
- `verl` — VERL training workflows; depends on heavier torch/vLLM stacks and is CUDA-oriented in practice.
- `mongo` — persistent store backend.
- `weave` — experimental tracing integration.

### Selected dependency groups

- `dev` — tests, formatting, docs, and local developer tooling.
- `torch-stable` / `torch-legacy` — general torch stacks used by training-heavy examples.
- `torch-gpu-stable` / `torch-gpu-legacy` — CUDA-oriented variants.
- `trl` — Unsloth/TRL example stack.
- `agents`, `langchain`, `rag`, `tinker`, `image`, `sql` — optional example families.

## Optional backends and services

| Backend/service | Typical workflows | Status in this skill |
| --- | --- | --- |
| CPU / any | package import, authoring, tracing, in-memory store, CLI help | verified |
| CUDA / GPU | VERL, vLLM serving, Unsloth, ChartQA, Calc-X, Spider, RAG training | documented but not required |
| MongoDB | persistent LightningStore backend | documented but not required |
| OpenAI-compatible API | APO and hosted-debug examples | documented but not required |
| Azure / Anthropic / Tinker / W&B | cloud or hosted example workflows | documented but not required |
| Docker / Ray / SWE-bench | selected examples and maintainer workflows | documented but not required |
| Node / npm | dashboard development/build | documented but not required |

## Verification facts worth remembering

- `agentlightning` imports cleanly after installing the base package and the needed runtime-compatible dependencies.
- `agl --help`, `agl store --help`, and `agl prometheus --help` are the most useful quick checks for CLI availability.
- `InMemoryLightningStore` is the safe default for CPU-only smoke tests.
- `OtelTracer` plus `LitAgentRunner.step` is enough to validate a minimal rollout path without external services.

## When to stop and gather more resources

Stop and ask for the missing resource if a task needs any of the following and they are not available:

- a real OpenAI-compatible endpoint or API key,
- CUDA-capable hardware or the matching PyTorch/vLLM stack,
- a MongoDB replica set,
- a hosted service such as Azure, Anthropic, Tinker, or W&B,
- a large dataset or benchmark download,
- Docker or Node/npm for the dashboard or containerized examples.
