# Inference Workflows

## Inspect the Installed Surface

Run the bundled inspector before relying on field names from docs or examples:

```bash
python scripts/inspect_inference_config.py --check-modules
```

Use the output to confirm the installed `init_inference` signature, Pydantic field names, aliases, and whether optional modules such as `transformers`, `triton`, inference v2, or module injection helpers import cleanly.

## Basic Kernel Injection

Use kernel injection when the model architecture has a built-in DeepSpeed policy and the user wants optimized transformer inference kernels:

```python
import deepspeed
import torch

engine = deepspeed.init_inference(
    model,
    tensor_parallel={"tp_size": world_size},
    dtype=torch.float16,
    replace_with_kernel_inject=True,
)
model = engine.module
```

Equivalent alias form:

```python
engine = deepspeed.init_inference(model, config={"kernel_inject": True, "tp": {"tp_size": world_size}})
```

Prefer canonical field names in new guidance (`replace_with_kernel_inject`, `tensor_parallel`) and mention aliases only when adapting existing configs.

## Manual Injection Policy for Unsupported Architectures

Use manual injection when the model lacks a built-in kernel policy but has transformer blocks whose output projections can be tensor-parallelized:

```python
from transformers.models.t5.modeling_t5 import T5Block

engine = deepspeed.init_inference(
    model,
    tensor_parallel={"tp_size": world_size},
    dtype=torch.float32,
    injection_policy={T5Block: ("SelfAttention.o", "EncDecAttention.o", "DenseReluDense.wo")},
)
```

Checklist:

- Identify the repeated block class, not the top-level model class.
- Use child module-name suffixes from `model.named_modules()`.
- Do not combine manual `injection_policy` with `replace_with_kernel_inject=True`.
- If DeepSpeed raises that a policy layer is not valid, print or inspect layer names and update suffixes.

## AutoTP Without Kernel Injection

Use AutoTP when `tensor_parallel.tp_size > 1`, there is no manual policy, and kernel injection is off:

```python
engine = deepspeed.init_inference(
    model,
    tensor_parallel={"tp_size": world_size},
    dtype="fp16",
    replace_with_kernel_inject=False,
)
```

DeepSpeed then tries to infer injection policies through `AutoTP.tp_parser(model)`. If inference fails, either switch to kernel injection for a supported model or provide a manual `injection_policy`.

## Checkpoint MP Reshaping

When inference TP degree differs from training MP degree:

```python
engine = deepspeed.init_inference(
    model,
    checkpoint="checkpoint.json",
    training_mp_size=training_mp_size,
    tensor_parallel={"tp_size": inference_tp_size},
    dtype=torch.float16,
    replace_with_kernel_inject=True,
    save_mp_checkpoint_path="reshaped_checkpoint",
)
```

Use `save_mp_checkpoint_path` only when the user wants to cache the reshaped checkpoint. A checkpoint JSON may contain a DeepSpeed checkpoint path or a list of Megatron-style MP checkpoint files. Keep generated skills self-contained; do not embed local checkpoint paths in reusable guidance.

## Quantized Inference

For current APIs, pair int8 dtype with `quant`, not the older `quantization_setting` name:

```python
engine = deepspeed.init_inference(
    model,
    dtype=torch.int8,
    tensor_parallel={"tp_size": world_size},
    quant={
        "enabled": True,
        "weight": {"enabled": True, "num_bits": 8, "q_type": "symmetric", "q_groups": 1},
    },
)
```

If adapting an old example using `quantization_setting=(groups, extra_mlp_grouping)`, explain that the installed `DeepSpeedInferenceConfig` exposes `quant`; inspect the exact installed fields before rewriting the config.

## CUDA Graph and Triton Choices

- `enable_cuda_graph=True` requires CUDA and PyTorch support. `InferenceEngine` asserts CUDA graph is not supported when `tensor_parallel.tp_size > 1`.
- `use_triton=True` validates that DeepSpeed detected Triton import support; otherwise config validation raises a Triton installation error.
- `triton_autotune=True` can improve later performance but increases first-run startup time.

## Choosing v1 vs v2/FastGen

Choose classic `init_inference` when the user is integrating a PyTorch/Hugging Face model directly and asks about `DeepSpeedInferenceConfig`, kernel injection, manual policies, AutoTP, checkpoint reshaping, or MoQ-style inference quantization.

Route users to DeepSpeed-FastGen/MII concepts when they ask for the latest high-throughput text generation serving path. Treat files under `deepspeed.inference.v2` as FastGen internals unless the user is modifying DeepSpeed itself.

## Hybrid Engine Distinction

If a user asks whether `hybrid_engine` replaces `init_inference`, answer no. Hybrid engine is enabled through training config and `deepspeed.initialize`; it creates `DeepSpeedHybridEngine` for training workflows that temporarily use inference-style containers during generation. `init_inference` returns `InferenceEngine` and is the inference entrypoint.
