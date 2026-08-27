# API serving troubleshooting

## Server startup

- If `openai_api_server.py` fails at model load, first confirm the base model path, tokenizer path, and LoRA path belong to the same model family.
- If CPU mode is selected, do not pass 4-bit or 8-bit loading flags.
- If `--use_ntk` is enabled, confirm the model is meant for the requested long-context behavior.

## Request validation

- A model-name mismatch can produce a not-found style error in the vLLM server.
- Chat requests should use role/content dictionaries unless the specific protocol model accepts a raw string.
- Streaming responses require a client that can consume SSE or chunked output.

## Optional dependency failures

- The vLLM branch requires `vllm`, `fastchat`, and a compatible GPU stack.
- The non-vLLM server requires FastAPI, Uvicorn, SSE support, ShortUUID, Transformers, PEFT, and Torch.
- Missing FlashAttention is not fatal for the non-vLLM server unless the user explicitly requires that acceleration path.

## Feature mismatches

- The vLLM branch is not a drop-in replacement for the non-vLLM branch: LoRA, quantization, CFG, and speculative sampling behavior differs.
- If the user only wants local generation and not an HTTP service, route back to `hf-inference`.
