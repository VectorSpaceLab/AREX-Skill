# vLLM Performance and Observability Reference

Use this guide to measure serving health, debug performance, and collect evidence before changing deployment topology. Prefer metrics and controlled benchmarks over isolated anecdotes.

## Production Metrics

The OpenAI-compatible server exposes Prometheus metrics at `/metrics` by default.

```bash
vllm serve MODEL_ID_OR_PATH --host 0.0.0.0 --port 8000
curl http://127.0.0.1:8000/metrics | head
```

Expected response shape includes Prometheus `# HELP` and `# TYPE` lines and `vllm:` metric names such as token iteration, request, queue, cache, and timing series. If the endpoint is missing, confirm the request is sent to the API server process and not to a reverse proxy path that strips `/metrics`.

### Useful metric families and signals

| Signal | What to inspect |
| --- | --- |
| Request rate and failures | Running/waiting queues, request success/error counters, HTTP status metrics. |
| TTFT | Prefill pressure, long prompts, prefix-cache effectiveness, disaggregated prefill impact. |
| TPOT / ITL | Decode throughput, KV cache pressure, communication overhead, structured-output or adapter overhead. |
| KV cache usage | `vllm:kv_cache_usage_perc` and related cache metrics when enabled. |
| Prefix cache | Cache hit rate and queue state; low hits can mean poor prompt sharing or load-balancer routing. |
| MFU | Enable with `--enable-mfu-metrics` when model FLOPs utilization matters. |
| Hidden/deprecated metrics | `--show-hidden-metrics-for-version=X.Y` is a temporary migration aid, not a permanent dependency. |

KV cache residency metrics are sampled and require stats logging to remain enabled:

```bash
vllm serve MODEL_ID_OR_PATH \
  --kv-cache-metrics \
  --kv-cache-metrics-sample 0.01
```

CUDA graph metrics and MFU metrics can add overhead or cardinality. Enable them for diagnosis windows, then turn them off when no longer needed.

## OpenTelemetry Tracing

OpenTelemetry trace export is configured by endpoint:

```bash
export OTEL_SERVICE_NAME=vllm
export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://localhost:4317
vllm serve MODEL_ID_OR_PATH \
  --otlp-traces-endpoint "$OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"
```

Detailed traces require an OTLP endpoint and can affect performance:

```bash
vllm serve MODEL_ID_OR_PATH \
  --otlp-traces-endpoint "$OTEL_EXPORTER_OTLP_TRACES_ENDPOINT" \
  --collect-detailed-traces model,worker
```

Use detailed traces for short windows around a reproducible issue. Do not keep them enabled during normal throughput measurements unless the overhead is part of the measurement.

## Prometheus and Grafana Checklist

1. Start the vLLM server and verify `curl /metrics` locally.
2. Configure Prometheus to scrape the vLLM host and port.
3. Verify Prometheus targets are `UP`.
4. Add Prometheus as a Grafana data source.
5. Import or build dashboards for request rates, TTFT, ITL/TPOT, queue length, GPU utilization, and KV cache usage.
6. Add labels that distinguish model name, deployment replica, DP rank, and environment.

If Grafana has no data, debug in this order: vLLM `/metrics`, network reachability, Prometheus target status, Prometheus query result, Grafana data source, dashboard variable filters.

## Profiling Workflows

### Offline torch profiler

Use offline profiling for small, controlled reproductions where request traffic is not required:

```python
from vllm import LLM, SamplingParams

llm = LLM(
    model="MODEL_ID_OR_PATH",
    profiler_config={
        "profiler": "torch",
        "torch_profiler_dir": "/absolute/path/for/traces",
        "torch_profiler_with_stack": True,
        "torch_profiler_record_shapes": False,
        "torch_profiler_with_memory": False,
        "delay_iterations": 1,
        "max_iterations": 5,
    },
)

llm.start_profile()
llm.generate(["Write a short haiku about GPUs."], SamplingParams(max_tokens=32))
llm.stop_profile()
```

