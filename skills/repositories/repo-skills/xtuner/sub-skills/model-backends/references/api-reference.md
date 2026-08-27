# XTuner V1 model-backends API reference

Use this as a quick import and field reference for model/backend tasks. APIs listed here were distilled from the XTuner V1 package surface and installed-package signatures. Always verify optional acceleration on the target machine.

## 1. Core imports

```python
from pathlib import Path
import torch

from xtuner.v1.model import (
    get_model_config,
    get_model_config_from_hf,
    Qwen3Dense8BConfig,
    Qwen3Dense4BConfig,
    Qwen3Dense0P6BConfig,
    Qwen3MoE30BA3Config,
    Qwen3MoEConfig,
    Qwen3VLDense4BConfig,
    Qwen3VLDense8BConfig,
    Qwen3VLMoE30BA3Config,
    Qwen3VLMoE235BA22Config,
    InternS1Config,
    InternS1MiniConfig,
    InternVL3P5Dense1BConfig,
    InternVL3P5Dense8BConfig,
    InternVL3P5MoE30BA3Config,
)
from xtuner.v1.config import FSDPConfig, AdamWConfig, LRConfig, OptimConfig
from xtuner.v1.float8.config import Float8Config, ScalingGranularity
from xtuner.v1.loss.ce_loss import CELossConfig
from xtuner.v1.module.attention import MHAConfig, MLAConfig, GatedDeltaNetConfig
from xtuner.v1.module.router.greedy import GreedyRouterConfig
from xtuner.v1.module.router.noaux_router import NoAuxRouterConfig
```

Some classes may not be exported by the top-level `xtuner.v1.model` namespace in every installed build. If a top-level import fails, import from the concrete module path shown by the class name in package docs.

## 2. Helper functions

| Helper | Signature | Use | Notes |
|---|---|---|---|
| `get_model_config` | `(model_alias: str)` | Return an instantiated config for a known alias. | Returns `None` for unknown aliases; aliases are normalized by lowercasing and hyphen/underscore replacement. |
| `get_model_config_from_hf` | `(model_path: pathlib.Path)` | Convert a supported HuggingFace text config to an XTuner config. | Supports common text model types; compose/VLM support is limited. |

Example:

```python
cfg = get_model_config("qwen3_moe_30BA3")
if cfg is None:
    raise ValueError("Unknown XTuner model alias")

hf_cfg = get_model_config_from_hf(Path("/path/to/hf/model"))
```

## 3. Base model config fields

All XTuner model configs derive from `XTunerBaseModelConfig` or compose wrappers around it.

| Field | Type / default | Meaning |
|---|---|---|
| `hf_save_cfg` | `HFSaveCfg()` | HF save worker/shard configuration. |
| `float8_cfg` | `Float8Config | None` | Enables FP8 conversion paths when backend supports them. |
| `compile_cfg` | `dict | None | bool` | `None`/`True` uses defaults, `False` disables compile, dict customizes compile options. |
| `hf_key_mapping` | `dict[str, str] | None` | Regex mapping from XTuner parameter keys to HF parameter keys. |
| `dcp_ignore_frozen_params` | `bool = True` | DCP/FSDP save behavior for frozen params. |
| `lm_loss_cfg` | `BaseLossConfig` | Default language-model loss config, commonly CE loss. |

`TransformerConfig` adds model-shape fields such as `vocab_size`, `max_position_embeddings`, `num_hidden_layers`, `hidden_size`, `intermediate_size`, `attention`, `rope_parameters_cfg`, `use_sliding_window`, `max_window_layers`, `generate_config`, and `mesh_prefix`.

## 4. Concrete model config quick table

