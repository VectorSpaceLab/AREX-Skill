# Provider Routing Reference

This reference distills the provider behavior used by FunClip's LLM tab.
The launcher routes in this order: `litellm/` -> `pegasus*` -> `qwen*` ->
OpenAI-compatible models (`gpt*`, `deepseek*`, `atlascloud/*`, `minimax/*`,
launcher-accepted `moonshot*`) -> `g4f*` -> unsupported-prefix error.

## Route table

| Model string entered in the UI | Launcher branch | Helper | What it does | Key / env behavior | Notes |
| --- | --- | --- | --- | --- | --- |
| `litellm/<provider>/<model>` | `model.startswith("litellm/")` | `litellm_call` | Strips the `litellm/` namespace, sends `messages`, sets `stream=False` and `drop_params=True` | Uses `apikey` when non-empty; optional `LITELLM_API_BASE` becomes `api_base` | Missing `litellm` raises an ImportError with an install hint. Empty model after stripping raises `ValueError`. Provider auth, not-found, rate-limit, timeout, and connection errors are logged and re-raised. |
| `qwen*` | `model.startswith("qwen")` | `call_qwen_model` | Passes the model string through to `dashscope.Generation.call(..., result_format='message')` | Assigns `dashscope.api_key = key`; this helper does not add its own env fallback | The helper prints the raw DashScope response before returning the message content. |
| `gpt*` / `deepseek*` / `atlascloud/<model>` / `minimax/<model>` / `moonshot*` | OpenAI-compatible branch | `openai_call` | Creates an `OpenAI` client and sends `messages` with the model string after any prefix stripping | AtlasCloud uses `ATLASCLOUD_API_KEY` and `ATLASCLOUD_API_BASE`; MiniMax uses `MINIMAX_API_KEY` and `MINIMAX_API_BASE`; generic routes use the key passed in | `deepseek*` maps to `https://api.deepseek.com`. `gpt-3.5-turbo*` maps to `https://api.moonshot.cn/v1`. Blank model after stripping `atlascloud/` or `minimax/` raises `ValueError`. |
| `g4f-<model>` | `model.startswith("g4f")` | `g4f_openai_call` | Removes the leading `g4f-` namespace before calling the g4f OpenAI-style client | No API key is used here | `g4f-` with no suffix becomes an empty model string and is invalid downstream. |
| `pegasus*` | `model.startswith("pegasus")` | `call_twelvelabs_pegasus` | Uses video understanding instead of transcript-only prompting, uploads local files when needed, and normalizes decimal-second ranges to SRT format | Uses the passed `apikey`, or `TWELVELABS_API_KEY` when the textbox is empty | Pegasus output must still match the FunClip bracketed timestamp format so `extract_timestamps` can read it. |

## Provider-specific key and base rules

- AtlasCloud and MiniMax are the only OpenAI-compatible routes with helper-level
  provider env fallback.
- `MINIMAX_API_BASE` can be overridden for region routing. Blank values fall
  back to the default global base.
- `MINIMAX_API_BASE_CN` is the mainland China base URL constant used by the
  tests and is safe to set when region routing is required.
- `LITELLM_API_BASE` is optional and only affects the LiteLLM path.
- `TWELVELABS_API_KEY` is used only when the key textbox is empty.
- `qwen` routes rely on the DashScope client; this helper does not read a
  provider-specific env var on its own.
- The launcher does not implement a helper-level fallback from a blank AtlasCloud
  or MiniMax key to `OPENAI_API_KEY`.

## Dependency notes

- `openai` 2.54.0 was verified with the OpenAI-compatible helper.
- `twelvelabs` 1.3.1 was verified with the Pegasus helper.
- `litellm` 1.96.2 was verified with the LiteLLM helper.
- `dashscope` is required for Qwen routing.
- g4f is best-effort and may be unstable; use it only when you are comfortable
  switching providers if the response fails or changes shape.

## No-live-call testing notes

Use the bundled smoke script first when you only need routing and format checks:

```bash
python scripts/provider_route_smoke.py --repo-root <repo-root>
```

When writing additional tests, patch or fake the client constructors and the
network-facing call methods instead of hitting the provider:

- `llm.openai_api.OpenAI`
- `llm.twelvelabs_api._resolve_video_context`
- `twelvelabs.TwelveLabs`
- `litellm.completion`
- `dashscope.Generation.call`
- `g4f.client.Client`

Assert the model string, base URL, key selection, prompt content, and returned
text. Do not assert on provider-side response metadata unless the helper itself
exposes it.
