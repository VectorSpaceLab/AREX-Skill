# Distributed And Backend Guidance

This reference covers PEFT integration decisions for Accelerate, FSDP, DeepSpeed, quantized training, offload, CPU fallback, and precision. It is not a replacement for method-specific configuration guidance.

## Backend Selection

| Backend | Use when | Main PEFT caveats |
| --- | --- | --- |
| `single-gpu` | Debugging, small models, QLoRA on one GPU, minimal moving parts | Still verify adapter trainability, dtype, and final adapter save. |
| `cpu` | Parser/config smoke checks or tiny development tests | Real training is slow; quantization/GPU-only packages may not work. |
| `fsdp` | Multi-GPU sharding with PyTorch/Accelerate | Use PEFT auto-wrap policy, `fsdp_use_orig_params: false` for memory savings, and full state dict before final adapter save. |
| `deepspeed` | ZeRO sharding/offload or large-model multi-GPU training | Align Accelerate config and training args; save through trainer/accelerator; check ZeRO stage and offload choices. |

## Accelerate Launch Pattern

Use `accelerate config --config_file <config.yaml>` to create a backend config, then launch with `accelerate launch --config_file <config.yaml> train.py ...`. Keep these synchronized:

- `num_processes`, `num_machines`, `machine_rank`, rendezvous settings.
- `mixed_precision` in Accelerate and `fp16`/`bf16` in trainer arguments.
- `gradient_accumulation_steps` in launcher/plugin config and training arguments.
- backend-specific save settings such as FSDP state dict type or DeepSpeed ZeRO-3 save behavior.

When debugging, first run the same script on a tiny local dataset or parser-only path without distributed launch, then add `accelerate launch`.

## FSDP With PEFT

PEFT + FSDP needs wrapper boundaries that separate trainable adapter parameters from frozen base parameters.

Checklist:

- Use an Accelerate FSDP config with `distributed_type: FSDP`.
- Set `fsdp_use_orig_params: false` when the goal is real GPU memory savings.
- Use `fsdp_auto_wrap_policy(trainer.model)` from `peft.utils.other` when the trainer exposes an FSDP plugin.
- For QLoRA + FSDP, use CPU RAM efficient loading and backend-compatible quantization storage dtype.
- Before final `trainer.save_model()`, switch FSDP to a full state dict if the adapter must load normally outside the sharded training job.
- Do not assume bitsandbytes 8-bit works with FSDP; PEFT examples call out incompatibility for that path.

Typical trainer hook:

```python
from peft.utils.other import fsdp_auto_wrap_policy

if getattr(trainer.accelerator.state, "fsdp_plugin", None):
    fsdp_plugin = trainer.accelerator.state.fsdp_plugin
    fsdp_plugin.auto_wrap_policy = fsdp_auto_wrap_policy(trainer.model)

if trainer.is_fsdp_enabled:
    trainer.accelerator.state.fsdp_plugin.set_state_dict_type("FULL_STATE_DICT")
trainer.save_model()
```

## DeepSpeed With PEFT

DeepSpeed ZeRO stages can work with PEFT LoRA and bitsandbytes-based QLoRA workflows, including ZeRO-3, when the surrounding stack supports the selected versions and dtypes.

Checklist:

- Use an Accelerate config with `distributed_type: DEEPSPEED`.
- Choose ZeRO stage deliberately: ZeRO-1 shards optimizer state, ZeRO-2 adds gradients, ZeRO-3 adds parameters.
- For ZeRO-3 large model initialization, use `zero3_init_flag: true` when required by the workflow.
- Keep `gradient_accumulation_steps` consistent between DeepSpeed/Accelerate config and trainer arguments.
- Use `zero3_save_16bit_model: true` only when you need full model state behavior; adapter-only saves should still be verified.
- Avoid rank-local manual saves; use `trainer.save_model()` or Accelerate/DeepSpeed-aware helpers.
- Treat CPU/NVMe offload as a memory tradeoff that can introduce dtype, checkpointing, and throughput issues.

## Quantized Distributed Training

PEFT can train adapters on quantized base models, but distributed compatibility is backend-specific.

Rules:

- For bitsandbytes 4-bit/8-bit training, load with a Transformers quantization config, then call `prepare_model_for_kbit_training` before `get_peft_model`.
- For QLoRA-style LoRA, target all linear layers unless a method-specific sub-skill recommends a narrower target.
- For FSDP + QLoRA, align `bnb_4bit_compute_dtype`, `bnb_4bit_quant_storage_dtype`, mixed precision, and `fsdp_offload_params` with the selected hardware.
- For DeepSpeed + QLoRA ZeRO-3, use current compatible versions of `bitsandbytes`, `accelerate`, `transformers`, `trl`, and `peft`; older stacks often fail in launcher or dtype setup before PEFT code is reached.
- For GPTQModel-based FSDP examples, use a model already quantized with GPTQModel and avoid known-bad Transformers versions called out by the workflow owner.
- Save adapters separately when the quantization backend cannot safely merge adapter deltas into quantized base weights.

## Precision And Adapter Dtype

Common choices:

- Prefer `bf16` on supported modern accelerators because it avoids many FP16 overflow/unscale problems.
- If using `fp16` automatic mixed precision, ensure trainable adapter parameters are not left in raw fp16 when the optimizer/scaler expects fp32 trainable weights.
- PEFT generally promotes adapter weights to fp32 by default where appropriate. Only disable this with `autocast_adapter_dtype=False` after understanding the stability tradeoff.
- Keep base model dtype, quantization compute dtype, adapter dtype, and trainer mixed precision aligned.

## Offload And Gradient Checkpointing

Offload and checkpointing reduce memory but increase constraints:

- Gradient checkpointing often requires `model.config.use_cache = False` for causal LMs.
- Reentrant checkpointing differs by workflow; test the exact single-GPU, multi-GPU, FSDP, or QLoRA path.
- CPU/NVMe offload can expose slow parameter movement, dtype casts, or missing device placement for trainable adapters.
- Runtime offload features that keep base weights on CPU should be checked with a tiny forward/backward pass before full training.

## Optional Dependency Matrix

Install only the optional packages the workflow needs:

- `trl`: SFTTrainer and instruction-tuning examples.
- `diffusers`: Stable Diffusion, DreamBooth, ControlNet, Flux, and related diffusion examples.
- `bitsandbytes`: 4-bit/8-bit loading and QLoRA-style training on supported hardware.
- `deepspeed`: DeepSpeed ZeRO training through Accelerate or Trainer.
- `gptqmodel`: GPTQModel quantized model examples.
- `accelerate`: launcher/distributed orchestration; PEFT training examples assume it for FSDP/DeepSpeed.
- `datasets`: most example datasets and SFT scripts.

Missing optional packages should be handled as environment setup issues, not as PEFT adapter bugs.
