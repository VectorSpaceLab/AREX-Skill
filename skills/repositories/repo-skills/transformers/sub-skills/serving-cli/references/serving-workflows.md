# Serving Workflows

Use these patterns to design safe serving commands without starting services by default.

## 1. No-network preflight

```bash
python sub-skills/serving-cli/scripts/cli_preflight.py --check-serving --check-clients --port 8000
```

Check the output for:

- `OK import transformers` and CLI module import success.
- Optional packages marked `present` or `missing`.
- Port status for the selected host/port.
- Warnings about missing torch or serving extras.

If `requests` is missing and CLI module import fails, propose a minimal reinstall or install that includes the base CLI dependencies before trying `transformers --help`.

## 2. Build a local-only command

Default to a safe localhost bind:

```bash
transformers serve --host localhost --port 8000 --log-level info
```

Use on-demand loading when testing several locally cached models:

```bash
transformers serve --host localhost --port 8000 --model-timeout 120 --dtype auto --device auto
```

Use force model loading when every request should target the same model:

```bash
transformers serve Qwen/Qwen2.5-0.5B-Instruct --host localhost --port 8000 --dtype auto --device auto
```

Do not add `--trust-remote-code` unless the model repository code has been reviewed and the user explicitly accepts local code execution.

## 3. Warm a model after server startup

Only run this when a server is expected to be up and model download/loading is acceptable:

```bash
curl -N -X POST http://localhost:8000/load_model \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen2.5-0.5B-Instruct"}'
```

Expected SSE signals include stages such as processor/config/download/weights and a final ready event. Cached or already-loaded models may skip download or report cached/already loaded states. Missing `model` returns a validation error.

## 4. Send a tiny request first

Use a non-streaming request before streaming, browser integrations, or continuous batching:

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-0.5B-Instruct",
    "messages": [{"role": "user", "content": "Reply with one short sentence."}],
    "max_tokens": 32,
    "temperature": 0
  }'
```

Expected response: JSON object with `choices[0].message.content`, `model`, and `usage` fields. If this fails, do not proceed to streaming or optimization flags.

## 5. Add streaming

```bash
curl -N -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-0.5B-Instruct",
    "messages": [{"role": "user", "content": "Count to three."}],
    "max_tokens": 32,
    "stream": true
  }'
```

Expected signal: Server-Sent Events beginning with `data:` chunks and ending normally. If a client buffers output, use `curl -N` or a streaming-capable SDK iterator.

## 6. Use `transformers chat`

Start from an already healthy server:

```bash
transformers chat Qwen/Qwen2.5-0.5B-Instruct http://localhost:8000 max_new_tokens=128 do_sample=False
```

Inside chat, use `!set key=value` to update generation settings. The parser accepts JSON-like values after conversion, including booleans, `None`, numbers, strings, and lists.

## 7. Enable CORS only when needed

Browser-based integrations often require CORS:

```bash
transformers serve --host localhost --port 8000 --enable-cors
```

Security note: the implementation uses permissive CORS when enabled. Prefer local trusted networks, avoid public binding, and put a controlled proxy in front for real deployments.

## 8. Configure reasoning

Reasoning mode adjusts chat template kwargs only for compatible models:

```bash
transformers serve Qwen/Qwen3-8B \
  --reasoning on \
  --chat-template-kwargs '{"enable_thinking": true}'
```

Use `--reasoning off` to set `enable_thinking=false`. For models without compatible reasoning templates or thinking delimiters, the flag has no effect. Clients should check `reasoning_content` fields where supported rather than assuming visible content includes reasoning.

## 9. Tune continuous batching

Start with the smallest set of flags:

```bash
transformers serve \
  --continuous-batching \
  --attn-implementation sdpa \
  --dtype bfloat16
```

Then tune KV cache parameters only after measuring:

```bash
transformers serve \
  --continuous-batching \
  --cb-block-size 16 \
  --cb-num-blocks 2048 \
  --cb-max-batch-tokens 4096 \
  --cb-max-memory-percent 0.8
```

Avoid `--compile` with `--continuous-batching`. If continuous batching fails or returns a 503 caused by worker death, retry without continuous batching, verify torch/GPU/attention backend compatibility, and reduce batch/KV cache pressure.

## 10. Add quantization or attention backends

Runtime bitsandbytes quantization:

```bash
transformers serve --quantization bnb-4bit --device auto --dtype auto
```

Attention backend:

```bash
transformers serve --attn-implementation flash_attention_2 --dtype bfloat16
```

Use pre-quantized model ids directly when available; install the relevant quantization backend first. For detailed quantization decisions, use the sibling quantization sub-skill.