Keep trace directories outside reusable instructions and collect only the minimum number of iterations needed. Stack, shape, memory, and FLOP options increase overhead and trace size.

### Server profiling pattern

For online deployments, use a short reproducible load window:

1. Start the server with metrics and any needed profiler flags.
2. Warm up with a few representative requests.
3. Start profiling or detailed tracing.
4. Run a bounded benchmark with fixed prompt/output lengths and concurrency.
5. Stop profiling.
6. Compare profiler time with metrics for the same window.

### Debug logging

Short-lived environment variables:

```bash
export VLLM_LOGGING_LEVEL=DEBUG
export VLLM_LOG_STATS_INTERVAL=1.
export NCCL_DEBUG=TRACE
```

Use `CUDA_LAUNCH_BLOCKING=1` only to identify kernel failures; it changes timing. Use `VLLM_TRACE_FUNCTION=1` only for severe hangs or crashes because it can slow generation dramatically. Start a fresh shell after debugging so diagnostic variables do not poison benchmarks.

## Benchmarking

### Online benchmark

```bash
vllm serve MODEL_ID_OR_PATH --port 8000

vllm bench serve \
  --backend vllm \
  --model MODEL_ID_OR_PATH \
  --endpoint /v1/completions \
  --dataset-name random \
  --num-prompts 100 \
  --random-input-len 1024 \
  --random-output-len 128 \
  --max-concurrency 16 \
  --save-result
```

Key outputs:

- Successful requests
- Request throughput
- Output token throughput
- Total token throughput
- Mean/median/P99 TTFT
- Mean/median/P99 TPOT
- Mean/median/P99 ITL

### Offline benchmark

Use offline benchmarks when testing engine-only throughput without HTTP overhead. Ensure the same model, dtype, quantization, max context, sampling, and batch shape are used when comparing against online results.

### Interpreting results

| Observation | Likely direction |
| --- | --- |
| High TTFT, normal TPOT | Prefill-bound; check prompt length, prefix cache, chunking/disaggregated prefill, TP/PP. |
| Normal TTFT, high TPOT/ITL | Decode-bound; check KV cache pressure, DCP, structured outputs, adapters, GPU utilization. |
| Low request throughput but high token throughput | Requests are long or concurrency is low; inspect workload shape. |
| High queue length and low GPU utilization | Frontend, tokenizer, networking, load balancing, or scheduling bottleneck. |
| High GPU utilization and high ITL | Model/kernel/communication bound; compare dtype, quantization, TP, EP, DCP. |
| Good synthetic benchmark, bad production | Dataset mismatch, prompt/output distribution, client concurrency, network, or load balancer issue. |

Do not compare benchmark runs unless these are controlled: model revision, dtype, quantization, TP/PP/DP/EP/DCP, max model length, max num seqs, prompt/output distributions, sampling parameters, concurrency, hardware, driver, and server commit/version.

## Structured Outputs, LoRA, and Multimodal Performance Triage

This sub-skill does not own request syntax or feature-specific configuration, but it owns the performance triage plan:

1. Reproduce baseline without the feature using the same prompts and output lengths.
2. Enable one feature at a time: structured outputs, LoRA/adapters, multimodal inputs, speculative decoding, or tool parsing.
3. Compare TTFT vs TPOT/ITL to identify prefill, decode, parser, or adapter overhead.
4. Inspect queue length, KV cache usage, CPU utilization, and GPU utilization.
5. Profile a bounded window if metrics do not explain the regression.
6. Route feature-specific fixes to the owning sub-skill and keep deployment-level changes here.

## Environment Collection

Use the bundled script for safe support summaries:

```bash
python scripts/collect_env_summary.py --json
python scripts/collect_env_summary.py --check-vllm-help
```

The script reports Python, platform, package versions, selected environment variables, optional GPU command summaries, and whether `vllm --help` / `vllm serve --help` execute. It does not start a model server or download models.