| Class | Key defaults / identity | When to choose |
|---|---|---|
| `Qwen3Dense8BConfig` | 36 layers, hidden 4096, 32 attention heads, 8 KV heads, head dim 128, sliding window 1024, untied embeddings. | Main Qwen3 dense 8B-style backend. |
| `Qwen3Dense4BConfig` | 36 layers, hidden 2560, max position 262144, tied embeddings. | Smaller dense text or VLM text base. |
| `Qwen3Dense0P6BConfig` | 28 layers, hidden 1024, 16 attention heads. | Tiny/dense sanity and InternVL 1B-style text base. |
| `Qwen3MoE30BA3Config` | 48 layers, hidden 2048, 128 routed experts, top-8, MoE intermediate 768. | Qwen3 30B total / 3B activated MoE. |
| `Qwen3MoE235BA22Config` | 94 layers, hidden 4096, 128 routed experts, top-8, MoE intermediate 1536. | Qwen3 235B total / 22B activated MoE. |
| `Qwen3MoEFoPEConfig` | HF-derived FoPE variant. | Qwen3 MoE with frequency-based position embedding. |
| `Qwen3VLDense4BConfig`, `Qwen3VLDense8BConfig` | Vision config + projector + Qwen3-VL text dense config. | Image/video + text dense VLM. |
| `Qwen3VLMoE30BA3Config`, `Qwen3VLMoE235BA22Config` | Vision config + projector + Qwen3-VL text MoE config. | Image/video + text MoE VLM. |
| `Qwen3_5_VLDense4BConfig`, `Qwen3_5_VLMoE35BA3Config` | Qwen3.5-specific token ids and vision/projector config. | Qwen3.5-VL dense or MoE workflows. |
| `InternVL3P5Dense1BConfig`, `InternVL3P5Dense8BConfig`, `InternVL3P5MoE30BA3Config` | InternVL vision/projector with Qwen3 dense or MoE text config. | InternVL 3.5 compose models. |
| `InternS1MiniConfig`, `InternS1Config` | InternS1 vision/projector; mini uses dense, full uses Qwen3 MoE-style text. | InternS1 VLM workflows. |
| `GptOss21BA3P6Config`, `GptOss117BA5P8Config` | GPT-OSS MoE variants. | GPT-OSS training/backends. |
| `DeepSeekV3Config`, `Glm52MoEConfig` | MoE/MLA/DSA-style configs. | DeepSeek/GLM-style backends with extra optional attention paths. |

## 5. `FSDPConfig`

Signature fields:

```python
FSDPConfig(
    tp_size=1,
    ep_size=1,
    reshard_after_forward=True,
    recompute_ratio=1.0,
    vision_recompute_ratio=1.0,
    checkpoint_preserve_rng_state=True,
    mtp_checkpoint_use_reentrant=True,
    cpu_offload=False,
    param_dtype=torch.bfloat16,
    reduce_dtype=torch.bfloat16,
    fp32_lm_head=False,
    torch_compile=True,
    mesh_prefix="default",
    requires_grad=True,
    hsdp_sharding_size=None,
)
```

Rules:

- `tp_size` and `ep_size` are parallel mesh sizes, not batch sizes.
- For MoE, `model_cfg.ep_size` must match `FSDPConfig(ep_size=...)`.
- `hsdp_sharding_size` asserts `ep_size == 1`.
- `cpu_offload=True` is an advanced memory workaround; verify on the exact Torch/model path.
- `param_dtype` and `reduce_dtype` accept `torch.dtype` or strings that deserialize to bfloat16/float16/float32.

## 6. `Float8Config` and FP8 modules

```python
from xtuner.v1.float8.config import Float8Config, ScalingGranularity

float8_cfg = Float8Config(
    scaling_granularity_gemm=ScalingGranularity.TILEWISE,
    scaling_granularity_grouped_gemm=ScalingGranularity.TILEWISE,
)
```

| Field | Meaning |
|---|---|
| `scaling_granularity_gemm` | Enables ordinary linear FP8 GEMM path when set. TILEWISE and TENSORWISE are the relevant operational choices. |
| `scaling_granularity_grouped_gemm` | Enables grouped-linear FP8 path; treat TILEWISE as the supported choice unless the target install proves more. |
| `enable_float8` | Property: true when either granularity is set. |
| `is_tilewise`, `is_tensorwise` | Convenience properties for handler logic. |

Selected runtime modules:

- `TileWiseFloat8Linear`
- `TensorWiseFloat8Linear`
- `TileWiseFloat8GroupedLinear`
- `Float8Handler`

FP8 requires real hardware/extension checks. `TileWiseFloat8GroupedLinear` asserts AdaptiveGEMM availability; the handler warns when device capability is below SM89.

## 7. Attention configs

`MHAConfig` signature fields:

```python
MHAConfig(
    num_attention_heads=...,
    num_key_value_heads=...,
    head_dim=...,
    dropout=0.0,
    qkv_bias=False,
    qk_norm=False,
    rms_norm_eps=1e-6,
    rms_norm_type="default",      # or "zero_centered"
    o_bias=False,
    sliding_window=-1,
    with_sink=False,
    with_gate=False,
    attn_impl="flash_attention",  # or "flex_attention", "eager_attention"
)
```

Operational notes:

- Use `flash_attention` only when FlashAttention is installed and ABI-compatible.
- `flex_attention` is XTuner's common fallback on CUDA when flash-attn is missing.
- `eager_attention` is useful for debugging and HF parity; `XTUNER_HF_IMPL=true` forces eager attention internally.
- VLM vision configs also expose `attn_impl` and perform the same flash-to-flex fallback.

## 8. Router and MoE config fields

`GreedyRouterConfig`:

```python
GreedyRouterConfig(
    scoring_func="softmax",
    router_scaling_factor=1.0,
    norm_topk_prob=True,
    use_grouped_router=False,
    router_n_groups=None,
)
```

`NoAuxRouterConfig` adds:

