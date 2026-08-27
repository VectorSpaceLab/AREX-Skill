# Training And Integration Troubleshooting

Use this when PEFT adapter construction succeeds but training integration, launcher behavior, dtype handling, distributed saving, or optional backend setup fails.

## Examples Fail After Copying

Symptoms:

- Import errors from `transformers`, `accelerate`, `trl`, `diffusers`, or `bitsandbytes`.
- Renamed trainer arguments, dataset fields, tokenizer/chat-template APIs, or Diffusers pipeline components.
- Shell scripts refer to unavailable model IDs, datasets, GPUs, hub credentials, or precision settings.

Actions:

1. Confirm package versions for `peft`, `torch`, `transformers`, and `accelerate`; add `trl`, `diffusers`, `bitsandbytes`, or `deepspeed` only as needed.
2. Run parser/help or config construction paths before training. Do not use full downloads/training as the first validation step.
3. Replace example defaults with explicit user-provided model, dataset, output directory, precision, and hub-push settings.
4. Keep the example's PEFT placement and distributed save pattern intact unless the upstream trainer API changed.
5. If an upstream API moved, adapt the framework call site rather than changing PEFT config semantics.

## `ValueError: Attempting to unscale FP16 gradients`

Likely cause: trainable adapter parameters are fp16 while AMP expects trainable parameters suitable for gradient scaling.

Fixes:

- Prefer `bf16` if hardware supports it.
- Keep PEFT default adapter autocasting behavior unless there is a strong reason to disable it.
- After wrapping, ensure trainable parameters are fp32 before `Trainer(fp16=True)` if needed:

```python
peft_model = get_peft_model(base_model, peft_config)
for param in peft_model.parameters():
    if param.requires_grad:
        param.data = param.data.float()
```

- Or use PEFT mixed-precision helpers such as `cast_mixed_precision_params` when appropriate for the method.
- Re-check base model dtype, adapter dtype, quantization compute dtype, and trainer precision as one system.

## Gradient Checkpointing Uses Too Much Memory Or Crashes

Checks:

- Set `model.config.use_cache = False` for causal LM training with checkpointing.
- Pass `gradient_checkpointing_kwargs={"use_reentrant": ...}` deliberately; single-GPU QLoRA and multi-GPU QLoRA examples may need different values.
- For TRL SFT, ensure the trainer version still accepts the same checkpointing argument names.
- For Unsloth or custom optimized kernels, verify whether the optimization replaces or disables normal checkpointing.
- Reduce sequence length or batch size to separate activation-memory pressure from adapter/backend bugs.

## FSDP Save Produces Unloadable Or Sharded-Only Adapters

Likely cause: the trainer saved while FSDP still used a sharded state dict, or PEFT adapter parameters were wrapped with frozen base parameters incorrectly.

Fixes:

- Use `fsdp_auto_wrap_policy(trainer.model)` from PEFT when FSDP is active.
- Use `fsdp_use_orig_params: false` for memory-efficient PEFT FSDP.
- Before final save, set FSDP state dict type to `FULL_STATE_DICT` through the Accelerate FSDP plugin, then call `trainer.save_model()`.
- Save only from the trainer/accelerator-controlled main process.
- Test reload with `PeftConfig.from_pretrained(...)` and `PeftModel.from_pretrained(base_model, adapter_dir)` after training.

## DeepSpeed ZeRO-3 Does Not Save Or Resume Correctly

Checks:

- Match `gradient_accumulation_steps` in DeepSpeed/Accelerate config and training args.
- Use `zero3_init_flag: true` for large ZeRO-3 model initialization when required.
- Avoid manual per-rank `model.save_pretrained(...)`; use `trainer.save_model()` or DeepSpeed-aware utilities.
- Decide whether you need adapter-only output or a 16-bit full model state, then set save flags consistently.
- For resume, pass the same launcher config and checkpoint path; mismatched ZeRO stage or process count can break state reconstruction.

## Quantized Training Fails Before PEFT Training Starts

Common causes:

- `bitsandbytes`, `gptqmodel`, or backend CUDA support is missing.
- The quantization config uses a dtype unsupported by the hardware or distributed backend.
- `prepare_model_for_kbit_training` was skipped before PEFT wrapping.
- FSDP is combined with bitsandbytes 8-bit, which PEFT examples call out as incompatible.
- A prequantized model is required but an unquantized model ID was passed, or vice versa.

Actions:

- Reproduce a tiny model load with the same quantization config first.
- Route LoRA/QLoRA method parameter questions to `lora-and-quantization`.
- Keep adapter save separate from merge/export for quantized backends that cannot merge safely.

## Offload Causes Device Or Dtype Errors

Actions:

- Confirm which parameters are trainable and where they live after accelerator preparation.
- Avoid mixing `device_map="auto"` model parallel placement with distributed launch unless the framework explicitly supports the combination.
- Treat CPU/NVMe offload as a throughput and correctness tradeoff; test a tiny forward/backward pass before full training.
- If runtime offload keeps frozen base weights on CPU, verify adapter parameters move to the intended training device.

## `torch.compile` Fails Or Gives Suspicious Results

Actions:

- Load and add all adapters before calling `torch.compile`.
- Avoid loading, deleting, switching, or hotswapping adapters after compilation unless following a tested PEFT hotswap flow.
- Validate loss/logits on a tiny fixed batch before and after compilation.
- Disable compilation first when debugging distributed, quantized, or adapter-routing failures.
- Expect dynamic adapter features to cause graph breaks or limited speedups.

## Optional Dependency Errors

Map the missing package to the workflow:

- `trl`: SFT training and chat/instruction examples.
- `diffusers`: DreamBooth, Stable Diffusion, Flux, ControlNet, and image-generation training.
- `bitsandbytes`: 4-bit/8-bit QLoRA-style loading.
- `deepspeed`: ZeRO training.
- `gptqmodel`: GPTQModel quantized examples.
- `datasets`: example dataset loading.

If the user does not need that workflow, remove the optional integration path instead of installing broad extras.
