# Quantization Workflows for LoRA

PEFT can train LoRA adapters on quantized base models because only adapter parameters are updated. The base model quantization choice is usually made through Transformers or a backend-specific loader before calling `get_peft_model`.

## Standard bitsandbytes QLoRA pattern

```python
import torch
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
)
base_model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=quantization_config,
    device_map="auto",
)
base_model = prepare_model_for_kbit_training(base_model)
peft_config = LoraConfig(task_type="CAUSAL_LM", target_modules="all-linear", r=16, lora_alpha=32)
model = get_peft_model(base_model, peft_config)
```

Use 4-bit NF4 for the common QLoRA recipe. Use `bnb_4bit_compute_dtype=torch.bfloat16` when the hardware supports bfloat16; otherwise choose a dtype compatible with the accelerator. Mismatched input and compute dtype can slow training.

## Backend matrix

| Backend | Typical load path | LoRA support notes | Caveats |
| --- | --- | --- | --- |
| bitsandbytes 8-bit/4-bit | `BitsAndBytesConfig` in `from_pretrained` | Common QLoRA path; call `prepare_model_for_kbit_training`; DoRA can work as QDoRA | 4-bit LoftQ replacement only supports bitsandbytes 4-bit; DeepSpeed ZeRO-2 has reported QDoRA issues |
| GPTQ / GPT-QModel | `GPTQConfig` or a prequantized GPTQ checkpoint | PEFT supports post-training GPTQ models; QALoRA is currently implemented for GPTQ | Backend dependency required; QALoRA targets linear layers and needs divisible group sizes |
| AQLM | prequantized AQLM model plus `aqlm` package | LoRA adapter tuning is supported | Finetuned LoRA adapters must be saved separately; merging into AQLM quantized weights is not possible |
| EETQ | `EetqConfig("int8")` in `from_pretrained` | LoRA fine-tuning on EETQ quantized models is supported | Requires compatible Transformers/EETQ versions |
| HQQ | `HQQModelForCausalLM.from_quantized` or `HqqConfig` | LoRA adapter tuning is supported | Requires `hqq` package; loading API differs by path |
| torchao | `TorchAoConfig` with torchao quantization config | Explicit LoRA support for int8 weight-only; DoRA currently works only with int8 weight-only | Only linear layers; int4 weight-only and NF4 are not supported; merge correctness is limited to LoRA with int8 weight-only |
| INC | Intel Neural Compressor prepare/calibrate/convert flow | PEFT LoRA adapters can load on INC-quantized models | `merge()` and `unmerge()` are not supported; only Linear INC-quantized layers are supported |

Other PEFT methods with quantization support include VeRA with bitsandbytes, AdaLoRA with bitsandbytes and GPTQ, and IA3 with bitsandbytes. Route non-LoRA methods to the specialized tuner guidance.

## LoftQ: initialization vs replacement

### Use full LoftQ initialization when the model is not quantized yet

```python
from peft import LoftQConfig, LoraConfig, get_peft_model

peft_config = LoraConfig(
    task_type="CAUSAL_LM",
    target_modules="all-linear",
    init_lora_weights="loftq",
    loftq_config=LoftQConfig(loftq_bits=4, loftq_iter=1),
)
model = get_peft_model(full_precision_base_model, peft_config)
```

This path quantizes backbone weights and initializes LoRA layers. Do not pass a prequantized base model. It requires `scipy` at configuration time.

### Use replacement when the model is already bitsandbytes 4-bit

```python
from peft import LoraConfig, get_peft_model, replace_lora_weights_loftq

peft_config = LoraConfig(task_type="CAUSAL_LM", target_modules="all-linear")
peft_model = get_peft_model(quantized_base_model, peft_config)
replace_lora_weights_loftq(peft_model)
```

This path updates LoRA weights in place after wrapping an already quantized model. It is easier but more limited:

- Model reference weights must be available as safetensors.
- Only bitsandbytes 4-bit quantization is supported.
- It performs one LoftQ step and updates only LoRA weights, not quantized base weights.
- A callback can accept/reject individual layer replacements.

## QALoRA workflow

QALoRA is currently implemented for GPTQ and linear layers.

```python
from peft import LoraConfig, get_peft_model

peft_config = LoraConfig(
    task_type="CAUSAL_LM",
    target_modules="all-linear",
    use_qalora=True,
    qalora_group_size=32,
)
model = get_peft_model(gptq_quantized_model, peft_config)
```

If PEFT raises that a module input dimension is not divisible by `qalora_group_size`, reduce `qalora_group_size`, choose a divisor that fits the architecture, or target a narrower set of compatible modules.

## Optional dependency fallback policy

When an optional quantization package is missing:

1. Confirm which backend the model actually needs. Do not install every backend by default.
2. If the user only needs generic LoRA, load the model in full precision or half precision and use standard `LoraConfig`.
3. If memory requires quantization, prefer a backend that is already installed and supported by the hardware.
4. If a specific checkpoint is prequantized for a missing backend, either install that backend or choose a different checkpoint format.
5. If merge is required, avoid backends whose docs state merge is unsupported or only partially correct.

Common install hints to provide generically:

```bash
pip install peft
pip install bitsandbytes
pip install "gptqmodel>=7.0.0"
pip install "aqlm>=1.0.2"
pip install hqq
pip install torchao
pip install "neural-compressor[pt]"
```

For contributors working from source, use an editable source install of PEFT instead of a local path in public instructions.

## Dtype and preparation caveats

- `prepare_model_for_kbit_training` is for k-bit training preparation before applying PEFT to bitsandbytes-style quantized models.
- Use `device_map="auto"` or an explicit device map for large quantized models; launcher/distributed details belong to training integration guidance.
- Keep adapter dtype autocasting in mind. `get_peft_model(..., autocast_adapter_dtype=True)` may promote adapter weights for stable training.
- Quantized base weights are typically frozen. If gradients appear on many base parameters, inspect preparation and adapter wrapping order.
- Some quantization backends load special layer classes; broad `target_modules="all-linear"` is usually safer than hard-coded names only if the backend exposes compatible layers.
