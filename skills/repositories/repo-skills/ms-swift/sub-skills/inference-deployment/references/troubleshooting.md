# Inference and Deployment Troubleshooting

Use this checklist when `swift infer`, `swift app`, `swift deploy`, or a Python/OpenAI-compatible client fails.

## Backend or optional dependency is missing

Symptoms:

- `ModuleNotFoundError` or import error for `vllm`, `sglang`, or `lmdeploy`.
- CLI help works but accelerated backend launch fails.
- A minimal environment proves base Swift routes but not optional integrations.

Fix:

1. Treat accelerated backends as optional dependencies.
2. Re-run with `--infer_backend transformers` to separate Swift/model issues from backend install issues.
3. Install the backend version compatible with the machine’s CUDA/accelerator stack and model family.
4. Re-run `swift infer --help`, `swift deploy --help`, or `swift app --help` after install to confirm the console route still works.

## Backend/model support mismatch

Symptoms:

- Accelerated backend rejects a model architecture.
- Server starts to download/load then fails with unsupported model/config errors.
- A quantized or multimodal model works in `transformers` but not `vllm`, `sglang`, or `lmdeploy`.

Fix:

1. Verify the base model in `transformers` first.
2. Check whether the chosen backend supports the exact architecture, modality, quantization, and context length.
3. Remove adapters, quantization flags, speculative decoding, and reasoning parser flags until the base model loads.
4. Lower context/concurrency: `--vllm_max_model_len`, `--vllm_max_num_seqs`, `--sglang_context_length`, or `--lmdeploy_session_len`.
5. Use another backend or a merged/exported checkpoint if support is missing.

## QLoRA with accelerated backends

Symptoms:

- vLLM/SGLang/LMDeploy rejects a QLoRA adapter or quantization/adapter combination.
- Dynamic adapter loading fails even though the adapter works with `transformers`.

Fix:

- Use `--infer_backend transformers` for direct QLoRA inference.
- Or merge/export the adapter into a compatible full checkpoint before accelerated serving.
- Do not plan dynamic QLoRA serving on vLLM/SGLang/LMDeploy.

## LoRA adapter loading and `args.json`

Symptoms:

- `--adapters` fails to infer the base model/template.
- Adapter serves but outputs look like the base model.
- Multiple adapters appear missing from `/v1/models`.

Fix:

1. If the adapter was trained by Swift, check whether it includes Swift metadata such as `args.json`; Swift uses this to recover base model/template settings.
2. If metadata is absent, provide `--model`, template/system settings, and any required base args explicitly.
3. For `swift deploy`, use named mapping syntax for multiple adapters: `--adapters lora1=./adapter-a lora2=./adapter-b`.
4. Query `/v1/models` and confirm the base `--served_model_name` plus adapter names are present.
5. For vLLM dynamic LoRA, set `--vllm_max_lora_rank` at least as high as the adapter rank.
6. If backend dynamic LoRA is unsupported, merge/export the adapter or serve with `transformers`.

## `merge_lora` versus multiple LoRAs

Use `--merge_lora true` when:

- Only one adapter needs to be served.
- The target backend cannot dynamically load the adapter.
- You want to simplify deployment as a normal full checkpoint.
- QLoRA or backend adapter limitations block direct serving.

Avoid merging when:

- You need several adapters available under one server.
- You want to route by OpenAI `model` name to `lora1`, `lora2`, etc.
- You are using vLLM dynamic LoRA and have confirmed support for the adapter rank/model.

## Multimodal OOM

Symptoms:

- VLM fails during processor/model load or first request.
- OOM appears only when images/videos are present.
- Requests with multiple images fail even at small token counts.

Fix:

1. Reduce media processor limits before launching:

```bash
MAX_PIXELS=1003520
VIDEO_MAX_PIXELS=50176
FPS_MAX_FRAMES=12
```

2. Reduce backend context/concurrency:

```bash
--vllm_max_model_len 4096
--vllm_max_num_seqs 4
--vllm_gpu_memory_utilization 0.8
--vllm_enforce_eager true
```

3. For vLLM multimodal prompts, cap media per prompt:

```bash
--vllm_limit_mm_per_prompt '{"image": 5, "video": 2}'
```

4. If vLLM still OOMs, validate the same request with `transformers` and fewer/smaller media inputs.
5. For LMDeploy VLMs, tune `--lmdeploy_vision_batch_size` and verify LMDeploy version/model compatibility.

## vLLM multiple-image rejection

Symptoms:

- A Qwen-VL-style vLLM deployment accepts one image but rejects multiple images.
- Error mentions multimodal items per prompt or unsupported media count.

