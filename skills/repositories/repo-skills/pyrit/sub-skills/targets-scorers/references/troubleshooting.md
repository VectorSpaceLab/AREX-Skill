# Targets and Scorers Troubleshooting

## Credentials, endpoint, or deployment missing

Symptoms: authentication errors, 401/403, `None` endpoint/model values, or target constructor works but sends fail.

Recovery:
1. Confirm whether the target uses API key, Azure identity, token provider, or config-file initializer.
2. Keep secrets in environment/config/secret stores, not in prompts or generated command examples.
3. Verify endpoint, deployment/model name, API version, and organization/project settings with a minimal provider-native request if the user permits network access.
4. Use `TextTarget` for no-secret route validation; do not claim live target verification from a `TextTarget` smoke.

## Rate limits, retries, and timeouts

Symptoms: 429, transient 5xx, timeout, repeated retry collector entries, partial responses.

Recovery: lower concurrency; set target-specific rate-limit parameters; use PyRIT retry-aware exceptions; separate objective, adversarial, and scorer target traffic; log request IDs when providers expose them.

## Modality or capability mismatch

Symptoms: image/audio/video message rejected, system prompts ignored, multi-turn state missing, JSON/tool response unsupported.

Recovery:
1. Inspect `TargetCapabilities` and `TargetConfiguration`.
2. Ensure converters produce a data type accepted by the target.
3. Use message normalizers for chat history/system-message behavior.
4. Route converter stack changes to `converters-datasets` and attack composition to `attacks-scenarios`.

## HTTP target template or parser fails

Symptoms: prompt placeholder remains unsubstituted, response callback returns empty data, JSON key path missing, regex does not match.

Recovery: validate the raw HTTP request template with a tiny local fixture when possible; confirm the prompt placeholder; distinguish `HTTPTarget` raw request mode from `HTTPXAPITarget` API/form mode; write a small callback test before live sends.

## Browser/Playwright targets fail

Symptoms: browser executable missing, selectors not found, account/session prompt appears, WebSocket disconnects.

Recovery: install and verify browser dependencies only when the user authorizes browser automation; update selectors for the current UI; treat account/login steps and screenshots as sensitive artifacts.

## LLM scorer returns invalid JSON or unusable output

Symptoms: invalid JSON exceptions, score value not in rubric, rationale missing, score aggregation errors.

Recovery:
1. Check the scorer's system prompt/rubric and response handler.
2. Use a validator or a stricter JSON schema where supported.
3. Lower concurrency/temperature for scorer calls.
4. Preserve raw scorer output only if it contains no sensitive target data.

## Optional model/download-heavy targets

HuggingFace, GCG, some policy models, and media/speech paths may require optional packages, large downloads, GPUs, or service credentials. Keep them optional unless the task explicitly requires them; record skipped verification separately from base PyRIT readiness.
