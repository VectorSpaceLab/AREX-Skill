# vLLM Deployment Configuration Reference

This reference distills operational flags and Python engine arguments for deployment and performance work. Hardware-backed serving, model downloads, GPU profiling, and distributed process launches are user-environment gated; validate them in the target environment before treating results as final.

## Core Entry Points

### Online server

```bash
vllm serve MODEL_ID_OR_PATH \
  --host 0.0.0.0 \
  --port 8000 \
  --tensor-parallel-size 1
```

`vllm serve` accepts engine arguments plus server arguments. A YAML file can provide long-form options, and command-line values override config-file values:

```yaml
model: meta-llama/Llama-3.1-8B-Instruct
host: "0.0.0.0"
port: 8000
uvicorn-log-level: info
tensor-parallel-size: 2
gpu-memory-utilization: 0.90
```

```bash
vllm serve --config serve.yaml
```

### Offline engine constructor

Installed API inspection verified this constructor shape for the runtime package:

```python
from vllm import LLM

llm = LLM(
    model="MODEL_ID_OR_PATH",
    runner="auto",
    tokenizer_mode="auto",
    tensor_parallel_size=1,
    dtype="auto",
    quantization=None,
    gpu_memory_utilization=0.92,
    cpu_offload_gb=0,
    kv_cache_memory_bytes=None,
    enforce_eager=False,
)
```

Use offline inference routing for prompt/request syntax. Use this sub-skill only for engine-level tuning and diagnosis.

## Memory Planning Knobs

### First-line OOM reductions

Prefer changes in this order because they are easy to explain and reverse:

1. Lower `--max-model-len` if the application does not need the model's full context.
2. Lower `--max-num-seqs` to reduce peak concurrent activation and KV pressure.
3. Increase `--tensor-parallel-size` when the model cannot fit on one GPU but fits on one node.
4. Add `--pipeline-parallel-size` when the model cannot fit on one node, or when uneven GPU splits make pipeline parallelism more practical.
5. Use a quantized checkpoint or an online quantization mode supported by the model/backend.
6. Add `--cpu-offload-gb` for weight offload when GPU memory is short and host memory/PCIe bandwidth are acceptable.
7. Use `--kv-cache-memory-bytes` for explicit KV reservation when the default memory fraction produces unsuitable cache capacity.
8. Disable CUDA graph capture with `--enforce-eager` only as a debugging or memory-reduction tradeoff, because it can reduce performance.

Example conservative OOM triage command:

```bash
vllm serve MODEL_ID_OR_PATH \
  --tensor-parallel-size 2 \
  --max-model-len 8192 \
  --max-num-seqs 8 \
  --gpu-memory-utilization 0.88 \
  --dtype bfloat16 \
  --cpu-offload-gb 8
```

For a 70B-class model on two GPUs, treat this as a hypothesis, not a guarantee. Two low-memory GPUs may still be insufficient unless the model uses a supported quantized checkpoint, a shorter context, lower concurrency, or offload that the host RAM and latency budget can tolerate.

### GPU memory fraction vs explicit KV size

- `--gpu-memory-utilization` defaults to `0.92` and is per vLLM instance, not global across all processes on a GPU.
- `--kv-cache-memory-bytes` overrides automatic KV sizing based on `--gpu-memory-utilization`.
- Startup logs should include lines similar to `GPU KV cache size: ... tokens` and `Maximum concurrency for ... tokens per request: ...x`. Treat these as the first sanity check for throughput capacity.
- If multiple vLLM instances share a GPU, lower each instance's `--gpu-memory-utilization` so their combined allocations leave room for model weights, kernels, and other services.

### CPU backend cache

For CPU-only deployments, the CPU KV cache space can be controlled with:

```bash
VLLM_CPU_KVCACHE_SPACE=8 vllm serve MODEL_ID_OR_PATH --device cpu
```

The value is in GiB. CPU execution is useful for smoke tests and small models, not as a proxy for GPU throughput.

## Parallelism Knobs

| Need | Primary setting | Notes |
| --- | --- | --- |
| Model fits one GPU | no distributed flags | Simplest and usually best latency. |
| Model too large for one GPU, fits one node | `--tensor-parallel-size N` | Use GPUs with fast interconnect when possible. |
| Model too large for one node | `--tensor-parallel-size GPUS_PER_NODE --pipeline-parallel-size NODES` | Use Ray or multiprocessing multi-node launch. |
| Uneven layer/GPU split or weak interconnect | `--pipeline-parallel-size` | Pipeline parallelism can be preferable on GPUs without NVLink. |
| Independent replicas for throughput | `--data-parallel-size N` | Each DP rank has independent KV cache; `--max-num-seqs` applies per rank. |
| MoE expert sharding | `--enable-expert-parallel` | EP size is `TP × DP`; requires MoE model and backend support. |
| Long-context decode KV duplication | `--decode-context-parallel-size N` | Use after increasing TP; valid range depends on KV heads and TP. |

