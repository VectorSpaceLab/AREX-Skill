# Backend Troubleshooting

Start by identifying which phase failed: registry lookup, optional dependency import, model construction, endpoint authentication, hardware allocation, request-type mismatch, or `model_args` parsing.

## Quick Checks

```bash
lm-eval ls models
python scripts/check_backend_requirements.py --backend hf --backend local-completions --backend vllm
python scripts/model_args_builder.py --set pretrained=EleutherAI/pythia-160m --set dtype=float16
```

If `lm-eval ls models` works but backend construction fails, the alias is registered and the problem is usually a missing extra, provider credential, model argument, or hardware/runtime dependency.

## Symptom Matrix

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Unknown model '...'` | Alias not registered or typo | Import `lm_eval.models`, check `lm-eval ls models`, use aliases from backend reference |
| `ModuleNotFoundError: torch` or `transformers` while using `hf` | Base install excludes HF stack | Install `pip install "lm_eval[hf]"` |
| `ModuleNotFoundError: vllm` | vLLM extra/backend missing | Install `pip install "lm_eval[vllm]"` in a compatible GPU environment |
| API model complains about `aiohttp`, `requests`, `tenacity`, or `tqdm` | API extra missing | Install `pip install "lm_eval[api]"` |
| `ModuleNotFoundError: litellm` | LiteLLM extra missing | Install `pip install "lm_eval[litellm]"` |
| `API key not found` | Missing provider environment variable | Set `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or provider-specific LiteLLM key outside committed configs |
| `Loglikelihood is not supported for chat completions` | Chat endpoint selected for likelihood/multiple-choice task | Use `local-completions` or `openai-completions`, or switch to a generative task |
| HTTP 404/405 from local server | Wrong endpoint path for backend | Match `local-completions` to `/v1/completions` and `local-chat-completions` to `/v1/chat/completions` |
| Bad likelihood scores from local API | Tokenizer mismatch or no logprobs/echo | Set `tokenizer_backend=huggingface,tokenizer=<matching-tokenizer>` or use a server with compatible logprobs |
| `enable_thinking=True` error on likelihood task | Thinking mode only valid for generation | Use a generative task or remove `enable_thinking` |
| `think_end_token` rejected or ineffective | Wrong type or delimiter | Use int/string for `hf`; string for `vllm`/`sglang`; copy exact tokenizer delimiter |
| CUDA OOM | Batch/model too large | Reduce `--batch_size`, use `batch_size=auto`, lower dtype, use smaller model, or use backend parallelism |
| `No CUDA` / device mismatch | Local backend assumes GPU | Set `--device cpu` for CPU-capable `hf`, or choose hardware-specific backend only on matching machine |
| Import succeeds but class construction fails | Required constructor `model_args` missing | Add backend-specific keys such as `pretrained=`, `model=`, `base_url=`, `tokenizer=` |
| `model_args` split incorrectly | Commas/spaces/quotes parsed unexpectedly | Build with `scripts/model_args_builder.py` and quote the full string in shell |

## Base Install Misconception

The base package deliberately excludes heavy optional backends. A base environment may list lazy registry aliases after `import lm_eval.models`, but concrete imports like `from lm_eval.models.huggingface import HFLM` can fail until `torch` and `transformers` are installed. Explain this clearly instead of treating it as a broken installation.

Suggested response:

> The harness core is installed, but `hf` is an optional backend. Install `lm_eval[hf]` to add `torch`, `transformers`, `accelerate`, and `peft`, then rerun the backend check.

## API Credential Failures

Do not put secrets in `--model_args`, YAML files, result logs, or skill content. Prefer environment variables:

```bash
export OPENAI_API_KEY=...
export ANTHROPIC_API_KEY=...
```

For self-hosted endpoints that need bearer auth, use the backend's `auth_token`/`header` support only in local private configs, and redact before sharing.

## `model_args` Quoting Rules

The harness accepts comma-separated `key=value` strings and newer CLI paths may also parse space-separated key-value pairs into dictionaries. In shell commands, quote the entire argument when values contain special characters:

```bash
lm-eval run --model hf \
  --model_args 'pretrained=org/model,dtype=float16,trust_remote_code=True' \
  --tasks hellaswag
```

Use JSON-like values sparingly in `model_args`; if a value contains a comma, build it with the helper and review the output:

```bash
python scripts/model_args_builder.py \
  --set pretrained=org/model \
  --set 'chat_template_args={"enable_thinking": true}'
```

If the helper cannot represent a complex value safely for the comma parser, prefer a configuration file and pass `model_args` as a mapping through the evaluation-runs workflow.

## Hardware-Specific Backends

- `vllm`, `sglang`, `trtllm`, `habana`, `ipex`, `openvino`, and `winml` depend on platform-specific runtimes. Validate driver/runtime compatibility outside the skill before running full evaluations.
- `vllm` data parallel replicas may require Ray and reserve `tensor_parallel_size` GPUs per actor.
- `hf` supports CPU/MPS/CUDA depending on installed PyTorch and model support; use `dtype=float32` for CPU when float16 is unsupported.
- OpenVINO expects converted Intermediate Representation models; Windows ML expects ONNX GenAI format.

## When to Escalate to Other Sub-skills

- If backend construction works but task output type is wrong, route to `task-authoring`.
- If the command structure, config file, batch/cache/run flags, or small-limit dry run is the focus, route to `evaluation-runs`.
- If uploading, logging samples, W&B, TrackIO, or Hub artifacts fail, route to `result-logging`.
