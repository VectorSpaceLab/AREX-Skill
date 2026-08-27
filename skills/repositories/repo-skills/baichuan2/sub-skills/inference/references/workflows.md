# Baichuan2 inference workflows

This reference is the operating guide for Baichuan2 Python inference, terminal chat, web chat, and API launch flows. It assumes model weights are available from Hugging Face or an equivalent local model directory and that `trust_remote_code=True` is acceptable for the model source being used.

## Model family decision

| Model family | Example id | Use for | Invocation style |
| --- | --- | --- | --- |
| Chat | `baichuan-inc/Baichuan2-7B-Chat`, `baichuan-inc/Baichuan2-13B-Chat` | Assistant conversations, CLI demo, Streamlit UI, OpenAI-compatible chat-completions server | `model.chat(tokenizer, messages)` |
| Base | `baichuan-inc/Baichuan2-7B-Base`, `baichuan-inc/Baichuan2-13B-Base` | Prompt continuation / raw generation | `model.generate(**tokenized_inputs, ...)` |

The CLI, Streamlit, and OpenAI-compatible helpers are designed for Chat checkpoints. For Base checkpoints, use the Base Python generation recipe instead of forcing them through `model.chat`.

## Common setup

Install the inference/demo stack in the runtime environment:

```bash
python -m pip install torch transformers accelerate sentencepiece flask streamlit colorama
```

A verified inspection environment for this skill used torch `2.5.1+cu121`, transformers `5.15.0`, Streamlit CLI help, and a CUDA smoke test on NVIDIA A100. The real runtime must still have enough GPU memory and either network access or locally cached model weights.

### Dtype and device map

- `device_map="auto"` is the standard Baichuan2 recipe and lets Transformers/Accelerate place weights on visible devices.
- Set `CUDA_VISIBLE_DEVICES=0` or a comma-separated list before launch to control which GPUs are visible.
- Use `torch.bfloat16` on Ampere-class GPUs such as A100 when supported; the README chat example uses bfloat16.
- Use `torch.float16` for the native demo behavior and broader CUDA compatibility.
- Use `float32` only when intentionally running on CPU or debugging precision support; large-model CPU inference is slow and belongs to deployment planning, not this primary inference route.

## Chat model Python inference

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
model.eval()

messages = [{"role": "user", "content": "解释一下“温故而知新”"}]
with torch.inference_mode():
    response = model.chat(tokenizer, messages)
print(response)
```

### Multi-turn chat

Maintain a list of OpenAI-style role/content dictionaries. Append the user turn before generation and append the assistant response after generation:

```python
messages = []
messages.append({"role": "user", "content": "你好，请介绍你自己。"})
response = model.chat(tokenizer, messages)
messages.append({"role": "assistant", "content": response})
messages.append({"role": "user", "content": "用三点总结。"})
response = model.chat(tokenizer, messages)
```

### Streaming chat

`model.chat(tokenizer, messages, stream=True)` yields progressively longer response strings. A terminal renderer should print the delta only:

```python
position = 0
for response in model.chat(tokenizer, messages, stream=True):
    print(response[position:], end="", flush=True)
    position = len(response)
print()
```

If the generation is interrupted before a response is complete, only append the assistant turn when a non-empty response exists.

## Base model Python generation

Use Base checkpoints for continuation-style generation. They do not use the Chat message helper.

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "baichuan-inc/Baichuan2-13B-Base"
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    trust_remote_code=True,
)

inputs = tokenizer("登鹳雀楼->王之涣\n夜雨寄北->", return_tensors="pt")
inputs = inputs.to("cuda:0")
pred = model.generate(**inputs, max_new_tokens=64, repetition_penalty=1.1)
print(tokenizer.decode(pred.cpu()[0], skip_special_tokens=True))
```

If using a custom device placement, move tokenized inputs to the same device as the model's first CUDA shard or to the selected single device.

## Interactive CLI chat

The CLI helper adapts the native terminal demo with configurable model, dtype, and multiline behavior:

```bash
python scripts/chat_cli.py --dry-run
python scripts/chat_cli.py --model baichuan-inc/Baichuan2-13B-Chat --dtype float16 --stream
```

Interactive commands:

- `exit` or `quit`: end the session.
- `clear`: clear conversation history and redraw the banner.
- `stream`: toggle streaming/non-streaming generation.
- `vim` or `multiline`: open the configured editor for multiline input.

The multiline editor defaults to `$EDITOR`, then `vim`. Use `--editor nano`, `--editor code --wait`, or `--disable-editor` depending on the host terminal. If no editor is available, paste a normal single-line prompt instead.

## Streamlit web chat

The web helper adapts the native Streamlit chat UI. Start with dry-run/config validation:

```bash
python scripts/chat_web_demo.py --dry-run --model baichuan-inc/Baichuan2-13B-Chat
```

Launch through Streamlit:

```bash
streamlit run scripts/chat_web_demo.py --server.address 0.0.0.0 --server.port 8501 -- --model baichuan-inc/Baichuan2-13B-Chat --dtype float16
```

Notes:

- Streamlit server host/port are configured by Streamlit flags such as `--server.address` and `--server.port`.
- Arguments after `--` are passed to the Baichuan2 helper.
- The app caches the model with `st.cache_resource`, stores chat history in `st.session_state.messages`, and streams assistant updates into a placeholder.

## OpenAI-compatible chat-completions server

The API helper adapts the native Flask server and exposes a non-streaming OpenAI-style endpoint:

```bash
python scripts/run_openai_api.py --dry-run --host 127.0.0.1 --port 8000
python scripts/run_openai_api.py --model baichuan-inc/Baichuan2-13B-Chat --host 0.0.0.0 --port 8000 --dtype float16
```

Then call:

```bash
curl http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "baichuan2-chat",
    "messages": [{"role": "user", "content": "你好，请用一句话介绍百川二代。"}],
    "stream": false
  }'
```

Streaming requests are rejected intentionally. See [`api-reference.md`](api-reference.md) for request and response details.
