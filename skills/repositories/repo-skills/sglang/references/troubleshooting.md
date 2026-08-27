# SGLang Troubleshooting

## Dependency And Install Failures

- Full SGLang installs may pull large CUDA, Torch, flashinfer, and kernel wheels. If a large wheel times out, record the exact package and retry only with an approved mirror/proxy or an existing verified environment.
- Partial editable installs can expose metadata and source layout but may not import top-level `sglang` because import-time dependencies such as `orjson`, `torch`, or `transformers` are missing.
- Do not treat a source-only environment as proof that the production server can run.

## Serving Failures

- Separate CLI parsing issues from runtime model loading. Check server arguments, model path, tokenizer path, dtype, context length, TP/DP/EP settings, and CUDA visibility before debugging scheduler internals.
- OpenAI-compatible client failures can come from wrong base URL, model name mismatch, streaming format, tool/JSON constraints, or server warmup/model-load errors.
- Throughput or OOM issues need batch, KV cache, quantization, tensor parallelism, and scheduler settings checked together.

## Frontend Failures

- Frontend programs must use the right runtime/backend endpoint and generation primitives. Validate roles, `gen`/`select` names, stop conditions, and structured output assumptions.

## Benchmarking Failures

- Keep benchmark dataset, prompt/output lengths, concurrency, request rate, warmup, backend, GPU, and commit fixed before comparing numbers.
- Do not compare cold-start model load time with steady-state serving latency.
