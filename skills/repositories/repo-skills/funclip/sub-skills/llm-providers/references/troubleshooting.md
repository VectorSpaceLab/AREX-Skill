# Troubleshooting

Use this guide when the LLM tab fails before AI Clip can consume the output.
When in doubt, run `scripts/provider_route_smoke.py --repo-root <repo-root>`
first to prove that the local routing logic and timestamp normalization still
work without contacting any provider.

## Key and auth failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Missing API key: pass apikey or set ATLASCLOUD_API_KEY` | AtlasCloud route selected with an empty key textbox and no env fallback | Set the key in the UI or export `ATLASCLOUD_API_KEY`. Then rerun the LLM step. |
| `Missing API key: pass apikey or set MINIMAX_API_KEY` | MiniMax route selected with no provider key | Set `MINIMAX_API_KEY` or enter the key in the UI. Do not expect a fallback from `OPENAI_API_KEY`. |
| Provider auth / 401 / 403 | Wrong key, wrong model string, or wrong base URL | Check the provider prefix, the stripped model name, and the provider-specific key or base URL before retrying. |
| DashScope auth or model errors | Qwen key missing or the model name is not valid for DashScope | Set the DashScope key and confirm the selected model string. The helper prints the raw response, so inspect stdout for provider details. |
| LiteLLM auth, not-found, rate-limit, timeout, or connection errors | The upstream provider or proxy rejected the request | The helper logs the failure and re-raises the underlying LiteLLM exception. Retry, switch models, or correct the proxy. |

## Routing and prefix failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Model name is empty after stripping atlascloud/ prefix` | The UI value was `atlascloud/` without a model suffix | Enter a full model name such as `atlascloud/qwen/qwen3.5-flash`. |
| `Model name is empty after stripping minimax/ prefix` | The UI value was `minimax/` without a model suffix | Enter a full model name such as `minimax/MiniMax-M2.7`. |
| `Model name is empty after stripping litellm/ prefix` | The UI value was `litellm/` without a provider/model suffix | Enter a full LiteLLM route such as `litellm/openai/gpt-4o`. |
| Unsupported-prefix log from `llm_inference` | The model string did not match any launcher branch | Choose one of the supported prefixes or add the correct provider namespace. |
| Empty or bizarre g4f model after prefix stripping | The string started with `g4f-` but had no suffix | Use a full g4f model name such as `g4f-gpt-3.5-turbo`. |
| `moonshot*` behaves differently from the other OpenAI-compatible routes | The launcher accepts it, but the helper only hard-codes a Moonshot base for `gpt-3.5-turbo*` model names | Verify the exact model string and base URL you intend to use before relying on this branch. |

## Pegasus and video-understanding failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Pegasus requires a video input; please upload a video first.` | Pegasus was selected without a video file | Upload a video before running LLM inference. Pegasus does not work transcript-only. |
| `Video source not found: ...` | The local video path is invalid | Point to an existing file or use a public URL. |
| Local upload never becomes ready | The asset is still processing or the network is unstable | Wait for processing to finish. The helper polls for up to 300 seconds. If it still fails, retry with a smaller file or a stable network. |
| Pegasus output looks like `12.5-15.0` | The response was not normalized into SRT form | Re-run with the bundled Pegasus prompt and confirm that the normalizer is active. |

## Timestamp parsing failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `extract_timestamps` returns `[]` | The model output is not in bracketed SRT form | Make sure each line contains `[HH:MM:SS,mmm-HH:MM:SS,mmm]` and re-run AI Clip. |
| Some ranges parse but others do not | One or more ranges are reversed, malformed, or missing brackets | Fix the prompt or normalize the Pegasus output, then run the smoke script again. |
| AI Clip trims the wrong section | The timestamp text no longer matches the subtitle transcript | Re-run LLM inference with a prompt that keeps the ranges aligned to the transcript or video scene boundaries. |

## Provider-specific recovery checklist

1. Identify the route from the model prefix.
2. Confirm the provider key or env var for that route.
3. Confirm the stripped model string is not empty.
4. Confirm the output uses bracketed SRT ranges.
5. Re-run the bundled smoke script before a live provider retry when the issue
   looks local.
6. If the route is Pegasus, verify that a video input is present and readable.

## When to switch providers

- Switch away from g4f if you only need a stable prompt-format check.
- Switch away from a rate-limited or timeout-prone provider if you need to
  confirm the AI Clip prompt format quickly.
- Switch to Pegasus only when you need visual or audio context that the
  transcript route cannot capture.
