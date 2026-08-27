# Troubleshooting Transformers Integrations

## Missing Optional Dependencies

Symptoms:

- `ModuleNotFoundError: No module named 'transformers'`
- `ImportError` mentioning Accelerate, PEFT, or Diffusers
- `BitsAndBytesConfig` cannot be imported from `bitsandbytes`

Actions:

- Import `BitsAndBytesConfig` from `transformers`, not `bitsandbytes`.
- Install `transformers` and `accelerate` for quantized model loading.
- Install `peft` for QLoRA preparation and adapter creation.
- Install `diffusers` only for Diffusers-specific tasks.
- Use `scripts/transformers-bnb-config-check.py --mode qlora --require-peft` for a no-download import/config check.

## Model Download, Network, or Credentials

Symptoms:

- `from_pretrained` fails with HTTP, auth, gated repository, or missing file errors.
- CI blocks outbound network.
- A tokenizer load fails before quantization is reached.

Actions:

- Separate config validation from model loading; validate `BitsAndBytesConfig` without downloads first.
- Use a local model path or pre-populated cache when network is disallowed.
- Confirm Hugging Face token, gated model access, license acceptance, and `trust_remote_code` policy.
- Do not diagnose download failures as bitsandbytes kernel failures until a local model load reaches quantization.

## Device Map Unavailable

Symptoms:

- `device_map="auto"` is rejected or ignored.
- Errors mention missing Accelerate integration or unsupported dispatch.

Actions:

- Ensure `accelerate` is installed and compatible with Transformers.
- Use an explicit `device_map` or single-device load when auto dispatch is unavailable.
- For CPU-only validation, avoid loading the model and run the config-check script instead.

## Backend or Device Not Visible

Symptoms:

- bitsandbytes imports but quantized execution fails on the expected accelerator.
- Errors mention unavailable CUDA/XPU/HPU/MPS backend, missing native library, or incompatible PyTorch build.

Actions:

- Route to `installation-diagnostics` for `python -m bitsandbytes`, PyTorch device visibility, and native library checks.
- Do not fix backend visibility by changing `BitsAndBytesConfig` unless the chosen mode is unsupported on that backend.
- Remember that config construction can pass on CPU while execution requires a supported runtime path.

## Unsupported or Poor Dtype Choice

Symptoms:

- bfloat16 errors on hardware without bfloat16 support.
- float16 numerical instability during training.
- Slow 4-bit execution with default float32 compute.

Actions:

- Choose `bnb_4bit_compute_dtype=torch.bfloat16` only when supported by the accelerator.
- Consider `torch.float16` for compatible CUDA inference when bfloat16 is unavailable, while monitoring stability.
- Keep float32 for compatibility checks or conservative CPU-style validation.
- For FSDP-QLoRA, align `bnb_4bit_quant_storage` with model `torch_dtype`; this is separate from compute dtype.

## OOM and Offload Decisions

Symptoms:

- Model load OOMs despite 8-bit or 4-bit settings.
- Auto device mapping places too much on one device.
- CPU offload is unexpectedly slow.

Actions:

- Provide `max_memory` per device when using `device_map="auto"`.
- Use a smaller model, shorter sequence length, lower batch size, or explicit device map.
- Treat CPU offload as a memory escape hatch with performance cost.
- For training, consider gradient checkpointing, paged optimizers, LoRA-only updates, or FSDP-QLoRA planning.

## Confusing Transformers Config with bitsandbytes APIs

Symptoms:

- User tries `bitsandbytes.BitsAndBytesConfig` or expects `load_in_4bit` in direct `bnb.nn.Linear4bit` construction.
- User mixes direct layer replacement with `from_pretrained` quantization.

Actions:

- Use `transformers.BitsAndBytesConfig` for Hugging Face model loading.
- Use `bitsandbytes.nn` modules only for direct PyTorch module replacement; route those tasks to `quantized-modules-functions`.
- Keep optimizer memory-saving tasks in `optimizers-training`.

## FSDP State-Dict and Quant State Problems

Symptoms:

- FSDP save/load misses `absmax`, `quant_map`, or other quantization metadata.
- Errors mention `Params4bit` attributes during state-dict traversal.
- FSDP cannot flatten quantized/frozen base parameters.

Actions:

- Confirm `bnb_4bit_quant_storage` and model `torch_dtype` match.
- Use `use_orig_params=True` and ignore frozen quantized base parameters when direct FSDP wrapping requires it.
- Verify state dicts include both adapter weights and quantization metadata.
- Treat missing quant state as checkpoint corruption or integration mismatch; do not strip those keys.
