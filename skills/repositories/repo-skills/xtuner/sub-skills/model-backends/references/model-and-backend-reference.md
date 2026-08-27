# XTuner V1 model and backend reference

This reference summarizes operational knowledge for selecting XTuner V1 model configs and backend features. It is intentionally self-contained: use installed `xtuner` package imports and the bundled checker rather than reading an original source checkout at runtime.

## 1. Model config selection

### Alias helpers

Use aliases when they are enough:

```python
from xtuner.v1.model import get_model_config, get_model_config_from_hf

cfg = get_model_config("qwen3-moe-30BA3")
assert cfg is not None
```

`get_model_config(alias)` normalizes case and hyphen/underscore differences. Known aliases include:

| Alias | Returned config family | Notes |
|---|---|---|
| `qwen3-moe-30BA3` | `Qwen3MoE30BA3Config` | Text MoE, about 30B total / 3B activated. |
| `qwen3-8B` | `Qwen3Dense8BConfig` | Text dense. |
| `qwen3-4B` | `Qwen3Dense4BConfig` | Text dense; tied embeddings. |
| `intern-s1` | `InternS1Config` | Compose/VLM with Qwen3 MoE text config. |
| `intern-s1-mini` | `InternS1MiniConfig` | Compose/VLM with Qwen3 dense text config. |
| `gpt-oss-20b` | `GptOss21BA3P6Config` | Text MoE. |
| `gpt-oss-120b` | `GptOss117BA5P8Config` | Text MoE. |
| `internvl-3.5-8b-hf` | `InternVL3P5Dense8BConfig` | Compose/VLM dense. |
| `internvl-3.5-1b-hf` | `InternVL3P5Dense1BConfig` | Compose/VLM dense. |
| `internvl-3.5-30b-a3b-hf` | `InternVL3P5MoE30BA3Config` | Compose/VLM MoE. |
| `qwen3.5-vl-4b` | `Qwen3_5_VLDense4BConfig` | Compose/VLM dense. |
| `glm-5.2` | `Glm52MoEConfig` | Text MoE with GLM-style attention/router details. |

If an alias is absent, instantiate the concrete class directly or use `get_model_config_from_hf(Path(...))` for supported HuggingFace text configs. The HF helper supports text model types such as `qwen3_moe`, `qwen3_moe_fope`, `qwen2`, `qwen3`, `gpt_oss`, `deepseek_v3`, and `glm_moe_dsa`. Compose/VLM `from_hf` support is more limited; expect some VLM configs to retain the original HF config during save rather than converting every changed XTuner value.

### Config family map

| Family | Representative classes | Backend implications |
|---|---|---|
| Qwen2 dense | `Qwen2DenseConfig`, `Qwen2Dense7BConfig` | Dense transformer; no expert router/dispatcher. |
| Qwen3 dense | `Qwen3DenseConfig`, `Qwen3Dense8BConfig`, `Qwen3Dense4BConfig`, `Qwen3Dense0P6BConfig` | Dense transformer; use FSDP and optional TP. |
| Qwen3 MoE | `Qwen3MoEConfig`, `Qwen3MoE30BA3Config`, `Qwen3MoE235BA22Config`, `Qwen3MoEFoPEConfig` | Routed experts, grouped linear/GEMM, optional EP dispatcher, balancing/z/aux losses. |
| GPT-OSS MoE | `GptOssConfig`, `GptOss21BA3P6Config`, `GptOss117BA5P8Config` | MoE plus GPT-OSS attention variants such as sink/gate handling. |
| DeepSeek/GLM MoE | `DeepSeekV3Config`, `Glm52MoEConfig` | MoE/MLA/DSA style paths; verify optional sparse/attention backend support. |
| Qwen3-VL | `Qwen3VLDense4BConfig`, `Qwen3VLDense8BConfig`, `Qwen3VLMoE30BA3Config`, `Qwen3VLMoE235BA22Config` | Compose model with vision config + projector + text config; image/video tokens; VLM attention fallback rules. |
| Qwen3.5-VL | `Qwen3_5_VLDense4BConfig`, `Qwen3_5_VLMoE35BA3Config` and split/time-series variants | Compose model with Qwen3.5-specific token ids and text configs. |
| InternVL | `InternVL3P5Dense1BConfig`, `InternVL3P5Dense8BConfig`, `InternVL3P5MoE30BA3Config` | Compose model with InternVL vision/projector and dense or MoE Qwen3 text backend. |
| InternS1 | `InternS1Config`, `InternS1MiniConfig` | Compose scientific VLM; full InternS1 uses Qwen3 MoE 235B-style text config, mini uses Qwen3 dense 8B-style text config. |

## 2. Dense vs MoE choice

### Dense configs

Choose dense when the goal is simpler setup, fewer optional dependencies, easier HF parity, or smaller-scale fine-tuning. Dense configs avoid expert routing, `dispatcher`, `ep_size`, balancing losses, and grouped GEMM concerns.

Typical dense skeleton:

