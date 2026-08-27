---
name: deployment-performance
description: "Deployment topology, parallelism, memory planning, quantization,
  KV cache/offloading, disaggregated serving, distributed execution,
  observability, profiling, environment collection, backend/hardware selection,
  and performance troubleshooting for vLLM."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Deployment Performance

Use this sub-skill when a task asks how to deploy, scale, tune, observe, or troubleshoot vLLM performance. It owns operational configuration and diagnosis, not request payload syntax.

## Route Here For

- Choosing `vllm serve` engine flags for GPU memory, context length, batch size, tensor/data/pipeline/expert/context parallelism, Ray, multiprocessing, or torchrun-style external launchers.
- Planning quantization, dtype, CPU weight offload, KV cache sizing, prefix caching, KV offloading, or disaggregated prefill/decode topologies.
- Setting up production metrics, OpenTelemetry tracing, Prometheus/Grafana scraping, profiler captures, benchmark interpretation, or environment summaries.
- Debugging OOM, unsupported dtype/quantization, CUDA/ROCm/CPU mismatch, NCCL/GLOO/Ray/network failures, bad parallel sizes, missing `/metrics`, or misleading throughput results.

## Start With These References

- [Configuration](references/configuration.md): engine/server flags, memory controls, quantization, KV cache, prefix cache, and profiling knobs.
- [Deployment](references/deployment.md): single-node, multi-node, Ray, multiprocessing, data/expert/context parallel, disaggregated prefill, and hardware/backend selection.
- [Performance and Observability](references/performance-and-observability.md): metrics, OpenTelemetry, profiling, benchmarks, and runbook signals.
- [Troubleshooting](references/troubleshooting.md): symptom-to-action checks for memory, distributed launch, hardware, metrics, and benchmark issues.

## Bundled Tools

- `scripts/collect_env_summary.py`: safe environment and package summary for support tickets; does not download models or start servers.
- `scripts/memory_command_planner.py`: prints a conservative `vllm serve` command skeleton and checklist from model length, GPU count, TP size, memory utilization, offload, and KV-cache inputs.

## Cross-Skill Routing

- For offline `LLM.generate` code and sampling/request examples, route to the offline-inference sub-skill.
- For OpenAI-compatible API request bodies, chat/completions syntax, or client integration, route to the openai-serving sub-skill.
- For structured outputs, tool calling, parser behavior, or guided decoding interactions, route to structured-tool-reasoning and cross-link back here only for throughput/profiling impact.
- For LoRA, multimodal, pooling, or adapter-specific memory details, route to modalities-adapters-pooling and cross-link back here for GPU/KV/cache capacity planning.