```python
NoAuxRouterConfig(
    scoring_func="sigmoid",
    router_scaling_factor=...,
    norm_topk_prob=True,
    n_group=...,
    topk_group=...,
    router_bias_update_speed=0.001,
    use_grouped_router=False,
    router_n_groups=None,
)
```

`MoEConfig` adds these backend fields on top of `TransformerConfig`:

| Field | Meaning |
|---|---|
| `n_routed_experts`, `n_shared_experts` | Routed/shared expert counts. |
| `num_experts_per_tok` | Top-k experts selected per token. |
| `first_k_dense_replace` | Dense layers before MoE replacement. |
| `moe_intermediate_size` | Expert MLP hidden size. |
| `ep_size` | Expert parallel size inside the model config. |
| `dispatcher` | `None`, `"all2all"`, `"deepep"`, or `"agrs"`. |
| `router` | `GreedyRouterConfig` or `NoAuxRouterConfig`. |
| `balancing_loss_cfg`, `z_loss_cfg`, `aux_loss_cfg` | MoE load-balance/accounting losses. |
| `return_router_results` | Debug router outputs; can increase memory. |
| `router_compute_dtype` | `"float32"` or `"native"`. |
| `moe_bias`, `gate_bias` | Expert/gate bias controls. |
| `mtp_config` | Multi-token prediction config for supported models. |
| `freeze_routers`, `router_async_offload` | Advanced router training/memory controls. |
| `embed_reshard_after_forward` | Embedding FSDP lifecycle behavior for MoE/compose models. |

## 9. Dispatcher API

```python
from xtuner.v1.module.dispatcher import build_dispatcher

dispatcher = build_dispatcher(
    dispatcher="all2all",          # None, "all2all", "deepep", "agrs"
    n_routed_experts=128,
    ep_group=process_group,
    training_dtype="bf16",         # or "fp8"
    generate_dtype="bf16",         # or "fp8"
)
```

Notes:

- `ep_group is None` or group size 1 returns the local/naive dispatcher.
- `dispatcher=None` with EP group size >1 defaults to `all2all`.
- `deepep` imports `deep_ep`/`deep_ep_cpp`; missing imports are optional-dependency failures, not XTuner config failures.
- `agrs` requires grouped router settings and an EP topology matching XTuner assertions.

## 10. Loss and optimizer config APIs

`CELossConfig`:

```python
CELossConfig(
    ignore_idx=-100,
    mode="eager",             # or "chunk"
    chunk_size=1024,
    loss_reduction="token",   # "token", "sample", or "square"
)
```

Use `mode="chunk"` to save memory for large vocab/sequence settings. `mode="eager"` is simpler and useful for parity debugging.

`AdamWConfig`:

```python
AdamWConfig(
    lr=1e-5,
    max_grad_norm=1.0,
    skip_grad_norm_threshold=None,
    weight_decay=0.01,
    betas=(0.9, 0.95),
    eps=1e-8,
    foreach=None,
    swap_optimizer=False,
)
```

`LRConfig`:

```python
LRConfig(
    lr_type="constant",  # "cosine", "linear", or "constant"
    warmup_ratio=0.03,
    lr_min=1e-6,
)
```

## 11. Safe snippets

### Alias sanity

```python
from xtuner.v1.model import get_model_config

for alias in ["qwen3-8B", "qwen3-moe-30BA3", "intern-s1-mini"]:
    cfg = get_model_config(alias)
    print(alias, type(cfg).__name__ if cfg is not None else "MISSING")
```

### Dense backend config

```python
from xtuner.v1.config import FSDPConfig
from xtuner.v1.model import Qwen3Dense8BConfig

model_cfg = Qwen3Dense8BConfig(compile_cfg=False)
fsdp_cfg = FSDPConfig(tp_size=1, ep_size=1, recompute_ratio=1.0)
```

### MoE backend config

```python
from xtuner.v1.config import FSDPConfig
from xtuner.v1.model import Qwen3MoE30BA3Config

model_cfg = Qwen3MoE30BA3Config(compile_cfg=False, ep_size=8, dispatcher="all2all")
fsdp_cfg = FSDPConfig(tp_size=1, ep_size=8, recompute_ratio=1.0)
```

### FP8 config-only setup

```python
from xtuner.v1.float8.config import Float8Config, ScalingGranularity
from xtuner.v1.model import Qwen3MoE30BA3Config

float8_cfg = Float8Config(
    scaling_granularity_gemm=ScalingGranularity.TILEWISE,
    scaling_granularity_grouped_gemm=ScalingGranularity.TILEWISE,
)
model_cfg = Qwen3MoE30BA3Config(float8_cfg=float8_cfg)
```

This snippet only proves config construction. Run backend probes and kernel/native tests before claiming FP8 training works.

### Backend checker invocation

From the sub-skill directory:

```bash
python scripts/check_xtuner_backend.py --json --check-optional
python scripts/check_xtuner_backend.py --expect-cuda
```
