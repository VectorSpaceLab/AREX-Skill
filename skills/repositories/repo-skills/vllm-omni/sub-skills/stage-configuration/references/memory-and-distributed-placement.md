# Memory and distributed placement

Use this reference to choose stage placement, memory budgets, connector type, launch shape, and diffusion/distributed flags without loading a model.

## Mental model

vLLM-Omni separates these layers:

```text
Model structure       -> what components exist
PipelineConfig        -> fixed logical stages and stage relationships
Stage runtime policy  -> AR/generation/diffusion scheduling and parallelism
DeployConfig          -> devices, replicas, memory, connectors, and defaults
CLI/runtime overrides -> final operator choices at launch time
```

A stage is the unit you resource independently. It may be an autoregressive LLM stage, a generation/vocoder stage, or a diffusion stage. A stage is not always a separate process, but stage-split serving uses separate head/headless processes.

## Quick planning workflow

1. Identify stage count and rough roles: for example `thinker,talker,code2wav` or `ar,dit,vae`.
2. Decide whether the pipeline streams between stages (`async_chunk: true`) or runs end-to-end (`async_chunk: false`). Streaming benefits from placing concurrently active stages on distinct GPUs when possible.
3. Assign each stage a logical device string. Use `"0,1"` only when that stage's parallel world needs multiple GPUs.
4. Budget `gpu_memory_utilization` per stage and per GPU. If multiple resident stages share one GPU, leave combined headroom.
5. Set `max_num_seqs`, `max_num_batched_tokens`, and `max_model_len` to control concurrency and KV/cache pressure.
6. For multi-node or cross-host placement, replace same-host shared memory connectors with a cross-host connector and confirm services/ports.
7. Validate YAML with `scripts/validate_deploy_yaml.py`; estimate rows with `scripts/plan_stage_memory.py`; run live serving only after model weights, GPU capacity, and ports are approved.

## Non-model-loading planner

The bundled planner prints stage rows from declared GPU count/memory and stage labels:

```bash
python sub-skills/stage-configuration/scripts/plan_stage_memory.py \
  --num-gpus 2 --gpu-mem-gib 80 --stages thinker,talker,code2wav \
  --headroom-gib 4 --streaming
```

It is intentionally conservative and does not inspect model weights. Treat its output as a starting point for an overlay, not as a guarantee that the model will fit.

You can override relative stage weights:

```bash
python sub-skills/stage-configuration/scripts/plan_stage_memory.py \
  --num-gpus 4 --gpu-mem-gib 80,80,80,80 \
  --stages thinker:30,talker:4,code2wav:1 --headroom-gib 6 --streaming
```

## Memory controls

### `gpu_memory_utilization`

The requested memory for each stage is approximately:

```text
requested_memory = total_gpu_memory * gpu_memory_utilization
```

The runtime checks available/free memory against the requested budget at stage initialization. Leave space for CUDA/PyTorch overhead, connector buffers, non-torch allocations, CUDA graphs, and other processes. Values near `1.0` are risky; `0.90-0.95` is usually an upper bound, not a default target.

When several stages are resident on one GPU, reason about the combined budget. A conservative rule is:

```text
sum(stage gpu_memory_utilization on GPU X) <= (total_gib - headroom_gib) / total_gib
```

This is conservative because some stages may not peak simultaneously, but it prevents common startup failures.

### `max_num_seqs`

`max_num_seqs` controls stage-local concurrency. It affects scheduler wave capacity, KV cache demand, and batching. Lower it when:

- initialization succeeds but inference OOMs;
- requests are long or media-heavy;
- stages share a GPU;
- diffusion/request batching is not validated for the selected model.

Raise it only after verifying memory headroom and output latency.

### `max_num_batched_tokens`

This controls prefill/token batch budget for token-based stages. Lower it for OOM during prompt prefill, long context, or multimodal pre-processing bursts. Raising it improves throughput only when memory and request shapes permit.

### `max_model_len`

Large `max_model_len` increases KV/cache memory. If a global CLI `--max-model-len` is passed, it applies to every stage unless a per-stage override wins. Prefer setting unusually large context only for stages that need it.

