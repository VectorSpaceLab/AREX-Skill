# Deploy schema and precedence

This reference is self-contained for vLLM-Omni deploy YAML work. Use it to inspect, author, or explain overlays without reopening repository docs or source files.

## Configuration objects

### `PipelineConfig`

Installed inspection reported this constructor shape:

```text
PipelineConfig(
  model_type: str,
  model_arch: str = '',
  stages: tuple[StagePipelineConfig, ...] = (),
  hf_architectures: tuple[str, ...] = (),
  hf_config_predicate: Callable[[Any], bool] | None = None,
  diffusers_class_name: str | None = None,
  endpoint_restrictions: tuple[EndpointRestriction, ...] = (),
  duplex_runtime_extension: str | None = None,
  duplex_serving_adapter: str | None = None,
  duplex_control_enabled: bool = False,
  default_deploy_config_name: str | None = None,
)
```

Purpose: immutable model topology. It says which logical stages exist, how they are related, which stage owns tokenizer or final output behavior, and which bundled deploy default belongs to the model. User deploy YAML should not invent a new logical graph except by selecting another registered `pipeline` key.

### `DeployConfig`

Installed inspection reported this constructor shape:

```text
DeployConfig(
  async_chunk: bool = True,
  session_mode: str = 'turn',
  active_stream_window: int = 0,
  duplex_session: DuplexSessionRuntimeConfig = <factory>,
  connectors: dict[str, Any] | None = None,
  edges: list[dict[str, Any]] | None = None,
  stages: list[StageDeployConfig] = <factory>,
  platforms: dict[str, Any] | None = None,
  pipeline: str | None = None,
  trust_remote_code: bool | None = None,
  distributed_executor_backend: str | None = None,
  dtype: str | None = None,
  quantization: str | None = None,
  enable_prefix_caching: bool | None = None,
  enable_chunked_prefill: bool | None = None,
  data_parallel_size: int | None = None,
  pipeline_parallel_size: int | None = None,
  custom_voice_dir: str | None = None,
)
```

Purpose: deploy-time placement and defaults. Top-level engine settings are applied uniformly to each stage unless a later per-stage or CLI layer overrides them.

### `StageDeployConfig`

Installed inspection reported this constructor shape; fields are grouped here by operational purpose:

```text
StageDeployConfig(
  stage_id: int,
  devices: str | None = None,
  num_replicas: int = 1,
  env: dict[str, Any] | None = None,
  output_connectors: dict[str, str] | None = None,
  input_connectors: dict[str, str] | None = None,
  default_sampling_params: dict[str, Any] | None = None,
  default_pooling_params: dict[str, Any] | None = None,
  subtalker_sampling_params: dict[str, Any] | None = None,
  tensor_parallel_size: int | None = None,
  enable_expert_parallel: bool | None = None,
  gpu_memory_utilization: float | None = None,
  max_num_seqs: int | None = None,
  max_num_batched_tokens: int | None = None,
  max_model_len: int | None = None,
  enforce_eager: bool | None = None,
  async_scheduling: bool | None = None,
  disable_hybrid_kv_cache_manager: bool | None = None,
  mm_processor_cache_gb: float | None = None,
  mamba_ssm_cache_dtype: str | None = None,
  compilation_config: dict[str, Any] | None = None,
  profiler_config: dict[str, Any] | None = None,
  skip_mm_profiling: bool | None = None,
  enable_flashinfer_autotune: bool | None = None,
  config_format: str | None = None,
  load_format: str | None = None,
  tokenizer_mode: str | None = None,
  ulysses_degree: int | None = None,
  ulysses_mode: str | None = None,
  ring_degree: int | None = None,
  allgather_degree: int | None = None,
  sequence_parallel_size: int | None = None,
  cfg_parallel_size: int | None = None,
  vae_patch_parallel_size: int | None = None,
  vae_parallel_mode: str | None = None,
  text_encoder_tp_size: int | None = None,
  use_hsdp: bool | None = None,
  hsdp_shard_size: int | None = None,
  hsdp_replicate_size: int | None = None,
  model_class_name: str | None = None,
  diffusion_load_format: str | None = None,
  lora_path: str | list[str] | None = None,
  lora_backend: str | None = None,
  lora_scale: float | None = None,
  diffusers_load_kwargs: dict[str, Any] | None = None,
  diffusers_call_kwargs: dict[str, Any] | None = None,
  diffusion_quantization_config: str | None = None,
  diffusion_attention_backend: str | None = None,
  diffusion_attention_config: dict[str, Any] | None = None,
  diffusion_compile_granularity: str | None = None,
  diffusion_compile_dynamic: bool | None = None,
  fa_deterministic: bool | None = None,
  cache_backend: str | None = None,
  cache_config: dict[str, Any] | None = None,
  enable_cache_dit_summary: bool | None = None,
  step_execution: bool | None = None,
  vae_use_slicing: bool | None = None,
  vae_use_tiling: bool | None = None,
  boundary_ratio: float | None = None,
  flow_shift: float | None = None,
  diffusion_kv_cache_dtype: str | None = None,
  diffusion_kv_cache_skip_steps: str | None = None,
  diffusion_kv_cache_skip_layers: str | None = None,
  auxiliary_text_encoder: str | None = None,
  enable_multithread_weight_load: bool | None = None,
  num_weight_load_threads: int | None = None,
  enable_cpu_offload: bool | None = None,
  enable_layerwise_offload: bool | None = None,
  enable_distributed_layerwise_offload: bool | None = None,
  dlo_use_allgather: bool | None = None,
  dlo_resident_layers: int | None = None,
  enable_diffusion_pipeline_profiler: bool | None = None,
  max_generated_image_size: int | None = None,
  tts_max_instructions_length: int | None = None,
  engine_extras: dict[str, Any] = <factory>,
)
```

