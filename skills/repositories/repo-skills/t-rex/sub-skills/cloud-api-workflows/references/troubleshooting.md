# Cloud API Workflow Troubleshooting

Use this reference for T-Rex2 API tokens, network calls, prompt payloads, API polling, and embedding files. Route installation/package repair to the root troubleshooting reference. Route rendering-only issues to [visualization-and-demo](../../visualization-and-demo/SKILL.md).

## Quick triage

| Symptom | Likely cause | Recovery |
|---|---|---|
| Script errors that live mode needs a token | Neither `--token` nor `T_REX_API_TOKEN` was supplied. | Use `--dry-run` for validation, or provide a valid token for live calls. Never put the token in JSON files or committed logs. |
| `RuntimeError: API call failed ...` immediately after submit | API response `msg` was not `ok`; common causes are invalid token, quota/service denial, malformed payload, or endpoint-side validation. | Re-run with `--dry-run` to verify local schema; confirm token/quota/network; inspect the API error message without exposing the token. |
| `RuntimeError` after polling | Task terminal status was `failed`. | Reduce payload size, verify prompt coordinates/category ids, and retry if the service error is transient. Keep the failed response message for the caller. |
| Process appears to wait indefinitely | The wrapper polls while task status is `waiting` or `running` and has no timeout option. | Use an outer shell/process timeout for bounded jobs. If timeouts repeat, treat it as a service/network issue rather than a local GPU issue. |
| JSON parser error before network | Prompt JSON is malformed or does not match the expected list-of-objects schema. | Fix JSON syntax, ensure every prompt has `image` and non-empty `interactions`, and validate again with `--dry-run`. |
| Missing image error | `--target-image` or a prompt `image` path does not exist from the script's resolution rules. | Use absolute image paths, or place prompt images relative to the prompt JSON file. |
| API rejects payload or returns no useful boxes | Prompt boxes/points are out of image bounds, inverted, too small, or category ids do not group intended examples. | Check `rect` is `[x1, y1, x2, y2]` with `x1 < x2` and `y1 < y2`; keep the same `category_id` for the same category. |
| Embedding inference fails before network | Embedding file is empty or not base64 text. | Use the output of `create_visual_embedding.py`; do not pass a URL, binary `.safetensors` file, or JSON wrapper unless it contains the base64 embedding string expected by `TRex2APIWrapper`. |
| Visualization raises `AttributeError: 'float' object has no attribute 'item'` | The renderer expects score values with `.item()`; plain Python floats fail. | The bundled API scripts convert scores to NumPy arrays before rendering. For separate rendering, route to [visualization-and-demo](../../visualization-and-demo/SKILL.md). |

## Token and network boundary

- `TRex2APIWrapper(token)` sends the token in the HTTP `Token` header.
- Dry-run mode never calls the API and does not require a token.
- Live mode calls the DeepDataSpace service and requires network access, valid credentials, and available API quota.
- Do not log full request headers, environment variables, or shell commands that include real tokens.
- The cloud API workflow is not a local model workload; CUDA/ROCm/MPS availability is unrelated to API success.

## Payload-size and image issues

Images are base64-encoded into the JSON payload. Very large target or reference images can create large requests and slow uploads or service failures.

Recommended recovery steps:

1. Run the relevant script with `--dry-run` and inspect only the reported data-URI lengths and interaction counts.
2. Downscale overly large images before submission if the payload is excessive.
3. Avoid sending many reference images in a single prompt unless needed.
4. Keep prompt coordinates in the pixel coordinate system of each corresponding prompt image.

## Prompt mutation side effect

`convert_visual_prompt` replaces each prompt dictionary's `image` value with a base64 data URI in place. This can surprise code that expects to reuse the same prompt list after conversion.

Recovery pattern:

```python
import copy
from trex import TRex2APIWrapper

wrapper = TRex2APIWrapper(token)
payload = wrapper.convert_visual_prompt(target_image, copy.deepcopy(prompts))
```

The bundled scripts follow this pattern when they need both validation metadata and conversion.

## Return-type mistakes

- Use `return_type=['bbox']` for detection JSON.
- Use `return_type=['embedding']` when the required artifact is a visual embedding.
- If `visual_prompt_inference` is called without `"embedding"` in `return_type`, its second return value is `None`.
- If an embedding call returns no embedding, treat it as an API/result-schema failure and preserve the service message for debugging.

## Result schema mistakes

Expected detection result:

```json
{
  "scores": [0.97],
  "labels": [1],
  "boxes": [[12, 34, 56, 78]]
}
```

Common fixes:

- Keep `scores`, `labels`, and `boxes` the same length.
- Use boxes as four-value pixel coordinates, not normalized center-width-height boxes.
- Convert result arrays to JSON lists when storing them.
- Convert lists back to NumPy arrays or tensors before `trex.visualize`.

## Embedding-file mistakes

`run_embedding_inference.py` expects a text file whose contents are the base64 embedding string accepted by `TRex2APIWrapper.embedding_inference`.

Do not pass:

- A path to an image file.
- A JSON response file unless you extract the embedding field first.
- A URL string or binary checkpoint file.
- A token or any other credential.

If the service returns an external download link instead of direct base64 text, obtain the base64 embedding content required by the wrapper before using the bundled embedding inference script.
