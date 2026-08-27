# Backend Configuration

LMDeploy exposes one public `pipeline(model_path, backend_config=..., ...)` entry point and chooses either the PyTorch engine or TurboMind from the backend config and model support. Use explicit backend configs for reproducible tuning instead of relying on auto selection during debugging.

## Backend Selection

- Use `PytorchEngineConfig` when you need widest Hugging Face architecture coverage, Python-side model patching, `custom_module_map`, LoRA adapter support, PyTorch scheduler inspection, or fast maintainer iteration.
- Use `TurbomindEngineConfig` when TurboMind supports the model and the task prioritizes high-throughput conversational serving, persistent batching, TurboMind KV-cache behavior, or TurboMind-specific weight formats.
- `autoget_backend_config()` maps compatible config fields across backends. If the wrong engine is selected or TurboMind is unavailable, LMDeploy falls back to PyTorch with a warning.
- For VLMs, backend selection also depends on model architecture and vision encoder handling. Route prompt/media specifics to `vision-language`.

Minimal explicit selection:

```python
from lmdeploy import PytorchEngineConfig, TurbomindEngineConfig, pipeline

pt_pipe = pipeline(model_path, backend_config=PytorchEngineConfig(tp=1))
tm_pipe = pipeline(model_path, backend_config=TurbomindEngineConfig(tp=1))
```

## PyTorch Engine Fields

`PytorchEngineConfig` validates its fields at construction time. The highest-value knobs are:

| Field | Use | Notes |
| --- | --- | --- |
| `dtype` | Weight/activation dtype | `auto`, `float16`, or `bfloat16`. BF16 may downshift if unsupported by device. |
| `tp`, `dp`, `ep` | Parallelism | `DistConfig` derives attention/MLP/MoE TP and asserts divisibility. |
| `attn_tp_size`, `mlp_tp_size`, `moe_tp_size` | DP+TP split control | Only meaningful with data/expert parallel paths. |
| `session_len` | Max context/session length | Raises memory pressure through scheduler/cache allocation. |
| `max_batch_size` | Max concurrent batch size | If omitted, engine infers from environment. |
| `cache_max_entry_count` | KV-cache free-memory fraction | Must satisfy `0 < value < 1` for PyTorch. Lower for OOM. |
| `block_size`, `kernel_block_size` | Paging granularity | `kernel_block_size` defaults to `block_size`; must be power of two >= 16 and divide `block_size`. |
| `num_cpu_blocks`, `num_gpu_blocks` | Explicit block counts | Use for tests or tightly controlled cache sizing; `0` lets runtime allocate. |
| `max_prefill_token_num` | Chunked prefill size | Lower to reduce peak prefill memory; higher may improve throughput. |
| `prefill_interval` | Scheduling interval | Tune only after measuring latency/throughput. |
| `cudagraph_capture_batch_sizes` | CUDA graph capture | Non-empty positive sizes, filtered to `<= max_batch_size`; max batch is appended. |
| `enable_prefix_caching` | Reuse matching prompt prefixes | Disabled automatically for window attention in `CacheConfig`. |
| `prefix_cache_state_budget`, `prefix_cache_decode_state_interval` | SSM prefix-cache checkpoints | Keep at defaults unless repeated SSM continuations justify extra state memory/copy cost. |
| `quant_policy` | KV-cache quantization | Accepts `QuantPolicy` values: `NONE`, `INT4`, `INT8`, `FP8`, `FP8_E5M2`, `TURBO_QUANT`; positive values require CUDA or Ascend. |
| `custom_module_map` | External PyTorch model rewrite map | Used for new model support without editing installed LMDeploy source. |
| `distributed_executor_backend`, `enable_mp_engine`, `mp_engine_backend` | Process/distributed execution | Use `if __name__ == "__main__":` guards for multiprocessing entrypoints. |
| `model_format` | Weight format hint | PyTorch path currently uses this for formats such as `fp8`. |
| `hf_overrides` | Override Hugging Face config | Useful for known config fixes; record the override in reproducibility notes. |
| `disable_vision_encoder` | Skip VLM vision encoder | Backend-level knob; media semantics belong to `vision-language`. |

Example cache/OOM-oriented config:

```python
from lmdeploy import PytorchEngineConfig, pipeline

backend_config = PytorchEngineConfig(
    dtype='auto',
    tp=1,
    session_len=4096,
    cache_max_entry_count=0.45,
    max_prefill_token_num=2048,
    enable_prefix_caching=True,
)
pipe = pipeline(model_path, backend_config=backend_config)
```

## TurboMind Engine Fields

Use `TurbomindEngineConfig` for supported models and TurboMind runtime tuning. Important differences from PyTorch:

- `cache_max_entry_count` must be positive; decimals represent a memory fraction and integers can represent block counts.
- `cache_block_seq_len` is TurboMind's cache block token length; PyTorch names the analogous field `block_size`.
- `quant_policy` supports INT4 and INT8 KV-cache quantization. TurboMind rejects FP8 policies.
- `async_` is `1` or `0`, not a boolean field name at the Python API boundary.
- `model_format` can describe TurboMind/HF weight layout such as `hf`, `awq`, `gptq`, `compressed-tensors`, `fp8`, or `mxfp4`.

Example TurboMind config:

```python
from lmdeploy import TurbomindEngineConfig, pipeline

backend_config = TurbomindEngineConfig(
    dtype='auto',
    tp=1,
    session_len=8192,
    cache_max_entry_count=0.5,
    cache_block_seq_len=128,
    enable_prefix_caching=True,
    quant_policy=8,
)
pipe = pipeline(model_path, backend_config=backend_config)
```

## Scheduler And Cache Mental Model

PyTorch scheduling uses `SchedulerConfig` plus `CacheConfig`:

- The scheduler admits waiting sequences, allocates KV cache blocks, evicts stopped sequences, and tracks running/waiting/hanging status.
- `block_size` controls cache block granularity; smaller blocks reduce internal waste but add metadata/management overhead.
- Prefix caching matches shared prompt blocks before allocation, then rolls back tentative matches if eviction, long-context chunking, or state-cache allocation cannot safely proceed.
- SSM state-cache checkpoints are separate from ordinary KV blocks; decode checkpoints can improve repeated continuations but consume extra state slots.
- `max_prefill_token_num` caps per-iteration prefill tokens and can reduce OOM on large prompts or multimodal-prefill-heavy requests.

Useful native tests for scheduler/config changes:

```bash
pytest tests/pytorch/config/test_model_config.py
pytest tests/pytorch/paging/test_scheduler.py
```

## Validation Pattern

1. Construct the backend config in a tiny Python snippet first so dataclass assertions catch invalid values.
2. Run `python -m lmdeploy check_env` when runtime/build dependencies are suspect.
3. From this sub-skill directory, run `python scripts/inspect_backend_config.py --json` to confirm the installed API and module map without model loading.
4. If changing PyTorch scheduler or cache code, run targeted scheduler/config tests.
5. If changing model support, run config-builder and module-map checks before any GPU/model-weight test.

Dataclass smoke check:

```bash
python - <<'PY'
from lmdeploy import PytorchEngineConfig, TurbomindEngineConfig
print(PytorchEngineConfig(cache_max_entry_count=0.5, block_size=64))
print(TurbomindEngineConfig(cache_max_entry_count=0.5, cache_block_seq_len=128))
PY
```
