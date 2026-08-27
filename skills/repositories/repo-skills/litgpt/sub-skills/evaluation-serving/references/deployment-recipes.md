# Deployment Recipes

Use these recipes to plan LitGPT HTTP serving through LitServe. Starting a server loads model weights and is long-running, so preflight and request-shape planning should happen first.

## Preflight Checklist

1. Check optional dependencies and port availability:
   `python scripts/check_optional_eval_serve_deps.py --mode serve --checkpoint-dir CHECKPOINT_DIR --port 8000`.
2. Route checkpoint layout, download, conversion, or tokenizer problems to `../../checkpoint-conversion/`.
3. Choose exactly one endpoint mode: simple, simple streaming, or OpenAI-compatible.
4. Generate curl examples with `scripts/build_curl_examples.py` before starting the server.
5. Start `litgpt serve` only after the user accepts a long-running process and the port/device choices are clear.

## Simple Prompt API

Start server:

```bash
litgpt serve CHECKPOINT_DIR --port 8000 --api_path /predict
```

Request shape:

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Fix typos in this sentence: Example input"}'
```

Expected response shape:

```json
{"output":"...model text..."}
```

Use this mode when the client can send a single prompt string and expects one final JSON response.

## Simple Streaming API

Start server:

```bash
litgpt serve CHECKPOINT_DIR --port 8000 --api_path /predict --stream true
```

Request shape:

```bash
curl -N -X POST http://127.0.0.1:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Write one sentence about LitGPT."}'
```

Expected response shape:

- Line-oriented JSON chunks.
- Each chunk contains an `output` field.
- Clients should concatenate chunk outputs for the final text.

Use this mode for token-by-token simple prompt streaming. It is not the OpenAI streaming schema.

## OpenAI-Compatible Chat Completions

Start server:

```bash
litgpt serve CHECKPOINT_DIR --port 8000 --openai_spec true
```

Request shape:

```bash
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "local-litgpt-model",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

Expected non-streaming response shape:

- JSON object with `choices`.
- First choice contains `message.content`.

Streaming OpenAI-compatible request:

```bash
curl -N -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "local-litgpt-model",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": true
  }'
```

Expected streaming response shape:

- Server-sent-event style lines beginning with `data:`.
- Chunks contain `choices[0].delta.content`.
- A final done marker may appear.

OpenAI mode notes:

- Requires `litserve` and `jinja2`.
- Reads `tokenizer_config.json` to find `chat_template`; if missing, LitGPT falls back to a simple default chat template.
- Do not send `{"prompt": "..."}` to `/v1/chat/completions`; use `messages`.
- Do not send `messages` to `/predict`; use `prompt`.

## Generate Curl Examples Without Starting a Server

Simple mode:

```bash
python scripts/build_curl_examples.py --mode simple --port 8000 --api-path /predict
```

Streaming simple mode:

```bash
python scripts/build_curl_examples.py --mode stream --port 8000 --api-path /predict
```

OpenAI-compatible mode:

```bash
python scripts/build_curl_examples.py \
  --mode openai \
  --port 8000 \
  --api-path /v1/chat/completions \
  --model local-litgpt-model
```

## Devices, Precision, and Quantization

Common server plan:

```bash
litgpt serve CHECKPOINT_DIR \
  --accelerator cuda \
  --devices 1 \
  --precision bf16-true \
  --quantize bnb.nf4 \
  --port 8000
```

Cautions:

- `bnb.*` quantization requires bitsandbytes and a compatible backend; it is often CUDA/Linux-sensitive.
- `--devices 2` with no explicit `--generate_strategy` may use sequential block distribution from source behavior.
- `--generate_strategy tensor_parallel` needs a suitable multi-GPU environment.
- `--timeout` controls LitServe request timeout; it does not guarantee model startup time.

## Hard Case: OpenAI Path vs Simple Path

For `--openai_spec true`, use:

```bash
litgpt serve CHECKPOINT_DIR --openai_spec true --port 8000
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"local-litgpt-model","messages":[{"role":"user","content":"Hello"}]}'
```

For simple prompt mode, use:

```bash
litgpt serve CHECKPOINT_DIR --api_path /predict --port 8000
curl -X POST http://127.0.0.1:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Hello"}'
```

If a user asks for OpenAI-compatible `/v1/chat/completions` and simple `/predict` examples, generate both separately and label the payload schema difference before starting a server.