Python equivalents use snake_case constructor kwargs, for example `tensor_parallel_size=2`, `pipeline_parallel_size=2`, and `distributed_executor_backend="ray"`.

## Quantization and Dtype

### Selection checklist

- Prefer a checkpoint that already declares a supported quantization method when possible.
- Use `--dtype auto` unless a model/backend compatibility issue requires explicit `float16` or `bfloat16`.
- Use `--quantization METHOD` for checkpoint or supported online modes; inspect server startup logs for resolved quantization, dtype, and kernel backend.
- If startup fails with an unsupported quantization error, check whether the active platform supports that method. CUDA, ROCm, CPU, XPU, and other plugins do not expose identical quantization support.

### Online quantization shorthands

The current config accepts these online shorthand names when the model/backend supports them:

- `fp8_per_tensor`
- `fp8_per_block`
- `fp8_per_channel`
- `mxfp8`
- `int8_per_channel_weight_only`
- `online` with a `--quantization-config` JSON object

Example:

```bash
vllm serve MODEL_ID_OR_PATH \
  --quantization fp8_per_tensor \
  --dtype auto
```

When `--quantization-config` is provided, it is valid with `--quantization online` or one of the online shorthand names. Do not combine arbitrary checkpoint quantization names with an online config unless the CLI accepts it.

## KV Cache, Prefix Cache, and Offload

### Prefix caching

Automatic prefix caching reuses KV blocks for repeated prefixes. It improves prefill-heavy workloads with shared documents, system prompts, or multi-turn conversation history. It does not speed up decode-heavy workloads with long generated answers, and it does not help when prompts do not share prefixes.

Relevant knobs:

```bash
vllm serve MODEL_ID_OR_PATH \
  --enable-prefix-caching \
  --prefix-caching-hash-algo sha256
```

The cache config defaults to prefix caching enabled. Hash algorithm options include secure `sha256` variants and faster non-cryptographic `xxhash` variants when the optional dependency is installed. Consider collision/security risk before using non-cryptographic hashes in multi-tenant deployments.

### KV cache dtype

`--kv-cache-dtype auto` uses the model dtype by default. Current cache dtype options include `float16`, `bfloat16`, fp8 variants, int8/per-token-head variants, and hardware/plugin-specific formats. Use quantized KV cache only when the hardware/backend and model support it, and verify output quality and memory savings with a representative workload.

### Native KV offloading buffer

The cache config includes `kv_offloading_size` in GiB and `kv_offloading_backend` (`native` or `lmcache`). Enable only when the target vLLM version exposes the matching CLI flags; verify with `vllm serve --help` because argument spelling may vary across releases.

### KV transfer offloading connector

For connector-based offload to CPU memory:

```bash
vllm serve MODEL_ID_OR_PATH \
  --kv-transfer-config '{
    "kv_connector": "OffloadingConnector",
    "kv_role": "kv_both",
    "kv_connector_extra_config": {
      "block_size": 64,
      "cpu_bytes_to_use": 1000000000
    }
  }'
```

Multi-tier CPU plus filesystem offload uses `TieringOffloadingSpec` and a `secondary_tiers` list. Requirements and checks:

- `cpu_bytes_to_use` is total host memory for the CPU tier, not per worker.
- Offloaded `block_size` must be a multiple of the GPU block size.
- Filesystem tiers need fast local or shared storage and tuned read/write thread counts.
- Cross-process sharing through a common filesystem root requires fixed `PYTHONHASHSEED` across instances.
- Secondary tiers stage through the CPU primary tier; they do not directly read/write GPU memory.

## Profiling Configuration

Offline code can pass a `profiler_config` dict and call `start_profile()` / `stop_profile()`:

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
        "max_iterations": 5,
    },
)
llm.start_profile()
llm.generate(["Hello"], SamplingParams(max_tokens=16))
llm.stop_profile()
```

The torch profiler directory must be absolute at runtime. Do not publish machine-specific profiler paths in reusable instructions; use placeholders such as `/absolute/path/for/traces`.

## Validation Checklist

After changing deployment flags, capture these facts before declaring success:

- `vllm --help` and `vllm serve --help` show the flags being used.
- Startup logs report resolved model dtype, quantization, parallel sizes, executor backend, and KV cache capacity.
- `/metrics` responds when using the OpenAI-compatible server.
- A small smoke request succeeds before large benchmarks.
- Benchmark prompt/output lengths, concurrency, endpoint type, and sampling settings match the target workload.
