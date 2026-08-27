# Backend Protocol Troubleshooting

## Parameter validation

| Symptom | Likely cause | Fix |
|---|---|---|
| `temperature must be non-negative` | Negative temperature passed to `LLMParams`. | Use `temperature=0` for greedy or a positive value for sampling. |
| `n must be 1 when using greedy sampling` | Near-zero temperature with multiple completions. | Keep `n=1` or raise temperature above the greedy threshold. |
| `top_k must be -1, or at least 1` | `top_k=0` or negative other than `-1`. | Use `-1` to disable or a positive integer. |
| `min_tokens` exceeds `max_tokens` | Inconsistent generation bounds. | Increase `max_tokens` or reduce `min_tokens`. |

## Registry failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `No model class found for model ...` | Model key does not match registered model-specific key and no task-type fallback exists. | Normalize slash names to the expected registry key and verify handler registration. |
| DistilBERT handler not selected in UI | Model name mismatch or handler import failed. | Confirm backend handlers import before UI creation; check local model name spelling. |
| Remote Llama mapping missing | Model key absent from the LLM model mapping. | Add mapping and handler registration together; test with request preview first. |

## Prompt/request failures

| Symptom | Likely cause | Fix |
|---|---|---|
| Sanitized content loses characters | `clean_string` strips non-ASCII/non-printable content. | Reproduce with a minimal string and decide whether the source helper is appropriate for that task. |
| Request payload sends plaintext | Tokenization step skipped or wrong handler selected. | Use request preview to confirm message content is token IDs, not raw text. |
| Output integers are not decoded | Local tokenizer missing or terminator handling wrong. | Verify tokenizer path/model key and EOS/EOT token ids. |

## Service/network failures

| Symptom | Likely cause | Fix |
|---|---|---|
| SSE stream times out before first chunk | Endpoint unreachable or service unavailable. | Report as network/service blocked; do not mark protocol code wrong without a local preview pass. |
| `msgspec.DecodeError` while streaming | Response shape differs from expected `InferenceResponse`. | Capture one sanitized event block and compare fields to the API reference. |
| HTTP status error | Endpoint, auth, model id, or service state issue. | Check configured stream URL and model id; ask for credentials or service status if needed. |

## Dependency failures

Install backend protocol dependencies before importing source helpers:

```bash
python -m pip install msgspec pydantic-settings python-dotenv nats-py httpx transformers
```

Add `torch`, `safetensors`, and local model dependencies only when inspecting the
Hugging Face model handler or local DistilBERT workflow.
