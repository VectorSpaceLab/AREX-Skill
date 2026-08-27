# Baichuan2 quantization

## Scope

Use this reference for Baichuan2 GPU-memory reduction through BitsAndBytes-backed quantization. It covers online 4-bit/8-bit quantization, loading published 4-bit Chat checkpoints, and saving an 8-bit quantized model directory.

This reference does not cover prompt formatting, chat UI/API serving, training, or LoRA.

## Decision table

| Goal | Recommended route | CUDA needed? | `device_map="auto"`? | Notes |
|---|---|---:|---:|---|
| Lowest memory for Chat with minimum local work | Load a published `*-Chat-4bits` checkpoint | Yes | Yes | Uses the pre-quantized 4-bit Chat model family. |
| Quantize an fp16 Baichuan2 Chat model during the current run | Online quantization with `model.quantize(4)` or `model.quantize(8)` | Yes | No | Load to CPU first, quantize, then call `.cuda()`. |
| Save an 8-bit model directory for later reuse | Offline 8-bit Transformers/BitsAndBytes load, then `save_pretrained` | Yes | Yes | The project did not publish separate 8-bit weights; the helper can save them. |
| CPU-only run | Do not use this quantization path | No | No | Use [cpu-deployment.md](cpu-deployment.md) instead. |

## Quantization choices

- **4-bit online**: use `model.quantize(4).cuda()`. Baichuan2 chooses **NF4** as the 4-bit data type in its documented BitsAndBytes method.
- **8-bit online**: use `model.quantize(8).cuda()`. This usually costs more memory than 4-bit but can be a safer quality/performance compromise.
- **4-bit pre-quantized**: load the available Chat 4-bit checkpoint directly with `device_map="auto"`; do not run `model.quantize` again.
- **8-bit offline saved model**: load the original model through the Transformers/BitsAndBytes 8-bit API, save to a new directory, then reload that directory for deployment.

## Documented memory and quality expectations

The Baichuan2 docs report the following approximate GPU memory footprints. The two language variants of the docs differ slightly for fp16/bf16 and 13B 8-bit memory, so treat these as planning ranges rather than strict capacity guarantees.

| Precision | 7B memory | 13B memory | Interpretation |
|---|---:|---:|---|
| bf16 / fp16 | 14.0-15.3 GB | 25.9-27.5 GB | Baseline half-precision load. |
| 8-bit | 8.0 GB | 14.2-16.1 GB | Roughly halves memory versus fp16/bf16. |
| 4-bit | 5.1 GB | 8.6 GB | Lowest documented memory path. |

Documented 4-bit benchmark results are close to the original Chat models, with about a **1-2 point** drop relative to bfloat16 in the cited C-Eval/MMLU/CMMLU comparisons. Re-check quality for task-specific workloads.

## Core code patterns

### Online 8-bit

```python
from transformers import AutoModelForCausalLM
import torch

model = AutoModelForCausalLM.from_pretrained(
    "baichuan-inc/Baichuan2-7B-Chat",
    torch_dtype=torch.float16,
    trust_remote_code=True,
)
model = model.quantize(8).cuda()
```

### Online 4-bit

```python
from transformers import AutoModelForCausalLM
import torch

model = AutoModelForCausalLM.from_pretrained(
    "baichuan-inc/Baichuan2-7B-Chat",
    torch_dtype=torch.float16,
    trust_remote_code=True,
)
model = model.quantize(4).cuda()
```

Do **not** add `device_map="auto"` to these online quantization loads. The model must be loaded in CPU memory before `quantize()` is called.

### Load a pre-quantized 4-bit Chat model

```python
from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained(
    "baichuan-inc/Baichuan2-7B-Chat-4bits",
    device_map="auto",
    trust_remote_code=True,
)
```

### Save and reload an 8-bit quantized model

```python
from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    load_in_8bit=True,
    device_map="auto",
    trust_remote_code=True,
)
model.save_pretrained(quant8_saved_dir)
model = AutoModelForCausalLM.from_pretrained(
    quant8_saved_dir,
    device_map="auto",
    trust_remote_code=True,
)
```

## Bundled helper usage

From this sub-skill directory:

```bash
python scripts/quantize_model.py \
  --dry-run --validate-imports \
  --mode online --bits 4 \
  --model-id baichuan-inc/Baichuan2-7B-Chat
```

Online 4-bit quantization:

```bash
python scripts/quantize_model.py \
  --mode online --bits 4 \
  --model-id baichuan-inc/Baichuan2-7B-Chat
```

Online 8-bit quantization:

```bash
python scripts/quantize_model.py \
  --mode online --bits 8 \
  --model-id baichuan-inc/Baichuan2-7B-Chat
```

Save an 8-bit model directory:

```bash
python scripts/quantize_model.py \
  --mode offline-8bit \
  --model-id baichuan-inc/Baichuan2-7B-Chat \
  --save-dir ./Baichuan2-7B-Chat-8bit
```

Load a pre-quantized 4-bit Chat checkpoint:

```bash
python scripts/quantize_model.py \
  --mode load-prequantized-4bit \
  --model-id baichuan-inc/Baichuan2-7B-Chat-4bits
```

## Environment facts to rely on

A representative inspection stack verified:

- Torch `2.5.1+cu121` with a passing CUDA tensor smoke check.
- Transformers `5.15.0` import.
- BitsAndBytes `0.50.1` import.
- `bitsandbytes.nn.Linear8bitLt` CUDA forward smoke check.

These facts prove the inspected package stack can import BitsAndBytes and run a minimal CUDA 8-bit layer; they do not prove that every target host has enough memory for a full 7B/13B quantization run.