### `dtype` and `quantization`

Top-level `dtype` and `quantization` are pipeline-wide. Some model components cannot share the same quantization assumptions, so per-stage `engine_extras` or model-specific deploy defaults may clear or override quantization metadata for audio/vocoder/diffusion stages. Do not infer that a Thinker/LLM quantization path is valid for Talker, Code2Wav, VAE, or DiT components.

## Device placement patterns

### Single GPU

Use only if the model and all active stages fit comfortably. Example:

```yaml
async_chunk: false
stages:
  - stage_id: 0
    devices: "0"
    gpu_memory_utilization: 0.80
    max_num_seqs: 1
  - stage_id: 1
    devices: "0"
    gpu_memory_utilization: 0.10
    max_num_seqs: 1
```

For streaming pipelines, single-GPU placement may work but gives less overlap and increases shared memory pressure.

### Two GPUs for three-stage audio/chat

Common starting point:

```yaml
async_chunk: true
stages:
  - stage_id: 0
    devices: "0"
    gpu_memory_utilization: 0.85
    max_num_seqs: 16
  - stage_id: 1
    devices: "1"
    gpu_memory_utilization: 0.55
    max_num_seqs: 16
    input_connectors: {from_stage_0: shm}
  - stage_id: 2
    devices: "1"
    gpu_memory_utilization: 0.15
    max_num_seqs: 16
    input_connectors: {from_stage_1: shm}
```

Reasoning: a heavy AR stage gets its own GPU; lighter Talker/vocoder or decoder stages share another GPU. If stage 1 and stage 2 peak together, reduce both memory/utilization or move one to a third GPU.

### Multi-GPU stage with TP

If one stage needs tensor parallelism:

```yaml
stages:
  - stage_id: 0
    devices: "0,1"
    tensor_parallel_size: 2
    gpu_memory_utilization: 0.70
```

The logical device list must contain enough entries for the effective world size. For a stage, effective device demand can include:

```text
tensor_parallel_size * data_parallel_size * pipeline_parallel_size * num_replicas
```

Diffusion stages can add sequence/CFG/VAE/HSDP dimensions; see below.

## DP, PP, TP, replicas, and strategies

- `tensor_parallel_size` is stage-local in `StageDeployConfig`; it splits one stage across devices.
- `data_parallel_size` and `pipeline_parallel_size` exist as pipeline-wide top-level deploy fields; strategy or per-stage overrides may still affect effective stage fields.
- `num_replicas` is stage-local replica fan-out coordinated by the Omni stage pool, not the same as vLLM data-parallel CLI flags.
- In `--omni` serving, do not use upstream vLLM data-parallel server flags for Omni parallelism. Configure per-stage YAML and `--omni-dp-size-local` for process-local head/headless replicas.
- Composable parallel strategy files, when used, are applied after deploy YAML and before CLI overrides. CLI still wins and can trigger conflict warnings if it overrides a strategy-derived axis.

## Diffusion parallel fields

The diffusion parallel constructor verified during inspection exposes these defaults:

```text
DiffusionParallelConfig(
  pipeline_parallel_size=1,
  data_parallel_size=1,
  tensor_parallel_size=1,
  enable_expert_parallel=False,
  sequence_parallel_size=None,
  ulysses_degree=1,
  ring_degree=1,
  allgather_degree=1,
  ulysses_mode='strict',
  cfg_parallel_size=1,
  vae_patch_parallel_size=1,
  text_encoder_tp_size=1,
  vae_parallel_mode='tile',
  use_hsdp=False,
  mask_sp_padding=False,
  hsdp_shard_size=-1,
  hsdp_replicate_size=1,
)
```

Important constraints and uses:

| Field | Use | Constraints and cautions |
| --- | --- | --- |
| `ulysses_degree` | Sequence parallel all-to-all for long diffusion/video sequences. | `ulysses_mode` is `strict` or `advanced_uaa`; strict mode requires compatible sequence/head divisibility. |
| `ring_degree` | Ring attention sequence parallelism. | Sequence parallel size is usually `ulysses_degree * ring_degree`. |
| `allgather_degree` | Alternative allgather sequence-parallel path. | Mutually exclusive with `ulysses_degree > 1` or `ring_degree > 1`. |
| `cfg_parallel_size` | Classifier-free-guidance branch parallelism. | Commonly `2`; only use larger values for models explicitly designed for multi-branch CFG. |
| `vae_patch_parallel_size` | VAE tile/patch decode parallelism. | Should not exceed the DiT process group size; unsupported models may fall back to sequential/tile decode. |
| `vae_parallel_mode` | VAE work splitting mode: `tile`, `spatial_shard_height`, or `spatial_shard_width`. | Spatial-shard modes require model/runtime support; otherwise use `tile`. |
| `text_encoder_tp_size` | Shards a diffusion pipeline's text encoder. | Useful when the text encoder is a memory bottleneck; verify model support. |
| `enable_expert_parallel` | Expert/MoE parallel execution. | Expert parallel size must be consistent with TP/DP-derived world dimensions for the model. |
| `use_hsdp` | Hybrid sharded data parallel for diffusion weights. | Cannot be used with TP or DP in the verified config path. If auto `hsdp_shard_size=-1`, other parallelism must define a world size. |
| `hsdp_shard_size` / `hsdp_replicate_size` | HSDP shard/replica dimensions. | Product must equal the effective world size when other parallelism exists. |

When any diffusion degree changes, re-check the device count and memory. Parallelism reduces some per-GPU memory but may add communication buffers and connector pressure.

## Diffusion offload and memory-efficiency fields

| Field | Use | Caution |
| --- | --- | --- |
| `enable_cpu_offload` | Model/component offload to CPU between phases. | Saves GPU memory but increases transfer latency. |
| `enable_layerwise_offload` | Layer-level offload. | Mutually conflicts with model-level offload in practice; if both are set, layerwise behavior takes priority. |
| `enable_distributed_layerwise_offload` | Distributed layerwise offload across ranks. | Requires a compatible distributed diffusion topology and enough host memory/bandwidth. |
| `dlo_use_allgather` | DLO gather behavior; default is true in the inspected config projection. | Allgather can improve availability of weights but changes per-rank host/GPU memory tradeoffs. |
| `dlo_resident_layers` | Keep N layers resident on device. | Higher values reduce transfer churn but increase GPU memory. |
| `vae_use_slicing` / `vae_use_tiling` | VAE memory reduction. | May reduce peak memory but add decode latency. |
| `enable_multithread_weight_load` / `num_weight_load_threads` | Load weights with multiple threads. | Startup-only optimization; not a memory fix by itself. |

Use offload when a model barely exceeds memory and lower concurrency is not enough. Prefer reducing `max_num_seqs`, `max_num_batched_tokens`, output resolution, or VAE tiling before assuming offload will be fast enough for interactive serving.

## Diffusion attention and execution fields

| Field | Use |
| --- | --- |
| `diffusion_attention_backend` | Select a diffusion attention backend by name when the model/runtime supports it. |
| `diffusion_attention_config` | Structured default/per-role attention backend configuration. Use when different model roles need different attention choices. |
| `diffusion_quantization_config` | Diffusion-specific quantization config separate from pipeline-wide `quantization`. |
| `diffusion_compile_granularity` / `diffusion_compile_dynamic` | Controls diffusion compilation behavior. Compilation can save latency but can increase warmup and graph compatibility risk. |
| `fa_deterministic` | Deterministic FlashAttention behavior when supported. |
| `step_execution` | Diffusion step-batched execution mode. Requires model support and attention/backend compatibility. |
| `cache_backend`, `cache_config`, `enable_cache_dit_summary` | Cache-DiT or related diffusion cache controls. Requires model support and quality/performance validation. |

For mixed causal/full attention diffusion workloads, a conservative fallback is a standard PyTorch SDPA-style backend if the faster backend rejects the attention pattern. Always describe attention backend choices as model-specific.

## Stage-based head/headless deployment