Purpose: stage-local knobs. Unknown stage keys are not necessarily invalid: the parser routes unrecognized stage fields into `engine_extras`, which are later forwarded to engine construction. Treat unknown stage keys as warnings unless the user asked for strict schema conformance.

## Top-level deploy YAML schema

```yaml
base_config: base.yaml       # optional overlay parent; relative to this YAML file
async_chunk: true            # streaming/chunked handoff between stages
pipeline: qwen3_omni_moe     # optional registered topology key override
trust_remote_code: true      # pipeline-wide engine field
executor_backend: null       # do not use; correct key is distributed_executor_backend
distributed_executor_backend: mp
# dtype and quantization are pipeline-wide unless a stage intentionally overrides via engine_extras
dtype: bfloat16
quantization: null
data_parallel_size: 1
pipeline_parallel_size: 1
connectors: {}
edges: []
stages: []
platforms: {}
```

Field meanings:

| Field | Expected shape | Operational meaning |
| --- | --- | --- |
| `base_config` | path string | Overlay parent. If relative, resolve it from the overlay file's directory. |
| `async_chunk` | bool | Enables chunked/streaming stage handoff. For single-stage pipelines it is effectively disabled. Multi-stage pipelines require async-capable stage processors when true. |
| `connectors` | mapping of name -> connector spec | Defines named transport implementations referenced by stage `input_connectors` and `output_connectors`. |
| `edges` | list of `{from: int, to: int}` | Optional explicit stage graph; if omitted, the runtime derives edges from stage inputs/connectors and pipeline topology. |
| `stages` | list of stage mappings | Required in a fully materialized deploy file. Overlays may contain only the stages they modify if `base_config` resolves. |
| `platforms` | mapping of platform -> `{stages: [...]}` | Per-platform stage overrides layered on top of the base stages for detected platforms such as `npu`, `rocm`, `xpu`, or `musa`. |
| `pipeline` | string | Selects a registered topology variant when auto-detection is insufficient. |
| `trust_remote_code` | bool/null | Pipeline-wide HF remote-code toggle. CLI `--trust-remote-code` can explicitly override to true; absence is not the same as false. |
| `distributed_executor_backend` | `mp`, `ray`, `external_launcher`, or null | Pipeline-wide vLLM distributed executor backend. Diffusion paths commonly default to `mp`; `ray` and `external_launcher` may be unsupported for some diffusion stages. |
| `dtype` | string/null | Pipeline-wide model dtype. |
| `quantization` | string/null | Pipeline-wide quantization method. Do not assume one stage's quantization works for all model components. |
| `enable_prefix_caching` | bool/null | Pipeline-wide prefix cache setting. Some latent-output stages should keep it false. |
| `enable_chunked_prefill` | bool/null | Pipeline-wide vLLM chunked prefill setting. Distinct from `async_chunk`. |
| `data_parallel_size` | int/null | Pipeline-wide DP degree applied to every stage unless overridden later. |
| `pipeline_parallel_size` | int/null | Pipeline-wide PP degree applied to every stage unless overridden later. |