Fix:

- Ensure the prompt’s `<image>` tag count matches the image list length.
- Add `--vllm_limit_mm_per_prompt '{"image": 10, "video": 5}'` or a smaller machine-appropriate limit.
- Lower `--vllm_max_model_len` and `--vllm_max_num_seqs` if enabling more media increases memory pressure.
- Use OpenAI-style content blocks consistently when calling `/v1/chat/completions`.

## Stream mode versus batch/result saving

Symptoms:

- Result JSONL or logprobs are missing after inference.
- Batch inference is slow or writes one item at a time.
- Logprobs are absent in saved results.

Fix:

- Set `--stream false` for dataset/batch/result-saving workflows.
- Set `--result_path ./results.jsonl` explicitly.
- Set `--logprobs true` and `--top_logprobs N` only where the backend supports it.
- For deploy requests, keep `top_logprobs <= --max_logprobs`.
- Use `--write_batch_size` for large datasets.

## Local server unreachable

Symptoms:

- Client receives connection refused or timeout.
- `/v1/models` does not return a model list.
- `swift app --base_url ...` launches UI but generation fails.

Fix:

1. Start server bound to local host for local testing:

```bash
swift deploy --host 127.0.0.1 --port 8000 --model <model> --infer_backend <backend>
```

2. Check health and model list:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/v1/models
```

3. Use a base URL ending in `/v1` for OpenAI clients and `swift app --base_url`.
4. If `--api_key` is set, pass `Authorization: Bearer <key>` or configure the OpenAI/Swift client API key.
5. Confirm the server did not auto-select another free port after the requested port was busy.
6. Check server logs for model-load failure before debugging the client.

## Model name mismatch

Symptoms:

- Server returns an error like the requested model is not in the model list.
- Base model works but adapter model names fail.

Fix:

- Query `/v1/models` and use exactly one of the returned ids.
- Set `--served_model_name` explicitly if clients expect a stable public name.
- For named adapters, use the adapter key as the OpenAI `model` value.

## API key failure

Symptoms:

- Server returns `API key error`.

Fix:

- If the server was launched with `--api_key`, clients must send `Authorization: Bearer <same-key>`.
- For OpenAI Python client, set `OpenAI(api_key="<same-key>", base_url="http://127.0.0.1:8000/v1")`.
- For Swift `InferClient`, set `InferClient(api_key="<same-key>", ...)`.

## Multimodal request shape errors

Symptoms:

- Missing media, mismatched tags, or empty content errors.
- OpenAI client request works for text but not images/videos.

Fix:

- Tag style: match each `<image>`, `<video>`, and `<audio>` tag with a corresponding item in `images`, `videos`, or `audios`.
- OpenAI-style blocks: use content blocks with a `type` and media key, followed by text blocks.
- Use local paths or base64 data for no-external-network smoke tests.
- Keep media count low until the backend/model is known to support the shape.

## `swift app` launches but generation fails

Symptoms:

- Gradio page opens, but requests fail.
- Self-deployed app consumes GPU then errors.
- App connected to `--base_url` cannot list models.

Fix:

1. If using `--base_url`, verify `curl <base_url>/models` first.
2. If self-deploying, debug the equivalent `swift deploy` command first.
3. Set `--is_multimodal true` when auto-detection fails for a multimodal service.
4. Avoid `--share true` in notebook/DSW-like environments unless explicitly required.
5. After closing the UI, remember that background services may continue; terminate them from the runtime UI or process manager.

## Hard-case playbooks

### LoRA checkpoint to accelerated serving

1. Start with `transformers` direct inference and deterministic prompt to prove adapter behavior.
2. Decide whether one adapter or multiple adapters must be served.
3. For one adapter on unsupported dynamic backend, merge/export and serve as a full checkpoint.
4. For multiple adapters on vLLM, use named `--adapters`, set `--vllm_max_lora_rank`, and verify `/v1/models`.
5. Smoke-test base and each adapter model id with low `max_tokens`.

### Qwen-VL vLLM OOM plus multiple-image rejection

1. Reproduce with a single small local image and low `max_tokens`.
2. Set `MAX_PIXELS`, `VIDEO_MAX_PIXELS`, and `FPS_MAX_FRAMES` before server launch.
3. Lower `--vllm_max_model_len`, `--vllm_max_num_seqs`, and optionally set `--vllm_enforce_eager true`.
4. Add `--vllm_limit_mm_per_prompt '{"image": 2, "video": 0}'` for two-image tests, then raise only if needed.
5. If still failing, run the same prompt with `transformers` to separate Swift template/media handling from vLLM limits.
