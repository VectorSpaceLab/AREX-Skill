# Core API reference

## Package imports

Use package imports rather than source-checkout paths:

```python
import torch
from megatron.core.transformer.transformer_config import TransformerConfig
from megatron.core.models.gpt.gpt_model import GPTModel
from megatron.core.models.gpt.gpt_layer_specs import get_gpt_layer_local_spec
from megatron.core import parallel_state
from megatron.core.distributed import DistributedDataParallel, DistributedDataParallelConfig
```

## `TransformerConfig`

`TransformerConfig` is the central dataclass for transformer architecture and model-parallel behavior. It inherits model-parallel fields such as tensor, pipeline, context, expert, sequence-parallel, and communication settings. Typical minimal construction for local CPU initialization:

```python
cfg = TransformerConfig(
    num_layers=2,
    hidden_size=128,
    num_attention_heads=4,
    use_cpu_initialization=True,
    pipeline_dtype=torch.float32,
)
```

Common architecture fields:

| Field | Purpose |
|---|---|
| `num_layers` | Transformer/hybrid layer count. |
| `hidden_size` | Hidden dimension. |
| `num_attention_heads` | Attention heads; must be compatible with TP. |
| `ffn_hidden_size` | MLP hidden dimension; defaults derive from `hidden_size` when omitted. |
| `context_parallel_size` | Split long sequence dimension across ranks. |
| `tensor_model_parallel_size` | Split tensor dimensions within layers. |
| `pipeline_model_parallel_size` | Split layer stack across pipeline stages. |
| `expert_model_parallel_size` | Split MoE experts across ranks. |
| `sequence_parallel` | Often required/recommended when combining TP with MoE/large models. |
| `pipeline_model_parallel_layout` | Optional explicit pipeline/hybrid layer layout string/list/object. |

## `GPTModel`

Current installed signature shape:

```python
GPTModel(
    config: TransformerConfig,
    transformer_layer_spec,
    vocab_size: int,
    max_sequence_length: int,
    pre_process: bool = True,
    post_process: bool = True,
    fp16_lm_cross_entropy: bool = False,
    parallel_output: bool = True,
    share_embeddings_and_output_weights: bool = False,
    position_embedding_type: "learned_absolute|rope|mrope|yarn|none" = "learned_absolute",
    rotary_percent: float = 1.0,
    rotary_base: int = 10000,
    rope_scaling: bool = False,
    rope_scaling_factor: float = 8.0,
    scatter_embedding_sequence_parallel: bool = True,
    seq_len_interpolation_factor = None,
    mtp_block_spec = None,
    pg_collection = None,
    vp_stage = None,
)
```

Important behaviors:

- The constructor logs that `GPTModel` is deprecated and points users to HybridModel migration.
- Use a layer spec such as `get_gpt_layer_local_spec()` for local/Torch components or TE-backed specs when the environment supports TransformerEngine.
- `pre_process` and `post_process` control embedding/output ownership under pipeline parallelism.
- `parallel_output=True` leaves logits sharded across tensor-parallel ranks.
- `pg_collection` lets callers pass process groups explicitly; prefer this over global process-group reads in new `megatron/core` library code.

## Distributed wrappers

For Megatron Core training loops, wrap a model with `DistributedDataParallel` and a `DistributedDataParallelConfig` when gradients must be synchronized through Megatron's buffers and finalization helpers.

Conceptual pattern:

```python
ddp_cfg = DistributedDataParallelConfig(
    grad_reduce_in_fp32=False,
    overlap_grad_reduce=False,
    use_distributed_optimizer=False,
)
model = DistributedDataParallel(config=cfg, ddp_config=ddp_cfg, module=model)
```

Use Megatron-FSDP when model/optimizer state sharding is required; see [parallelism-reference.md](parallelism-reference.md).

## Process groups

- Initialize Torch distributed before Megatron model-parallel groups.
- Initialize Megatron groups with tensor/pipeline/context/expert sizes that multiply into the intended world size.
- Destroy model-parallel state between tests or independent runs to avoid stale global state.
- In `megatron/core` production code, prefer accepting `ProcessGroupCollection` or explicit `torch.distributed.ProcessGroup` objects rather than adding new direct reads from global `parallel_state`.
