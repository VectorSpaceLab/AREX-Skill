# FSDP-QLoRA

FSDP-QLoRA combines 4-bit base model quantization, LoRA adapters, and Fully Sharded Data Parallel training. Use it when a user wants distributed QLoRA training with sharded parameters, gradients, and optimizer states.

## Core Constraint

FSDP needs wrapped modules to have compatible floating storage dtypes. bitsandbytes 4-bit weights are logically quantized, but FSDP planning is controlled through the storage dtype exposed by `bnb_4bit_quant_storage` in `transformers.BitsAndBytesConfig`.

The important alignment rule is:

```python
import torch
from transformers import BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_storage=torch.bfloat16,
)

model_kwargs = {
    "quantization_config": quantization_config,
    "torch_dtype": torch.bfloat16,
}
```

Set `torch_dtype` to match `bnb_4bit_quant_storage` so FSDP can wrap quantized and non-quantized layers consistently. If storage dtypes do not match, quantized linear layers may be wrapped separately or fail to shard as expected.

## Dtype Roles

- `bnb_4bit_quant_type`: choose `"nf4"` for common QLoRA flows; `"fp4"` is also supported by lower-level bitsandbytes modules.
- `bnb_4bit_compute_dtype`: dtype used for computation after unpacking/dequantization; bfloat16 is preferred when hardware supports it.
- `bnb_4bit_quant_storage`: storage dtype visible to FSDP; use a floating dtype such as bfloat16, float16, or float32 for FSDP compatibility.
- `torch_dtype`: model dtype passed during loading; align with quant storage for FSDP wrapping.

## Training Skeleton

A high-level FSDP-QLoRA plan usually includes:

1. Install current `bitsandbytes`, `transformers`, `accelerate`, `peft`, and the trainer stack.
2. Build a 4-bit NF4 `BitsAndBytesConfig` with matching `bnb_4bit_quant_storage` and `torch_dtype`.
3. Load the base model with `AutoModelForCausalLM.from_pretrained(..., quantization_config=..., torch_dtype=...)`.
4. Prepare the model with `prepare_model_for_kbit_training`.
5. Add LoRA adapters with `target_modules="all-linear"` when supported, or architecture-specific linear target names.
6. Launch distributed training through Accelerate or `torchrun`; do not run FSDP as an ordinary single-process script unless intentionally testing a minimal case.

## State-Dict Caveats

Repo tests cover a minimal FSDP state-dict save flow using a frozen 4-bit base layer plus a trainable adapter. Practical implications:

- Frozen quantized base parameters may need to be ignored by FSDP flattening because integer-like quantized parameters cannot be flattened like ordinary floating parameters.
- Use `use_orig_params=True` when planning FSDP around mixed frozen quantized parameters and trainable adapters.
- Full state-dict saving with CPU offload should preserve quantization metadata such as `absmax` and `quant_map` as well as adapter weights.
- Missing quantization metadata in a checkpoint is a serious save/load issue, not just a naming mismatch.
- FSDP scripts must initialize a distributed process group and select an appropriate backend such as `nccl` for CUDA, `xccl` for XPU, or `gloo` for CPU-style tests.

## Planning Checklist

- Hardware: enough devices for FSDP; backend supported by the local PyTorch build.
- Dtypes: `bnb_4bit_quant_storage` and model `torch_dtype` aligned.
- Quantization: `load_in_4bit=True`, `bnb_4bit_quant_type="nf4"`, double quantization considered.
- PEFT: LoRA adapter target modules verified for the model architecture.
- Launch: Accelerate or `torchrun` config owns process count, device placement, and FSDP policy.
- Checkpoint: state dict strategy preserves adapter weights and bitsandbytes quantization metadata.
- Boundaries: direct `bitsandbytes.nn.Linear4bit` replacement details belong in `quantized-modules-functions`; installation/backend failures belong in `installation-diagnostics`.
