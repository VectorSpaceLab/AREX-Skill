# Model Deployment Troubleshooting

## Provider auth or quota failure

**Symptom**: online module call fails with authentication, quota, model-not-found, timeout, or provider inspection errors.

**Recovery**

1. Confirm `source`, `model`, `url`, `api_key`, `timeout`, and model type.
2. Reproduce message formatting without provider calls using `scripts/model_surface_smoke.py`.
3. Ask for credentials/budget before retrying a real provider call.
4. Preserve provider error fragments, but do not reveal keys.

## Input inspection / unsafe history failure

**Symptom**: provider rejects a request after tool calls or streamed history.

**Recovery**

- Use online chat helper behavior: prior tool traces can be removed while current observations remain.
- Verify streamed tool calls merge by index and preserve list shape.
- Avoid resending stale untrusted tool payloads in a continuing conversation.

## Model type misclassification

**Symptom**: a provider model is treated as the wrong modality, for example VLM/STT/TTS/embed/image/video.

**Recovery**

- Run `python scripts/model_surface_smoke.py --model-name <name>`.
- If the model family is new, treat it as a code/update issue and refresh LazyLLM rather than hard-coding an unsupported mapping in application code.

## Local server fails to start

**Likely causes**: missing backend extra, missing model weights, insufficient GPU/CPU memory, port conflict, launcher unavailable, bad `pythonpath`, or security key mismatch.

**Recovery**

1. Confirm backend extra and model path/cache.
2. Check hardware and port availability.
3. Replace the model with a deterministic Python function wrapped in `ServerModule` to verify service wiring.
4. Only then run the real model backend.

## Fine-tuning/distillation cannot run

**Likely causes**: missing framework extra, no GPU, invalid dataset path/format, output path permissions, or insufficient time/budget.

**Recovery**

- Convert the task to a plan/config validation unless the user explicitly asked to run training.
- Verify dataset layout and target path before installing broad training stacks.
- Keep failures classified as optional backend blocks rather than core LazyLLM failures.

## Multimodal examples fail

**Likely causes**: missing provider SDK, local model, media codec, file path, or credentials.

**Recovery**

- Classify modality and backend first.
- Run only format/import checks by default.
- Ask before generating images/audio/video or sending media to a provider.