```python
from xtuner.v1.config import FSDPConfig
from xtuner.v1.model import Qwen3Dense8BConfig

model_cfg = Qwen3Dense8BConfig(compile_cfg=False)
fsdp_cfg = FSDPConfig(tp_size=1, ep_size=1, recompute_ratio=1.0)
```

Dense resource notes:

- Keep `ep_size=1`.
- Use `tp_size > 1` only when memory pressure justifies splitting attention/MLP work; larger TP can reduce per-rank matrix size and communication efficiency.
- `Qwen3Dense4BConfig` uses tied word embeddings by default; verify save/load behavior when changing vocab or embedding settings.
- VLM dense configs include vision/projector submodules and may need vision-specific `recompute_ratio` or freeze choices at training time.

### MoE configs

Choose MoE when the target model is a routed-expert model or when activated-parameter efficiency is required. MoE configs add expert load, top-k routing, grouped linear/GEMM, auxiliary/balancing loss accounting, and possible expert-parallel all-to-all communication.

Typical Qwen3 MoE skeleton:

```python
from xtuner.v1.config import FSDPConfig
from xtuner.v1.model import Qwen3MoE30BA3Config

model_cfg = Qwen3MoE30BA3Config(
    compile_cfg=False,
    ep_size=8,
    dispatcher="all2all",
)
fsdp_cfg = FSDPConfig(tp_size=1, ep_size=8, recompute_ratio=1.0)
```

MoE resource notes:

- Keep `model_cfg.ep_size` and `FSDPConfig(ep_size=...)` aligned.
- If `ep_size == 1`, any explicit dispatcher is ignored or downgraded to the local/naive path.
- If `ep_size > 1` and `dispatcher is None`, XTuner defaults to the torch all-to-all dispatcher.
- EP partitions experts but does not remove attention or activation memory. TP is still the main lever for activation memory when sequence/attention memory is the bottleneck.
- Increasing EP can improve expert GEMM density but adds all-to-all communication and can amplify load-imbalance sensitivity.
- `Qwen3MoE30BA3Config` defaults include 128 routed experts and top-8 routing with softmax greedy router. `Qwen3MoE235BA22Config` keeps 128 routed experts/top-8 but increases layers, hidden size, and activated scale.

## 3. FSDP, TP, EP, and HSDP sizing

`FSDPConfig` controls XTuner V1 model sharding and parallel mesh settings:

| Field | Operational meaning |
|---|---|
| `tp_size` | Tensor parallel size. Use sparingly; it can reduce memory but also lowers per-rank compute granularity. |
| `ep_size` | Expert parallel size. Must match MoE model config when using EP. Keep at `1` for dense models. |
| `reshard_after_forward` | Reshard parameters after forward to save memory. Default `True`. |
| `recompute_ratio` | Gradient checkpointing ratio for memory optimization. Default `1.0`. |
| `vision_recompute_ratio` | Recompute ratio for vision modules in compose/VLM models. |
| `cpu_offload` | Memory escape hatch; version-sensitive and not a default performance path. Verify full train/backward before relying on it. |
| `param_dtype`, `reduce_dtype` | Default to `torch.bfloat16`; make dtype changes deliberately and verify numerics/backend support. |
| `fp32_lm_head` | Keep language head in FP32 when needed for stability. |
| `torch_compile` | Default `True`; disable (`False`) when debugging or when compile interacts badly with optional kernels. |
| `hsdp_sharding_size` | Hybrid sharding size. XTuner asserts that HSDP currently requires `ep_size == 1`. |

Sizing checklist:

1. Confirm total world size and divisibility by TP/EP/FSDP mesh factors.
2. For dense models, start `tp_size=1`, `ep_size=1`, FSDP enabled; add TP only if memory needs it.
3. For MoE models, start with small EP (`ep_size=1` for local sanity or intra-node EP for real training), then select `all2all` or a verified optional dispatcher.
4. Do not combine HSDP with EP; `hsdp_sharding_size` requires `ep_size == 1`.
5. For VLM, include vision/projector memory and recomputation in capacity planning.

## 4. Attention and sequence-backend choices

`MHAConfig.attn_impl` accepts:

- `flash_attention`: fastest path when FlashAttention is installed and compatible.
- `flex_attention`: PyTorch flex attention fallback used by XTuner when FlashAttention is missing on CUDA.
- `eager_attention`: dense reference-style implementation; useful for debugging and HF parity.

Important behavior:

- On CUDA, XTuner config post-init checks for `flash-attn` or `flash-attn-3`. If missing and `attn_impl="flash_attention"`, it logs a warning and switches many config objects to `flex_attention`.
- `XTUNER_HF_IMPL=true` forces the eager attention implementation at runtime for HF-parity tests.
- Vision configs in Qwen3-VL, Qwen3.5-VL, InternVL, and InternS1 have their own `attn_impl` fields and the same flash-to-flex warning pattern.
- `with_sink`, `with_gate`, sliding window, MLA/DSA, and sparse MLA paths are model-family-specific. Treat them as backend-sensitive until the concrete optional kernels are checked.

## 5. Routers, dispatchers, and MoE load behavior

### Router configs

`GreedyRouterConfig` fields:

