# OpenChat serving troubleshooting

Use this guide for `python -m ochat.serving.openai_api_server`, `/v1/models`, and `/v1/chat/completions` failures. For launch patterns see [deployment.md](deployment.md); for payload fields see [api-reference.md](api-reference.md).

## Fast triage checklist

1. Run `./scripts/run_openchat_server.sh --help` in the target environment to confirm the installed module imports and to inspect exact vLLM flags.
2. Confirm `--model` points to available weights/tokenizer and that `--model-type` is correct or auto-detectable from `openchat.json`.
3. Confirm CUDA, PyTorch, vLLM, and Ray are installed in the same Python environment used for launch.
4. Query `/v1/models` after startup and use one returned `id` as the JSON request `model`.
5. Keep requests under the model context length and reduce `max_tokens` when needed.
6. If the server uses `--api-keys`, include `Authorization: Bearer ...` on every request.

## Import-time errors: FastAPI, vLLM, Ray, CUDA

Symptoms:

- `ModuleNotFoundError: No module named 'fastapi'`
- `ModuleNotFoundError: No module named 'vllm'`
- `ModuleNotFoundError: No module named 'ray'`
- vLLM/PyTorch errors about CUDA, missing kernels, incompatible GPU architecture, or no visible devices.

Actions:

- Install and launch from an environment that contains OpenChat plus serving dependencies from the package metadata: `fastapi`, `uvicorn`, `ray`, `vllm>=0.4.0`, `torch`, `transformers`, and tokenizer/model dependencies.
- Verify the same Python executable can import the serving stack:

  ```bash
  python - <<'PY'
  import torch, ray, vllm, fastapi, uvicorn
  print('torch', torch.__version__)
  print('cuda available', torch.cuda.is_available())
  print('cuda devices', torch.cuda.device_count())
  print('ray', ray.__version__)
  print('vllm', vllm.__version__)
  PY
  ```

- If `torch.cuda.is_available()` is false, do not expect model serving to work. Fix the driver/CUDA/PyTorch environment first.
- If the GPU is older and does not support `bfloat16`, retry with `--dtype float16` as recommended by the README.
- For tensor parallel serving, ensure visible GPU count is at least `--tensor-parallel-size` and include `--engine-use-ray --worker-use-ray`.

## `--model` versus `--model-type` auto-detect failures

Symptoms:

- Startup fails while trying to load `openchat.json`.
- Startup reaches tokenizer/model loading with the wrong template or context length.
- Client `model` names do not match the intended OpenChat family.

Cause:

- If `--model-type` is omitted, the server calls Hugging Face cache resolution for `openchat.json` inside the launch `--model` repository/directory and reads `model_type` from it.

Actions:

- Pass `--model-type` explicitly when serving weights that do not include OpenChat's `openchat.json` metadata.
- Use one of the installed model-type keys: `openchat_3.6`, `openchat_v3.2`, `openchat_v3.2_mistral`, `openchat_v3.2_gemma_new`, `chatml_8192`, `zephyr_mistral`, `gemma_it`, or `llama3_instruct`.
- After startup, query `/v1/models` and use that response for client-side `model` values.

## HTTP 404: model does not exist

Symptom:

```json
{"object":"error","message":"The model `...` does not exist.","type":"invalid_request_error"}
```

Cause:

The JSON request `model` is not in the server's allowed names. The allowed set is the launch `--model-type` plus that type's serving aliases.

Actions:

1. Query the server:

   ```bash
   curl -s http://localhost:18888/v1/models | python -m json.tool
   ```

2. Use one returned `id` in `/v1/chat/completions`.
3. Do not send the Hugging Face repo id as the request `model` unless `/v1/models` returns that exact string.

Common fix examples:

| Launch `--model-type` | Valid request `model` values |
|---|---|
| `openchat_3.6` | `openchat_3.6` |
| `openchat_v3.2_mistral` | `openchat_v3.2_mistral` or `openchat_3.5` |
| `openchat_v3.2_gemma_new` | `openchat_v3.2_gemma_new` or `openchat_3.5_gemma_new` |

## HTTP 400: context length exceeded

Symptom:

```text
This model's maximum context length is N tokens. However, you requested M tokens (... in the messages, ... in the completion). Please reduce the length of the messages or completion.
```

Cause:

The server tokenizes `messages` first, then checks `input_num_tokens + max_tokens <= model.max_length`. If `max_tokens` is omitted, it is set to the remaining context.

