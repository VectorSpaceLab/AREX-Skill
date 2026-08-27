# Model Loading and Inference

## When to read

Read this for Qwen local or cloud inference with Transformers, ModelScope, DashScope, batch generation, or local checkpoint fallback. For services and Docker, route to `../serving-deployment/SKILL.md`.

## Minimal dependency path

The documented base path is Python 3.8+, PyTorch, Transformers 4.32+, Accelerate, tiktoken, einops, `transformers_stream_generator`, and SciPy. Install the narrow base requirements before optional extras:

```bash
pip install -r requirements.txt
```

Avoid broad optional installs until the workflow requires them. FlashAttention, vLLM, AutoGPTQ, PEFT, DeepSpeed, ModelScope, web UI, and API-server packages solve different problems.

## Transformers chat model pattern

Use a chat checkpoint when the user expects assistant behavior:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.generation import GenerationConfig

model_id = "Qwen/Qwen-7B-Chat"
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    trust_remote_code=True,
).eval()

# Recent supported Transformers can load generation config automatically, but
# make it explicit when debugging checkpoint defaults.
model.generation_config = GenerationConfig.from_pretrained(model_id, trust_remote_code=True)

response, history = model.chat(tokenizer, "你好", history=None)
response, history = model.chat(tokenizer, "给这个回答起一个标题", history=history)
```

Useful variants:

- CPU compatibility: `device_map="cpu"`, with the expectation that generation is very slow.
- BF16-capable GPU: pass `bf16=True` where checkpoint-side model code supports it.
- FP16 or quantized model: pass `fp16=True` or select the `*-Int4`/`*-Int8` checkpoint and install the compatible quantization stack.
- Local checkpoint: replace `model_id` with a local directory after validating it with `scripts/qwen_inference_checklist.py --local-checkpoint /path/to/checkpoint`.

## Base model continuation pattern

Use a base checkpoint such as `Qwen/Qwen-7B` for continuation/generation, not for chat alignment:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen-7B", trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen-7B",
    device_map="auto",
    trust_remote_code=True,
).eval()

inputs = tokenizer("蒙古国的首都是乌兰巴托\n冰岛的首都是", return_tensors="pt")
inputs = inputs.to(model.device)
output_ids = model.generate(**inputs)
print(tokenizer.decode(output_ids.cpu()[0], skip_special_tokens=True))
```

If a user complains that instructions are ignored, first verify they did not load a base model for a chat task.

## ModelScope and local snapshots

ModelScope uses names such as `qwen/Qwen-7B-Chat`. Use it when the user prefers that hub or when Hugging Face access is unreliable. A safe plan is:

1. Download the snapshot with ModelScope in an environment where network/storage is approved.
2. Treat the resulting directory as the trusted local checkpoint.
3. Load that local directory with Transformers and `trust_remote_code=True`.

Do not write code that automatically downloads a model unless the user accepts network and storage cost.

## DashScope hosted API

DashScope is a hosted service, not the same as local Qwen weights. It requires network access, an Alibaba Cloud account, and an API key such as `DASHSCOPE_API_KEY`. Use DashScope when the user wants an API service and does not need local weights or repository scripts. Keep credentials outside examples and logs.

## Batch inference essentials

Qwen batch inference needs left padding and a pad token distinct from the EOS/control token so attention masks can be generated correctly. The historical pattern is:

```python
tokenizer = AutoTokenizer.from_pretrained(
    checkpoint_dir,
    pad_token="<|extra_0|>",
    eos_token="<|endoftext|>",
    padding_side="left",
    trust_remote_code=True,
)
model = AutoModelForCausalLM.from_pretrained(
    checkpoint_dir,
    pad_token_id=tokenizer.pad_token_id,
    device_map="auto",
    trust_remote_code=True,
).eval()
model.generation_config.pad_token_id = tokenizer.pad_token_id
```

Then build model-specific chat context for each raw query, tokenize with `padding='longest'`, generate, and decode each output after its padding length and raw prompt length. If a user's batch output contains prompt leakage or malformed masks, check padding before tuning sampling parameters.

## Local checkpoint checklist

Before loading weights, confirm:

- `config.json` exists.
- Tokenizer assets exist, especially tokenizer config and Qwen tiktoken files when applicable.
- All model shards or safetensors files are present.
- The directory contains the remote-code Python files expected by the checkpoint.
- The user trusts the checkpoint source because `trust_remote_code=True` executes code from it.
