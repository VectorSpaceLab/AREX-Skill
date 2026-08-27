# OpenAI Frontend CLI Reference

## Common launch

```bash
python3 openai_frontend/main.py \
  --model-repository /models \
  --tokenizer meta-llama/Meta-Llama-3.1-8B-Instruct \
  --backend vllm \
  --openai-port 9000
```

Run it inside a Triton environment/container that contains the OpenAI frontend package, Triton server libraries, and the selected LLM backend.

## Important flags

- `--model-repository`: required Triton model repository for LLM models.
- `--tokenizer`: Hugging Face ID or local tokenizer path for chat templates.
- `--backend`: `vllm` or `tensorrtllm` request formatting.
- `--model-control-mode`: `none` or `explicit`.
- `--load-model`: startup model names; `*` must be the only value and requires explicit mode.
- `--openai-port`: default `9000`.
- `--enable-kserve-frontends`: also expose KServe HTTP/gRPC frontends.
- `--kserve-http-port` and `--kserve-grpc-port`: default `8000` and `8001`.
- `--openai-restricted-api`: restrict endpoint groups with a header key/value.
- `--http-max-input-size`: default 64 MiB (`67108864` bytes).
- `--tool-call-parser`, `--max-tool-call-parse-bytes`, and `--chat-template`: tune tool calling/chat-template behavior.

## Command builder

```bash
python3 scripts/build_openai_frontend_command.py --model-repository /models --tokenizer meta-llama/Meta-Llama-3.1-8B-Instruct --backend vllm
python3 scripts/build_openai_frontend_command.py --model-repository /models --model-control-mode explicit --load-model '*' --enable-kserve-frontends --json
```
