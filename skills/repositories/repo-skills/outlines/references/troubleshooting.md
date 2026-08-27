# Cross-cutting Outlines troubleshooting

## Base install/import

Symptoms:

- `ModuleNotFoundError: outlines`.
- `pip check` reports dependency conflicts.
- Optional type modules raise import hints.

Actions:

1. Install the base package: `pip install outlines`.
2. Run a minimal import check:

   ```python
   import outlines
   from outlines.types import Regex, JsonSchema, CFG
   ```

3. Install optional extras only when the selected route needs them. For airport/country helper types, install the `airportsdata` or `iso3166` dependency.

## Wrong import path

`Chat` is not top-level in this source revision. Use:

```python
from outlines.inputs import Chat, Image, Audio, Video
```

## Output structure fails

Symptoms:

- Pydantic parsing fails.
- Regex does not match full output.
- CFG/backend errors.
- Provider rejects a schema.

Actions:

- Read `sub-skills/structured-generation/SKILL.md`.
- Validate samples before model calls.
- Remember that Outlines returns raw text; parse JSON after generation.
- Check backend compatibility and provider output-type support.

## Local model fails

Symptoms:

- Missing `torch`, `transformers`, `llama_cpp`, `mlx_lm`, or `vllm`.
- CUDA/MPS/VRAM/device errors.
- Model or tokenizer download/setup failures.

Actions:

- Read `sub-skills/local-models/SKILL.md`.
- Run the no-network prerequisite checker.
- Install only the selected optional stack.
- Verify hardware with the actual framework before claiming backend support.

## Provider call fails

Symptoms:

- API key or endpoint error.
- Rate limits, server 5xx, timeouts, or connection errors.
- Unsupported `Regex`/`CFG`/schema shape.
- Refusal/content filter/generation stop.

Actions:

- Read `sub-skills/remote-providers/SKILL.md`.
- Catch `outlines.exceptions.APIError` and branch on `retryable`.
- Retry only transient errors: rate limits, server errors, timeouts, and connection failures.
- Do not retry authentication, permission, not-found, malformed request/schema, or refusal errors without changing configuration or request content.
- Preserve provider/request IDs for debugging while redacting secrets.

## Prompt/template/input fails

Symptoms:

- Jinja `UndefinedError`.
- Template file include path problems.
- `Image` rejects a PIL image.
- Chat content shape unsupported by selected model/provider.
- Cache returns stale output.

Actions:

- Read `sub-skills/prompt-workflows/SKILL.md`.
- Render templates locally before model calls.
- Use `Image` only for PIL images with a format.
- Check whether the selected route supports vision/audio/video.
- Set or clear `OUTLINES_CACHE_DIR` deliberately; use `cache_disabled()` for one-off debugging.

## Safety failures

Do not use source examples that execute generated code as-is. If a workflow asks to generate Python code, parse and review the output as text; do not `eval`, `exec`, or shell it without a separate sandbox and explicit authorization.

Do not put API keys, tokens, model weights, private endpoints, or local environment paths into generated prompts, logs, or skill files.
