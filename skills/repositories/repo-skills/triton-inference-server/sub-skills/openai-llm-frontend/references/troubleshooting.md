# OpenAI Frontend Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Frontend fails to start | Missing Triton runtime libraries, wrong container variant, missing backend/model repository/tokenizer | Verify LLM Triton container, model repo, tokenizer, backend, GPU, and package imports. |
| `--load-model` error | `--load-model` without explicit mode or `*` combined with names | Use `--model-control-mode explicit`; use `--load-model=*` alone or list named models. |
| Request returns 401 | Endpoint group restricted by `--openai-restricted-api` | Send required header key/value or adjust restrictions. |
| Request too large / 413 | Payload exceeds `--http-max-input-size` default 64 MiB | Increase the flag intentionally or reduce request size. |
| Chat template/tokenizer failure | Missing tokenizer, wrong chat template, gated Hugging Face model, or missing `HF_TOKEN` | Provide local tokenizer, approved HF token, or custom chat template. |
| Tool calls malformed or truncated | Parser mismatch or output exceeds parser byte limit | Select compatible parser and adjust `--max-tool-call-parse-bytes`. |
| KServe request sent to OpenAI port | Protocol mix-up | Use `/v1/*` on the OpenAI port and `/v2/*` on the KServe HTTP port. |
