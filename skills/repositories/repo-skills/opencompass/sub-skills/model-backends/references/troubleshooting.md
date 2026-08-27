# Troubleshooting Model Backends

Use this guide when a model config fails before changing datasets, prompts, or summarizers. Isolate whether the failure is config parsing, missing optional packages, credentials, tokenizer/model loading, resource sizing, or backend compatibility.

## Fast Triage

1. Confirm the config has `models = [...]` and each model has `type`, `abbr`, `path` or service address, `max_out_len`, `batch_size`, and `run_cfg`.
2. For API configs, run `scripts/check_api_model_config.py` before any real request.
3. For HF/local models, validate package versions, model path access, tokenizer kwargs, and memory budget.
4. For vLLM/LMDeploy, verify the optional backend imports independently before launching OpenCompass.
5. Reduce `batch_size` and output length before changing evaluation semantics.

## Missing Optional Extras

Symptoms:

- `ModuleNotFoundError: openai`, `anthropic`, provider SDKs, `vllm`, `lmdeploy`, or `lightllm`.
- Assertion messages such as asking to install vLLM.
- Import succeeds for `opencompass`, but backend execution fails.

Fixes:

- Install only the needed optional backend dependencies for the task.
- Keep API, vLLM, and LMDeploy dependency sets isolated when they require conflicting Torch/CUDA versions.
- Do not claim backend execution was verified just because base OpenCompass imports.

## API Key and Base URL Failures

Symptoms:

- `OpenAI API key is not set.`
- 401/403 unauthorized responses.
- Connection failures to local servers.
- Requests go to public OpenAI when a local compatible service was intended.

Fixes:

- Use `key='ENV'` only when `OPENAI_API_KEY` is set.
- Use `key='EMPTY'` only for local compatible services that ignore API keys.
- Set `openai_api_base` explicitly for compatible services, including `/v1` when the server expects OpenAI-compatible paths.
- Use `api_addr` for `TurboMindAPIModel` native service configs.
- Run the dry-run checker to catch placeholders before a network call.

## Rate Limits and Retries

Symptoms:

- 429 rate-limit errors.
- Intermittent provider failures.
- Very slow API evaluations.

Fixes:

- Lower `query_per_second`.
- Start with `batch_size=1` for external providers.
- Keep `retry` modest for transient failures; fix auth/quota/config errors instead of retrying them.
- Enable `rpm_verbose=True` when request pacing is unclear.

## Invalid Model Path or Tokenizer Path

Symptoms:

- HF repo not found, local path not found, gated model errors.
- Token counting fails for API models.
- Service model name differs from tokenizer id.

Fixes:

- Confirm `path` is either a valid model id, local model directory, or served model name for the selected backend.
- For API/service models, set `tokenizer_path` to a real tokenizer id/path when `path` is only a provider model name or server alias.
- For gated HuggingFace models, authenticate outside the reusable config.

## `trust_remote_code` and Custom Code

Symptoms:

- HF model/tokenizer refuses to load custom architecture.
- Config works manually but fails under OpenCompass worker.

Fixes:

- Add `trust_remote_code=True` to `tokenizer_kwargs` and/or `model_kwargs` when the model requires custom code.
- Review the model repository before enabling remote code execution.
- Keep this setting explicit in shared configs so reviewers see the trust boundary.

## Tokenizer Padding and Truncation

Symptoms:

- `pad_token_id is not set for this tokenizer`.
- Batched results differ from single-sample results.
- Generation ignores the latest user question after truncation.

Fixes:

- Prefer `tokenizer_kwargs=dict(padding_side='left', truncation_side='left')` for decoder-only generation.
- Set `pad_token_id` explicitly when EOS fallback is not acceptable.
- Use `batch_padding=False` for models that do not behave correctly with padded batches.
- Keep `max_seq_len` high enough for in-context examples plus user input; truncating the right side can remove the actual question.

## GPU Memory and Throughput

Symptoms:

- CUDA out of memory.
- vLLM/LMDeploy service starts but crashes under load.
- Workers queue forever due to resource requests.

Fixes:

- Lower `batch_size`, then `max_out_len`, then `max_seq_len`.
- For HF, tune `model_kwargs` such as `device_map`, dtype, quantization, or model size.
- For vLLM, tune `tensor_parallel_size`, `gpu_memory_utilization`, and model-specific memory settings.
- For LMDeploy, tune `engine_config` such as `tp`, `session_len`, and cache-related options supported by the installed LMDeploy version.
- Align `run_cfg.num_gpus` with actual local worker needs; use `0` for remote APIs.

## Torch, Transformers, vLLM, and LMDeploy Compatibility

Symptoms:

- Backend import errors after installing accelerator packages.
- Warnings that Transformers requires a newer Torch version.
- CUDA symbol or ABI errors.
- vLLM requires a specific Torch/CUDA stack.

Fixes:

- Treat CPU-only inspection as config/import validation, not real model execution validation.
- Use backend-specific installation guidance for vLLM/LMDeploy instead of mixing arbitrary versions.
- If Transformers warns that the installed Torch is too old for real model execution, upgrade in a compatible runtime before running HF inference.
- Use separate environments for HF-only inspection, vLLM execution, and LMDeploy execution when dependency constraints conflict.

## API Failure Case: Missing Key and Bad Resources

If an API evaluation fails immediately:

1. Check whether `key='ENV'` is used without the corresponding environment variable.
2. Check whether a placeholder like `YOUR_API_KEY` leaked into the config.
3. Check whether `run_cfg=dict(num_gpus=1)` is unnecessarily reserving GPU for a remote API.
4. Check whether `batch_size` is too high for the provider rate limit.
5. Run the no-network checker:

```bash
python scripts/check_api_model_config.py path/to/eval_config.py
```

Then fix the config before attempting a real provider call.