Actions:

- Reduce prompt length or chat history.
- Lower `max_tokens`.
- Choose a model type with a larger context length when appropriate.
- Check that `--model-type` is correct; for example `openchat_v3.2` has 4096 context while most other installed types have 8192.
- If using `n > 1`, remember that it increases generated outputs and memory pressure even though the context-length check is per generated sequence.

## HTTP 401 or invalid API key

Symptoms:

- `/v1/models` or `/v1/chat/completions` returns 401.
- Error `code` is `invalid_api_key`.

Cause:

The server was launched with non-empty `--api-keys`, so every endpoint depends on bearer-token authentication.

Actions:

- Send an exact configured key:

  ```bash
  curl -s http://localhost:18888/v1/models \
    -H "Authorization: Bearer ${OPENCHAT_API_KEY}"
  ```

- Ensure there is no extra whitespace around the token.
- If this is a local-only test service and no auth is desired, restart without `--api-keys`.
- For production exposure, keep API keys enabled and put HTTPS in front of the service.

## System prompt appears ignored

Symptom:

A request includes a `system` message, but responses behave as if it was absent.

Cause:

`AsyncTokenizer.tokenize` skips `system` messages unless the server was launched with `--enable-sys-prompt`.

Actions:

- Restart the server with `--enable-sys-prompt`.
- Confirm the request uses role `system` in the messages list.
- For template-level details, route to [../../prompting/SKILL.md](../../prompting/SKILL.md).

## `logit_bias` rejected or `stop` appears ineffective

Symptoms:

- Non-empty `logit_bias` returns `logit_bias is not currently supported` with HTTP 400.
- Custom `stop` strings do not stop generation as expected.

Cause:

The server explicitly rejects non-empty `logit_bias`. Although `stop` exists in the request schema, the implementation does not pass it into vLLM `SamplingParams`; it overrides stop behavior with OpenChat end-of-turn token ids and `ignore_eos=True`.

Actions:

- Remove `logit_bias` from requests.
- Use shorter `max_tokens` or application-side truncation if custom stop strings are required.
- Do not promise full OpenAI feature parity for tools/function calling, `logit_bias`, or custom stop strings.

## Streaming client problems

Symptoms:

- Client buffers until completion.
- Multiple `n` responses interleave confusingly.
- First content begins with a missing leading space.

Actions:

- Use a streaming-capable client and disable curl buffering with `curl -N`.
- Parse server-sent events and concatenate `delta.content` per `choices[].index`.
- Expect an initial role-only chunk for each index, followed by content chunks, finish chunks, then `data: [DONE]`.
- The server strips one leading space from the first generated text delta for readability.
- Reduce launch `--stream-period` for more frequent chunks.

## Server starts but generation fails or hangs

Likely causes:

- Model weights are still downloading or unavailable.
- GPU memory is insufficient for the model, context length, batch pressure, or tensor parallel plan.
- Ray worker initialization failed.
- vLLM version or CUDA kernels are incompatible with the installed PyTorch/CUDA stack.

Actions:

- Start with a local-only single request and small `max_tokens`.
- Watch server logs for vLLM engine or Ray worker failures.
- Reduce concurrency, batch pressure, and `max_tokens` before changing model code.
- For multi-GPU, verify Ray sees the intended devices and retry with explicit tensor-parallel flags.
- Try `--dtype float16` on hardware without bfloat16 support.

## Logging and privacy surprises

Symptoms:

- Prompt or generated text appears in log files.
- Request statistics appear in vLLM logs.

Cause:

When `--log-file` is set, OpenChat writes JSON records containing requests and outputs. vLLM also has its own request/stat logging flags.

Actions:

- Treat OpenChat log files as sensitive data.
- For online service patterns, use vLLM flags such as `--disable-log-requests --disable-log-stats` when available in the installed vLLM CLI.
- Keep logs on restricted storage and rotate with `--log-max-mb` and `--log-max-count`.

## Validation errors from request shape

Symptoms:

- HTTP 400 containing pydantic validation details.
- Request accepted by another OpenAI-compatible server but rejected here.

Actions:

- Send `messages` as a list of dicts with `role` and `content` strings.
- Include required field `model`.
- Use numeric values for `temperature`, `top_p`, penalties, `n`, `max_tokens`, and `seed`.
- Remove unsupported OpenAI tool/function fields.
- Confirm JSON content type: `-H "Content-Type: application/json"`.