- `scoring_func`: `"softmax"` or `"sigmoid"`; common Qwen3 defaults use softmax.
- `router_scaling_factor`: scales selected top-k weights.
- `norm_topk_prob`: normalizes selected top-k probabilities.
- `use_grouped_router`, `router_n_groups`: grouped router mode used by specialized dispatchers.

`NoAuxRouterConfig` adds `n_group`, `topk_group`, and `router_bias_update_speed`; it is used by no-auxiliary-loss balancing variants. The grouped variant requires `router_n_groups` and top-k/group constraints.

### Dispatcher choices

| `dispatcher` value | Use when | Dependency/risk |
|---|---|---|
| `None` | `ep_size == 1` local MoE sanity path. | If EP group size is 1, explicit dispatchers are not used. |
| `all2all` | Default distributed EP path using torch all-to-all. | Requires distributed CUDA/NPU runtime; performance depends on topology. |
| `deepep` | High-performance expert all-to-all when DeepEP is installed and configured. | Requires `deep_ep` and `deep_ep_cpp`; only claim after real import and cluster check. |
| `agrs` | Specialized all-gather/reduce-scatter style path. | Requires grouped router; XTuner asserts `ep_size == router_n_groups == 8` for AGRS. |

Use `return_router_results=True` for debugging router outputs only when memory overhead is acceptable. `router_async_offload=True` offloads router tensors asynchronously and is advanced; verify correctness and performance before using it.

## 6. FP8 and grouped GEMM

`Float8Config` has two fields:

- `scaling_granularity_gemm`: `ScalingGranularity.TILEWISE` or `ScalingGranularity.TENSORWISE` for ordinary linear GEMM.
- `scaling_granularity_grouped_gemm`: intended for grouped GEMM; operationally treat TILEWISE as the supported grouped path unless the target installation proves otherwise.

Example:

```python
from xtuner.v1.float8.config import Float8Config, ScalingGranularity
from xtuner.v1.model import Qwen3Dense8BConfig

float8_cfg = Float8Config(
    scaling_granularity_gemm=ScalingGranularity.TILEWISE,
    scaling_granularity_grouped_gemm=ScalingGranularity.TILEWISE,
)
model_cfg = Qwen3Dense8BConfig(float8_cfg=float8_cfg)
```

FP8 verification rules:

- Effective FP8 requires a real CUDA device with SM89/Hopper-class or newer capability; config construction alone is not enough.
- Tile-wise FP8 linear and grouped-linear paths require `adaptive_gemm` imports.
- Triton-backed quantization kernels must be importable and compatible with the installed Torch/CUDA stack.
- FP8 is designed to work with FSDP so that communication and graph-memory savings offset quantization overhead. Isolated module timing may not reflect training throughput.
- If the FP8 handler logs that FP8 is unsupported on the current device, fall back to BF16 and record the unverified FP8 gap.

## 7. Loss and optimizer contexts that affect backend sizing

- `CELossConfig(mode="chunk", chunk_size=1024, loss_reduction="token")` is the memory-saving CE-loss path. `mode="eager"` is simpler but can use much more memory for large vocab/sequence settings.
- MoE configs may carry `BalancingLossConfig`, `ZLossConfig`, and `AuxLossConfig`. These add router statistics and global reductions; verify distributed groups and memory before enabling extra router-result logging.
- `AdamWConfig` is the standard optimizer config. `MuonConfig` has MoE-aware parameter grouping and optional all-to-all behavior; verify optional Triton/all-to-all paths before relying on it for large MoE jobs.
- RL-specific loss/advantage contexts should be handled by the reinforcement-learning sub-skill, not here.

## 8. HF save and checkpoint caveats

- Text `TransformerConfig` subclasses usually implement `hf_config` and HF key mapping for save/export.
- `HFSaveCfg` controls HF shard writing: `worker_per_rank`, `max_save_rank`, `bucket_size`, and optional `fp32_keys_pattern` regexes.
- Compose/VLM configs may warn that full conversion to HuggingFace config is not implemented and that the original HF config is retained. Do not silently promise changed VLM config values will appear in HF `config.json` unless verified.
- Async HF save behavior is a training/checkpoint workflow; route detailed launch/resume/save orchestration to training.

## 9. Verification levels

| Level | What it proves | What it does not prove |
|---|---|---|
| Import check | Package and Python module surface are reachable. | No CUDA/NPU kernel, no distributed communication, no throughput. |
| CPU config construction | Config classes, pydantic fields, helpers, and some pure CPU modules work. | MoE grouped GEMM, flash attention, FP8, DeepEP, real training. |
| CUDA visibility smoke | Torch sees CUDA devices and reports version/capability. | Optional extension ABI compatibility or XTuner kernels. |
| Optional dependency import | Extension package is installed and importable. | Correct GPU architecture, distributed topology, or numerical correctness. |
| Native CUDA/NPU tests or tiny training | Actual backend path runs on target hardware. | Full-scale memory/performance unless matched to target scale. |

Use the bundled checker for the first four levels, then require native tests or training-smoke evidence before claiming backend acceleration.