## Stage schema

A modern deploy YAML puts stage fields directly in each `stages:` entry, not under a nested `engine_args:` block. The parser also accepts legacy `engine_args:` and `runtime:` blocks and flattens them, but prefer the flat layout for new overlays.

```yaml
stages:
  - stage_id: 0
    devices: "0"
    num_replicas: 1
    output_connectors: {to_stage_1: shm}
    gpu_memory_utilization: 0.85
    max_num_seqs: 32
    max_num_batched_tokens: 32768
    max_model_len: 16384
    tensor_parallel_size: 1
    enforce_eager: false
    async_scheduling: true
    default_sampling_params:
      temperature: 0.0
      max_tokens: 2048
```

Important stage fields:

| Field | Meaning |
| --- | --- |
| `stage_id` | Required integer; must match a stage in the selected `PipelineConfig`. Unknown ids are ignored or fail depending on the code path; treat them as configuration errors. |
| `devices` | Logical device list for the stage process, e.g. `"0"` or `"0,1"`. It is interpreted after the process visibility environment. |
| `num_replicas` | Stage-local replica fan-out. In head/headless mode, `--omni-dp-size-local` controls how many replicas one process launches locally for its own `--stage-id`. |
| `input_connectors` / `output_connectors` | Edge-to-connector-name maps such as `from_stage_0: shm` and `to_stage_1: shm`. The referenced connector must exist in top-level `connectors`. |
| `gpu_memory_utilization` | Fraction of each assigned GPU memory vLLM may request for this stage. Use a value below 1.0 to leave driver/framework/headroom. |
| `max_num_seqs` | Stage-local concurrent sequence/request capacity. Lower it to reduce KV/cache or scheduler pressure; raise it only when memory and batching support permit. |
| `max_num_batched_tokens` | Stage-local prefill/token batch budget. Reduce for OOM during prefill or long prompts. |
| `max_model_len` | Stage-local context length. Large values increase memory pressure and may require allowing long model length in the runtime. |
| `tensor_parallel_size` | Stage-local TP degree; make `devices` contain at least this many logical GPUs for that stage. |
| Diffusion parallel fields | `ulysses_degree`, `ring_degree`, `allgather_degree`, `cfg_parallel_size`, `vae_patch_parallel_size`, `text_encoder_tp_size`, `use_hsdp`, `hsdp_shard_size`, `hsdp_replicate_size`. See `memory-and-distributed-placement.md`. |
| Diffusion offload fields | `enable_cpu_offload`, `enable_layerwise_offload`, `enable_distributed_layerwise_offload`, `dlo_use_allgather`, `dlo_resident_layers`. See `memory-and-distributed-placement.md`. |
| Diffusion attention fields | `diffusion_attention_backend`, `diffusion_attention_config`, `fa_deterministic`. Use for backend-specific diffusion attention choices; keep model compatibility explicit. |
| `engine_extras` | Explicit catch-all for stage engine args not represented by named fields. Unknown flat keys also land here. |

## Connector schema

Top-level connector specs have this shape:

```yaml
connectors:
  shm:
    name: SharedMemoryConnector
    extra: {}

  mooncake:
    name: MooncakeStoreConnector
    extra:
      host: "10.0.0.12"
      metadata_server: "http://10.0.0.10:8080/metadata"
      master: "10.0.0.10:50051"
      segment: 512000000
      localbuf: 64000000
      proto: tcp
```

| Connector | Use when | Required decisions |
| --- | --- | --- |
| `SharedMemoryConnector` | Stages are on the same host and can share host shared-memory resources. This is the safe default for most single-node bundled deploys. | Ensure both stages run on the same machine and connector names match on both sides of each edge. |
| `MooncakeStoreConnector` | Stages are split across hosts or need TCP/RDMA-backed cross-node transport. | Confirm the Mooncake package/services are installed, `host` is the local host address, `master` and `metadata_server` point at live services, `segment`/`localbuf` fit host memory, and `proto` is `tcp` or `rdma`. |

A stage references a connector by name:

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

