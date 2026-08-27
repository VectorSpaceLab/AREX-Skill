---
name: transformers-integrations
description: "Use bitsandbytes through Hugging Face Transformers, Diffusers,
  PEFT, and Accelerate for LLM.int8 inference, 4-bit/NF4 loading, QLoRA
  preparation, and FSDP-QLoRA planning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Transformers Integrations

Use this sub-skill when the task is about loading or preparing models through Hugging Face ecosystem APIs with bitsandbytes quantization. The key API is usually `transformers.BitsAndBytesConfig`; it is provided by Transformers, not by the `bitsandbytes` Python package.

## Route Here

- Build `BitsAndBytesConfig` for `load_in_8bit`, `load_in_4bit`, NF4, double quantization, compute dtype, or quantized storage dtype.
- Load a model with `AutoModelForCausalLM.from_pretrained(..., quantization_config=..., device_map=...)`.
- Prepare QLoRA with PEFT using `prepare_model_for_kbit_training`, `LoraConfig`, and `get_peft_model`.
- Plan FSDP-QLoRA, especially `bnb_4bit_quant_storage` and dtype alignment.
- Explain Diffusers, Accelerate, or Transformers integration decisions without direct layer replacement.
- Validate a quantization config in CI without downloading model weights.

## Route Elsewhere

- For install, import, missing native library, backend visibility, `python -m bitsandbytes`, or CUDA/XPU/HPU/MPS/CPU diagnostics, use `installation-diagnostics`.
- For direct `bitsandbytes.nn.Linear8bitLt`, `Linear4bit`, `Params4bit`, `QuantState`, or low-level functional APIs, use `quantized-modules-functions`.
- For standalone 8-bit or paged optimizer training loops, `Trainer(optim=...)`, or `bitsandbytes.optim`, use `optimizers-training`.

## Start Points

- Read `references/integration-workflows.md` for 8-bit inference, 4-bit/NF4 loading, QLoRA, Diffusers/Accelerate notes, validation, and model-download safety.
- Read `references/fsdp-qlora.md` for FSDP-QLoRA dtype, storage, sharding, and state-dict caveats.
- Read `references/troubleshooting.md` when integrations fail at import, model loading, device mapping, dtype, offload, or distributed save time.
- Run `scripts/transformers-bnb-config-check.py --mode qlora` to validate optional dependency imports and print no-download config snippets.

## Working Rules

- Separate config construction from execution: `BitsAndBytesConfig` can often be constructed on CPU-only CI, but actual quantized model loading may require a compatible accelerator, memory plan, model access, and network/cache availability.
- Prefer `quantization_config=BitsAndBytesConfig(...)` over legacy direct `load_in_8bit=True` or `load_in_4bit=True` arguments to `from_pretrained`.
- Treat model IDs, tokens, gated repositories, and remote code as deployment inputs; never assume downloads are allowed.
- Keep backend failures routed to installation diagnostics before changing model-loading code.
