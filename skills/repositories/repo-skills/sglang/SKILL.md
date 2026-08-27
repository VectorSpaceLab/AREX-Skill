---
name: sglang
description: "Use SGLang for high-throughput LLM and VLM serving,
  OpenAI-compatible APIs, frontend language programs, runtime/server arguments,
  benchmarking, profiling, model/kernel extension, and SGLang repository
  development."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SGLang

Use this skill when the task names SGLang, `sglang`, `sglang serve`, SRT, OpenAI-compatible serving, `ServerArgs`, radix cache, tensor/expert parallel serving, speculative decoding, SGLang frontend programs, benchmarking, profiling, custom model support, CUDA/JIT kernels, or development inside the SGLang repository.

## Route By Task

- **Serving runtime**: use `sub-skills/serving-runtime/SKILL.md` for server launch, CLI flags, `ServerArgs`, tokenizer/engine settings, OpenAI-compatible endpoints, cache/scheduling, parallelism, disaggregation, and runtime troubleshooting.
- **Frontend programming**: use `sub-skills/frontend-programming/SKILL.md` for `@sgl.function`, `gen`, `select`, chat roles, backend/runtime endpoints, structured generation, multimodal inputs, and provider-backed frontend execution.
- **Benchmarking and profiling**: use `sub-skills/benchmarking-profiling/SKILL.md` for `bench_serving`, `bench_one_batch`, `auto_benchmark`, profiler scripts, latency/throughput metrics, dataset choices, and reproducible performance triage.
- **Models and kernels**: use `sub-skills/model-kernel-extension/SKILL.md` for adding model configs, extending serving backends, custom kernels, JIT kernels, CUDA attention work, quantization-related kernels, and cookbook/model support workflows.
- **Repository development**: use `sub-skills/repo-development/SKILL.md` for source checkout work, test selection, CI conventions, docs/cookbook changes, dependency caveats, and existing `.claude/skills` guidance.

## Environment Notes

SGLang is a heavyweight serving stack. Full runtime installs can require pinned `torch`, CUDA/GPU packages, `flashinfer`, kernels, and other large wheels. Start with source/config inspection and help-only checks when a full serving environment is not already available. Do not promise that CPU-only or partial installs can run the production server.

## References

- `references/workflow-map.md` maps common serving, frontend, benchmark, model, and repository tasks to sub-skills.
- `references/troubleshooting.md` covers dependency, CUDA, server, OpenAI API, frontend, benchmark, and repo-development failure modes.
- `references/repo-provenance.md` records the source revision and extraction evidence.
- `scripts/sglang_source_smoke.py` performs source-tree checks without importing the full heavyweight runtime.
