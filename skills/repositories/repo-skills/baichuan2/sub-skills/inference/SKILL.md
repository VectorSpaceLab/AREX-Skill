---
name: inference
description: "Operate Baichuan2 chat/base inference, terminal chat, Streamlit
  chat, and OpenAI-compatible chat-completions workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
  repo: Baichuan2
  sub-skill-id: inference
  supported-workflows:
    - python-chat-inference
    - python-base-generation
    - interactive-cli-chat
    - streamlit-web-chat
    - openai-compatible-chat-completions
  required-backend: cuda-for-primary-chat-demos
  verified-inspection-context:
    torch: 2.5.1+cu121
    transformers: 5.15.0
    cuda-smoke: passed-on-nvidia-a100
    streamlit-cli-help: passed
    deepspeed-cli-help: passed
license: Apache 2.0
---

# Baichuan2 inference

Use this sub-skill when the user wants to run or understand Baichuan2 inference: Python chat snippets, Base-model text generation, the interactive terminal demo, the Streamlit chat UI, or the OpenAI-compatible `/v1/chat/completions` server.

Do **not** route quantization, CPU deployment conversion, model checkpoint normalization, fine-tuning, DeepSpeed training, or LoRA work here. Send those requests to the deployment or fine-tuning sub-skill.

## Route by user intent

| User asks for | Route | Key files |
| --- | --- | --- |
| "chat with Baichuan2 in Python" or "use model.chat" | Chat Python recipe | [`references/workflows.md`](references/workflows.md#chat-model-python-inference) |
| "run the Base model" or "plain text completion" | Base-model generation recipe | [`references/workflows.md`](references/workflows.md#base-model-python-generation) |
| "interactive CLI" or "terminal demo" | Chat CLI helper | [`scripts/chat_cli.py`](scripts/chat_cli.py) |
| "web demo" or "browser UI" | Streamlit helper | [`scripts/chat_web_demo.py`](scripts/chat_web_demo.py) |
| "OpenAI API compatible server" or "chat completions endpoint" | Flask API helper | [`scripts/run_openai_api.py`](scripts/run_openai_api.py), [`references/api-reference.md`](references/api-reference.md) |
| Load/model/runtime failure | Troubleshooting | [`references/troubleshooting.md`](references/troubleshooting.md) |

## Core operating facts

- Baichuan2 publishes **Chat** and **Base** model families for 7B and 13B. Use `*-Chat` for assistant-style conversations and `*-Base` for continuation/generation tasks.
- Chat-model code uses `AutoTokenizer.from_pretrained(..., use_fast=False, trust_remote_code=True)`, `AutoModelForCausalLM.from_pretrained(..., device_map="auto", torch_dtype=...)`, and `GenerationConfig.from_pretrained(model_id)` before calling `model.chat(tokenizer, messages)`.
- Base-model code uses tokenization plus `model.generate(...)`; do not use the CLI/web/API wrappers with Base checkpoints because those wrappers expect Chat model behavior.
- `device_map="auto"` lets Transformers place weights across available GPUs. To constrain visible GPUs, set `CUDA_VISIBLE_DEVICES` before launch.
- `torch.bfloat16` is the README chat-inference dtype and is appropriate on Ampere-class GPUs such as A100. The bundled chat/API demos default to `float16` to match the native demo scripts; use `--dtype bfloat16` on hardware that supports it.
- The prepared inspection environment verified a CUDA-capable stack with torch `2.5.1+cu121`, transformers `5.15.0`, Streamlit CLI help, DeepSpeed CLI help, and a CUDA tensor smoke test on NVIDIA A100. DeepSpeed is not required for this inference sub-skill.

## Minimal chat model recipe

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.generation.utils import GenerationConfig

model_id = "baichuan-inc/Baichuan2-13B-Chat"
tokenizer = AutoTokenizer.from_pretrained(
    model_id,
    use_fast=False,
    trust_remote_code=True,
)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    torch_dtype=torch.bfloat16,
    trust_remote_code=True,
)
model.generation_config = GenerationConfig.from_pretrained(model_id)

messages = [{"role": "user", "content": "解释一下“温故而知新”"}]
response = model.chat(tokenizer, messages)
print(response)
```

For streaming chat, call `model.chat(tokenizer, messages, stream=True)`. The iterator yields progressively longer response strings, so terminal UIs should print only the delta after the previous position.

## Bundled helpers

Run `--help` before loading weights:

```bash
python scripts/chat_cli.py --help
python scripts/run_openai_api.py --help
python scripts/chat_web_demo.py --help
```

Check launch configuration without downloading/loading weights:

```bash
python scripts/chat_cli.py --dry-run --model baichuan-inc/Baichuan2-13B-Chat
python scripts/run_openai_api.py --dry-run --host 127.0.0.1 --port 8000
python scripts/chat_web_demo.py --dry-run --model baichuan-inc/Baichuan2-13B-Chat
```

Launch examples:

```bash
# Terminal chat, Chat model only.
python scripts/chat_cli.py --model baichuan-inc/Baichuan2-13B-Chat --dtype float16 --stream

# OpenAI-compatible non-streaming API.
python scripts/run_openai_api.py --model baichuan-inc/Baichuan2-13B-Chat --host 0.0.0.0 --port 8000 --dtype float16

# Streamlit web UI. Streamlit server flags configure the web host/port;
# arguments after `--` are passed to the Baichuan2 helper.
streamlit run scripts/chat_web_demo.py --server.address 0.0.0.0 --server.port 8501 -- --model baichuan-inc/Baichuan2-13B-Chat --dtype float16
```

## API behavior to remember

- Endpoint: `POST /v1/chat/completions`.
- Request body should contain `messages`, each with `role` and `content`.
- The bundled API helper is intentionally **non-streaming**. If a client sends `"stream": true`, it returns HTTP 400 with a streaming-not-supported error.
- The API helper loads one configured Chat model at process startup. The request `model` field is accepted for OpenAI-style clients but does not switch the already-loaded model.

## When to escalate

- Missing weights, private model access, incompatible remote code, or network timeouts: use [`references/troubleshooting.md`](references/troubleshooting.md#model-weights-network-and-cache).
- Out-of-memory or dtype failures: use [`references/troubleshooting.md`](references/troubleshooting.md#gpu-memory-pressure-and-dtype-choice).
- Need 4-bit/8-bit loading, CPU-only operation, or checkpoint conversion: route to deployment.
- Need SFT, LoRA, DeepSpeed, training data validation, or model output checkpoints: route to fine-tuning.
