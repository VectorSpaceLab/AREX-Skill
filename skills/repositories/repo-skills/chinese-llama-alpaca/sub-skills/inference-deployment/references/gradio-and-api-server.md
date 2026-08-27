# Gradio and OpenAI-Compatible API Server

The bundled UI/server scripts load large model assets and may expose network services. Run them only after the user confirms model paths, GPU/CPU backend, port, whether sharing/public exposure is acceptable, and shutdown policy.

## Gradio Chat Demo

Script: [`scripts/gradio_demo.py`](../scripts/gradio_demo.py)

```bash
python scripts/gradio_demo.py \
  --base_model /path/to/base_or_merged_hf_model \
  --lora_model /path/to/chinese_alpaca_lora_or_none \
  --tokenizer_path /path/to/matching_tokenizer \
  --gpus 0 \
  --port 19324 \
  --max_memory 2048
```

Important flags:

| Flag | Meaning |
| --- | --- |
| `--base_model` | Required model path/id. |
| `--lora_model` | Optional adapter path/id. |
| `--tokenizer_path` | Optional explicit tokenizer path. Defaults to LoRA path, then base model. |
| `--gpus` | CUDA device ids. `--only_cpu` clears CUDA. |
| `--share` | Gradio share setting. Treat public sharing as network exposure. |
| `--port` | Server port, default `19324`. |
| `--max_memory` | Maximum prompt-history character length retained by the script. |
| `--load_in_8bit` | Optional lower-VRAM loading. |
| `--alpha` | NTK scaling factor, float or `auto`. |

The UI builds a dialogue-style prompt by concatenating prior `### Instruction:` / `### Response:` turns and trimming to `max_memory` characters.

## OpenAI-Compatible FastAPI Server

Script: [`scripts/openai_api_server.py`](../scripts/openai_api_server.py)

```bash
python scripts/openai_api_server.py \
  --base_model /path/to/base_or_merged_hf_model \
  --lora_model /path/to/chinese_alpaca_lora_or_none \
  --tokenizer_path /path/to/matching_tokenizer \
  --gpus 0
```

The server listens on `0.0.0.0:19327` with one Uvicorn worker. Protect it with local firewall/reverse-proxy policy if used beyond localhost.

### Endpoints

| Endpoint | Request class | Purpose |
| --- | --- | --- |
| `POST /v1/completions` | `CompletionRequest` | Prompt completion using Alpaca instruction wrapper. |
| `POST /v1/chat/completions` | `ChatCompletionRequest` | Multi-message prompt assembled into instruction/response turns. |
| `POST /v1/embeddings` | `EmbeddingsRequest` | Mean-pooled normalized final hidden-state embedding. |

### Completion Example

```bash
curl http://localhost:19327/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"prompt":"告诉我中国的首都在哪里","max_tokens":90,"temperature":0.7,"top_k":40}'
```

### Chat Example and Schema Quirk

The source server maps incoming message dictionaries with keys `role` and `message` into internal `ChatMessage(role=..., content=...)`. Use `message`, not `content`, in request dictionaries for this bundled server version:

```bash
curl http://localhost:19327/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","message":"给我讲一些有关杭州的故事吧"}],"repetition_penalty":1.0}'
```

If a client sends OpenAI-style `content`, adapt the request or patch the server deliberately; do not silently assume both keys work.

## Decoding Parameters

The request schemas in [`scripts/openai_api_protocol.py`](../scripts/openai_api_protocol.py) support `temperature`, `top_p`, `top_k`, `num_beams`, `max_tokens`, `repetition_penalty`, and `do_sample`. The server passes these into `GenerationConfig` and `model.generate`.

## Embeddings Caveat

The embeddings endpoint adds `[PAD]` if the tokenizer has no pad token, averages final hidden states over the attention mask, and L2-normalizes. It is a simple demo embedding, not a dedicated embedding model benchmark.