If an edge has no explicit connector, the runtime may auto-configure a shared-memory connector for local deployments. Do not rely on that for multi-node; wire cross-host connectors explicitly.

## Overlay and merge rules

`base_config` creates an overlay file. The loader first resolves the base, then applies the overlay:

- Top-level scalar fields: overlay wins.
- `stages:`: lists are merged by `stage_id`; overlay stage fields win for that stage.
- `platforms:`: merged by platform key, and each platform's `stages:` list is merged by `stage_id`.
- Deep-merge stage subdicts: `default_sampling_params`, `default_pooling_params`, `subtalker_sampling_params`, `engine_extras`, and `engine_args`.
- Other dicts/lists are replaced by the overlay value unless they are one of the deep-merge keys above.

Minimal overlay example:

```yaml
base_config: qwen3_omni_moe.yaml
stages:
  - stage_id: 1
    gpu_memory_utilization: 0.50
    max_num_seqs: 16
```

Platform override example:

```yaml
platforms:
  rocm:
    stages:
      - stage_id: 2
        enforce_eager: true
  npu:
    stages:
      - stage_id: 0
        devices: "0,1"
        tensor_parallel_size: 2
        gpu_memory_utilization: 0.60
```

## CLI flags and precedence

Primary stage/deploy CLI flags:

| Flag | Use |
| --- | --- |
| `--deploy-config PATH` | Load a deploy YAML or overlay. If omitted, the model registry may choose a package-bundled default. |
| `--stage-overrides JSON` | Highest-priority per-stage overrides keyed by stringified `stage_id`, for example `'{"0":{"max_num_seqs":8}}'`. |
| `--async-chunk` / `--no-async-chunk` | Override YAML `async_chunk`; absent leaves the YAML value in force. |
| Explicit global flags | Values like `--gpu-memory-utilization`, `--max-model-len`, `--dtype`, or `--quantization` apply to all stages unless per-stage overrides win. |
| Stage-specific CLI aliases | Some parser paths expose `--stage-0-gpu-memory-utilization` style keys; these affect only that stage. |

Effective precedence, highest to lowest:

1. Per-stage overrides (`--stage-overrides` or `stage_<id>_<field>` runtime keys)
2. Explicit global CLI flags (only values the user actually typed or loaded from a CLI config file)
3. Platform section (`platforms.<current_platform>.stages`) applied on top of base stages
4. Overlay YAML via `base_config`
5. Parser/dataclass defaults

Worked example:

```yaml
# overlay.yaml
base_config: qwen3_omni_moe.yaml
stages:
  - stage_id: 1
    gpu_memory_utilization: 0.50
```

```bash
vllm serve MODEL --omni --deploy-config overlay.yaml \
  --max-model-len 16384 \
  --stage-overrides '{"0":{"max_num_seqs":8}}'
```

Expected final sources:

| Stage | Field | Source |
| --- | --- | --- |
| 0 | `max_num_seqs=8` | per-stage CLI override |
| 0 and 1 | `max_model_len=16384` | explicit global CLI flag |
| 1 | `gpu_memory_utilization=0.50` | overlay stage field |
| unchanged fields | inherited | base deploy/defaults |

## Stage-based head/headless launch paradigm

In a stage-split serving deployment:

- Stage 0 is normally the head/orchestrator/API process. It needs `--stage-id 0`, `--omni-master-address`, `--omni-master-port`, and ordinary server options such as `--port`.
- Worker stages run with `--headless`, their own `--stage-id`, and the same master address/port so they can register with stage 0.
- Every process that participates in the same deployment should load the same `--deploy-config` overlay and compatible CLI overrides.
- `--omni-replica-address` is for headless workers only; do not pass it to the head.
- `--omni-dp-size-local N` is process-local and requires `--stage-id`; it launches N local replicas for that process's stage.

Example shape:

```bash
CUDA_VISIBLE_DEVICES=0 vllm serve MODEL --omni \
  --stage-id 0 --port 8091 \
  --omni-master-address 10.0.0.10 --omni-master-port 26000 \
  --deploy-config overlay.yaml

CUDA_VISIBLE_DEVICES=1 vllm serve MODEL --omni --headless \
  --stage-id 1 \
  --omni-master-address 10.0.0.10 --omni-master-port 26000 \
  --deploy-config overlay.yaml
```

Use the troubleshooting reference for launch validation failures and connector mismatch symptoms.