Head/headless mode splits stage processes while one head owns the server and master registry.

Head process:

```bash
CUDA_VISIBLE_DEVICES=0 vllm serve MODEL --omni \
  --port 8091 \
  --stage-id 0 \
  --omni-master-address 10.0.0.10 \
  --omni-master-port 26000 \
  --deploy-config overlay.yaml
```

Headless worker:

```bash
CUDA_VISIBLE_DEVICES=1 vllm serve MODEL --omni --headless \
  --stage-id 1 \
  --omni-master-address 10.0.0.10 \
  --omni-master-port 26000 \
  --deploy-config overlay.yaml
```

Rules:

- `--stage-id` requires `--omni-master-address` and `--omni-master-port`.
- `--headless` also requires `--stage-id`, master address/port, and `worker_backend=multi_process`.
- `--omni-replica-address` is valid only on headless workers.
- `--omni-dp-size-local` must be `>= 1`; values other than `1` require `--stage-id`.
- Every process should agree on model, deploy config, connector names, `async_chunk`, and compatible stage ids.
- When each process owns only one stage, stage-specific CLI flags are usually clearer than a large `--stage-overrides` JSON, but the JSON form remains the highest-precedence option.

## Connector placement decisions

### Same host

Use `SharedMemoryConnector` when producer and consumer stages run on the same host. It is simple and commonly auto-configured for missing local edges. Explicit wiring is still clearer:

```yaml
connectors:
  shm:
    name: SharedMemoryConnector
stages:
  - stage_id: 0
    output_connectors: {to_stage_1: shm}
  - stage_id: 1
    input_connectors: {from_stage_0: shm}
```

### Multi-node

Use `MooncakeStoreConnector` for cross-host stage transfer over TCP/RDMA-backed Mooncake services:

```yaml
connectors:
  mooncake:
    name: MooncakeStoreConnector
    extra:
      host: "10.0.0.11"                       # local address for this stage host
      metadata_server: "http://10.0.0.10:8080/metadata"
      master: "10.0.0.10:50051"
      segment: 512000000
      localbuf: 64000000
      proto: tcp
stages:
  - stage_id: 0
    output_connectors: {to_stage_1: mooncake}
  - stage_id: 1
    input_connectors: {from_stage_0: mooncake}
```

For multi-node launch, connector configuration and head/headless master registration are separate: Mooncake transports stage payloads, while `--omni-master-address/--omni-master-port` coordinate runtime registration and routing. Both must be reachable.

## Overlay recipe for shrinking one stage

Problem: stage 1 OOMs on a smaller GPU, but base deploy defaults should remain.

```yaml
base_config: base.yaml
stages:
  - stage_id: 1
    devices: "1"
    gpu_memory_utilization: 0.50
    max_num_seqs: 8
    max_num_batched_tokens: 8192
```

Launch with an additional stage-0 concurrency override:

```bash
vllm serve MODEL --omni --deploy-config overlay.yaml \
  --stage-overrides '{"0":{"max_num_seqs":8}}'
```

Precedence outcome:

- Stage 1 memory/concurrency comes from the overlay.
- Stage 0 `max_num_seqs` comes from `--stage-overrides` and wins over the base YAML.
- Unmentioned fields remain inherited from the base deploy or parser defaults.

## Planning checklist before live runs

- [ ] Stage ids in YAML match the selected pipeline.
- [ ] Each connector reference names a top-level connector and both sides of each edge agree.
- [ ] `SharedMemoryConnector` is used only for same-host edges.
- [ ] Mooncake services, addresses, and ports are confirmed for cross-host edges.
- [ ] Each stage's device list has enough logical devices for effective world size.
- [ ] Sum of memory budgets on each GPU leaves headroom.
- [ ] `max_num_seqs`, `max_num_batched_tokens`, and `max_model_len` are set intentionally for the expected request shape.
- [ ] Diffusion parallel/offload/attention fields are model-compatible and not contradictory.
- [ ] CLI JSON is shell-quoted correctly.
- [ ] Model weights/cache, licenses, and runtime budget are approved before starting servers.
