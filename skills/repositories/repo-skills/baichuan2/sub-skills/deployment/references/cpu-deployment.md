# Baichuan2 CPU deployment

## Scope

Use this reference when a user must load Baichuan2 without CUDA. CPU deployment is a float32 model-loading path. It is separate from CUDA quantization and from chat/UI/API workflow details.

## When CPU deployment is appropriate

Use CPU deployment for:

- CPU-only smoke checks where speed is not important.
- Environments where CUDA is unavailable or not allowed.
- Verifying that model files, tokenizer files, and `trust_remote_code` loading are basically usable before moving to a GPU host.

Avoid CPU deployment for:

- Throughput-sensitive chat serving.
- Latency-sensitive applications.
- Proving that BitsAndBytes quantization works. BitsAndBytes quantized Baichuan2 deployment is CUDA-native in the documented workflow.

## Core model-loading recipe

```python
from transformers import AutoModelForCausalLM
import torch

model = AutoModelForCausalLM.from_pretrained(
    "baichuan-inc/Baichuan2-7B-Chat",
    torch_dtype=torch.float32,
    trust_remote_code=True,
)
model.eval()
```

Key points:

- Use `torch_dtype=torch.float32`.
- Do not call `.cuda()`.
- Do not call `model.quantize(...)`.
- Do not use `load_in_8bit` or a 4-bit checkpoint as the CPU recipe.
- After the model object is loaded, hand off to the inference sub-skill for prompt formatting, chat calls, web/API serving, or generation UX.

## Practical expectations

- **Speed**: CPU inference is expected to be very slow for 7B/13B models. Treat it as a fallback or validation path unless an external CPU-optimization stack is being used.
- **Memory**: float32 CPU weights require substantially more host memory than fp16/bf16 GPU loading. Leave additional memory for tokenizer, generation cache, and Python overhead.
- **Batch size**: start with batch size 1 and short sequence lengths. Increase only after measuring memory and latency.
- **Precision**: float32 is the documented CPU path. Do not assume bf16/fp16 CPU kernels are available or faster on all hosts.

## Minimal validation sequence

1. Confirm Python can import Torch and Transformers.
2. Load tokenizer and model files using the float32 recipe above.
3. Call `model.eval()` and verify no CUDA device transfer occurs.
4. For an actual prompt or chat run, switch to the inference sub-skill and reuse the same CPU-loaded model pattern.

## Relationship to Baichuan 1 optimization reuse

If the user wants CPU compilation or other Baichuan 1-oriented optimization tooling, first read [conversion.md](conversion.md). The checkpoint conversion normalizes Baichuan2 `lm_head.weight` in a copied checkpoint directory so downstream Baichuan 1-style tooling can consume it.
