# Integration Workflows

This reference covers using bitsandbytes through Hugging Face libraries. The `BitsAndBytesConfig` class is a Transformers-side configuration object. The `bitsandbytes` package supplies quantized kernels/modules used underneath model loading, but user-facing model quantization settings usually live in Transformers, Accelerate, PEFT, or Diffusers.

## Dependency Decisions

Install the integration stack that matches the task:

- Inference with Transformers: `bitsandbytes`, `transformers`, `accelerate`, and `torch`.
- QLoRA with PEFT: add `peft`; training scripts often also use `datasets`, `trl`, or a trainer framework.
- Accelerate-native quantization: use `accelerate.utils.BnbQuantizationConfig` and `load_and_quantize_model` for non-Transformers model flows.
- Diffusers quantization: use Diffusers' bitsandbytes integration patterns for supported pipelines/components; confirm component support before assuming every pipeline can be quantized.

Do not import `BitsAndBytesConfig` from `bitsandbytes`; import it from `transformers`.

## 8-Bit Inference

Use LLM.int8 when the user wants lower memory inference while preserving quality. Prefer `quantization_config`:

```python
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(load_in_8bit=True)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=quantization_config,
    device_map="auto",
)
```

Operational notes:

- `device_map="auto"` requires Accelerate support and an environment where Transformers can infer devices.
- For constrained memory, pass an explicit `max_memory` map instead of relying on all visible memory.
- Legacy examples may pass `load_in_8bit=True` directly to `from_pretrained`; modern agent output should prefer `BitsAndBytesConfig`.
- Running generation also needs tokenizer/model downloads or a populated local cache, plus credentials for gated models.

## 4-Bit and NF4 Loading

Use 4-bit loading for larger memory savings or as the base of QLoRA. NF4 is the common QLoRA quantization type:

```python
import torch
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=quantization_config,
    device_map="auto",
)
```

Dtype decisions:

- `bnb_4bit_compute_dtype=torch.bfloat16` is preferred when hardware supports bfloat16.
- `torch.float16` may be faster on some CUDA devices but can be less numerically stable.
- The default float32 compute path is broadly compatible but slower and larger.
- On CPU-only or unsupported hardware, config construction can still be valid while actual model execution may be slow, unsupported, or impossible for the chosen stack.

## QLoRA with PEFT

A typical PEFT QLoRA flow is:

```python
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=quantization_config,
    device_map="auto",
)
model = prepare_model_for_kbit_training(model)
peft_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules="all-linear",
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)
model = get_peft_model(model, peft_config)
```

Planning notes:

- `prepare_model_for_kbit_training` is a PEFT helper for Transformers models.
- `target_modules="all-linear"` is a robust QLoRA default when PEFT supports it for the architecture; otherwise identify architecture-specific projection names.
- Keep adapter training concerns separate from base model quantization. The frozen quantized base and trainable LoRA adapters have different state and checkpoint expectations.

## Accelerate Workflows

Accelerate can quantize custom PyTorch models using `accelerate.utils.BnbQuantizationConfig` and `load_and_quantize_model`. Choose this route when the model is not loaded through a standard Transformers `AutoModel...from_pretrained` call.

Typical decisions mirror Transformers config: `load_in_4bit`, `bnb_4bit_compute_dtype`, `bnb_4bit_use_double_quant`, `bnb_4bit_quant_type`, and `device_map`. Validate that the weights location is local or accessible before planning execution.

## Diffusers Mention

Diffusers has bitsandbytes quantization integrations for supported components. Treat Diffusers as a library-specific integration surface: use its quantization documentation and supported component list, then apply the same dependency, device, dtype, and model-download checks used for Transformers. Do not assume CausalLM examples transfer directly to diffusion pipelines.

## Torch Compile Constraints

Quantized Transformers models can be experimented with under `torch.compile`, but compile success is model-, PyTorch-, backend-, and graph-shape-dependent. Keep compile optional:

- First prove the uncompiled quantized load/generation path.
- Set `torch.set_float32_matmul_precision("high")` only if it matches the precision policy.
- Consider `torch._dynamo.config.suppress_errors = True` only as a debugging fallback, not as a correctness guarantee.
- If compile fails, keep the bitsandbytes config unchanged and troubleshoot PyTorch graph capture separately.

## Model-Download Safety

Before writing code that calls `from_pretrained` or tokenizer loading, ask or check:

- Is network access allowed, or must the model be in a local cache?
- Is the repository gated or private, requiring a Hugging Face token?
- Is `trust_remote_code=True` required, and has the user accepted that risk?
- Is the model license acceptable for the deployment?
- Does CI need a no-download validation path instead of loading weights?

For CI or offline validation, use the bundled config-check script. It imports optional packages and constructs config objects without loading a model.

## Validation Checklist

- Imports: `transformers` and `accelerate` for model loading; `peft` for QLoRA; `diffusers` only for Diffusers tasks.
- Config: exactly one of `load_in_8bit` or `load_in_4bit` should be true for the main model quantization mode.
- Dtype: compute dtype matches hardware capability; bfloat16 is not assumed on every accelerator.
- Device map: `device_map="auto"` is available only when the integration stack supports it.
- Backend: `bitsandbytes` imports and sees the intended device backend; route failures to `installation-diagnostics`.
- Download: model ID, local path, token, network, cache, and remote-code policy are explicit.
- Memory: large models have `max_memory`, offload, or smaller model alternatives planned.
- Execution: distinguish config-construction success from successful quantized forward/generation.
