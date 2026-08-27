# T-Rex2 Cloud API Reference

This reference describes the verified public package surface used by this sub-skill. Use the bundled scripts in `../scripts/` for routine calls; use this file when adapting code.

## Public import surface

```python
from trex import TRex2APIWrapper, visualize
from trex.model_wrapper import encode_image  # helper, not exported by trex.__all__
```

Verified installed facts:

| Object | Signature / contract | Notes |
|---|---|---|
| `TRex2APIWrapper` | `TRex2APIWrapper(token: str)` | Stores JSON headers with the token in the `Token` header. Treat the token as a secret. |
| `encode_image` | `encode_image(image)` | Accepts an image file path string or `PIL.Image.Image`; returns a raw base64 string without a data-URI prefix. |
| `convert_visual_prompt` | `convert_visual_prompt(self, target_image, prompts: List[Dict], return_type: List[str] = ['bbox'])` | Builds the API payload for visual prompts. Mutates each prompt dictionary by replacing `prompt['image']` with a `data:image/jpg;base64,...` URI. |
| `visual_prompt_inference` | `visual_prompt_inference(self, target_image, prompt: List[Dict], return_type: List[str] = ['bbox'])` | Converts the prompt, calls the API, postprocesses returned objects, and returns `(detection_result, base64_embedding_or_None)`. |
| `convert_embedding_prompt` | `convert_embedding_prompt(self, target_image, base64_embedding: str)` | Builds the API payload for embedding-based detection. |
| `embedding_inference` | `embedding_inference(self, target_image, base64_embedding: str)` | Converts the embedding prompt, calls the API, postprocesses returned objects, and returns `detection_result`. |
| `postprocess` | `postprocess(self, object_batches)` | Converts API object dictionaries to `{'scores': [...], 'labels': [...], 'boxes': [...]}`. |

## Visual prompt input schema

For the bundled scripts, prompt JSON is a list of prompt-image objects. Relative prompt-image paths are resolved from the prompt JSON file directory when possible.

```json
[
  {
    "image": "prompt-or-target-image.jpg",
    "interactions": [
      {
        "type": "rect",
        "category_id": 1,
        "rect": [159, 186, 337, 309]
      }
    ]
  }
]
```

The wrapper also documents point prompts:

```json
{
  "type": "point",
  "category_id": 1,
  "point": [159, 186]
}
```

Field rules:

- `image`: local image path in the bundled CLIs; file path string or `PIL.Image.Image` when calling the Python wrapper directly.
- `interactions`: non-empty list of rectangle or point prompts.
- `type`: `"rect"` for bounding boxes; `"point"` for single prompt points.
- `category_id`: integer category/group id. Reuse the same id for examples of the same category.
- `rect`: `[x1, y1, x2, y2]` in image pixel coordinates; `x1 < x2` and `y1 < y2`.
- `point`: `[x, y]` in image pixel coordinates.

Interactive and generic workflows use the same schema. Interactive prompting uses the target image itself as the prompt image. Generic prompting uses one or more separate reference images.

## Converted visual-prompt payload

`convert_visual_prompt(target_image, prompts, return_type)` returns a task dictionary like:

```json
{
  "model": "T-Rex-2.0",
  "image": "data:image/jpg;base64,...",
  "targets": ["bbox"],
  "prompt": {
    "type": "visual_images",
    "visual_images": [
      {
        "image": "data:image/jpg;base64,...",
        "interactions": [
          {"type": "rect", "category_id": 1, "rect": [159, 186, 337, 309]}
        ]
      }
    ]
  }
}
```

Important side effect: the method mutates the prompt objects passed to it. If code needs to log, reuse, or serialize the original prompt paths later, pass `copy.deepcopy(prompts)`.

Supported target requests observed in the wrapper are `"bbox"` and `"embedding"`:

- `return_type=['bbox']`: return detections only.
- `return_type=['embedding']`: return a base64 embedding string; detections may still be present in the raw result but are not the primary artifact.
- `return_type=['bbox', 'embedding']`: the wrapper can request both, but use only when both outputs are needed because it increases payload/result size.

## Visual-prompt result structure

`visual_prompt_inference(...)` returns:

```python
detection_result, base64_embedding_or_none = wrapper.visual_prompt_inference(...)
```

`detection_result` is JSON-serializable:

```json
{
  "scores": [0.97, 0.83],
  "labels": [1, 1],
  "boxes": [[12, 34, 56, 78], [90, 12, 140, 80]]
}
```

The second return value is a base64 string only when `"embedding"` is included in `return_type`; otherwise it is `None`.

## Embedding prompt schema

`convert_embedding_prompt(target_image, base64_embedding)` returns:

```json
{
  "model": "T-Rex-2.0",
  "image": "data:image/jpg;base64,...",
  "targets": ["bbox"],
  "prompt": {
    "type": "embedding",
    "embedding": "<base64 embedding text>"
  }
}
```

`embedding_inference(target_image, base64_embedding)` returns the same detection dictionary structure as visual-prompt inference.

## API status behavior

`call_api(task_dict)` posts the payload to the DeepDataSpace T-Rex detection task endpoint and then polls task status once per second.

Observed behavior:

1. `POST` returns JSON. If `json_resp['msg'] != 'ok'`, the wrapper raises `RuntimeError` with the response JSON.
2. On an OK create response, the wrapper extracts `data.task_uuid`.
3. It repeatedly calls the status endpoint while `data.status` is `waiting` or `running`.
4. If terminal status is `failed`, it raises `RuntimeError` with the API message.
5. If terminal status is `success`, it returns the full status JSON.

Boundary notes:

- The wrapper does not expose a timeout parameter; use an outer process timeout if a workflow must be time-bounded.
- Non-JSON HTTP responses, connectivity errors, quota errors, invalid tokens, and unexpected response shapes propagate as request/JSON/key errors or `RuntimeError` from the wrapper.
- The API wrapper performs live network calls only through `call_api`; `convert_visual_prompt` and `convert_embedding_prompt` are offline payload builders.

## Postprocess contract

`postprocess(object_batches)` expects a list of API object dictionaries like:

```json
[
  {"category_id": 1, "score": 0.97, "bbox": [12, 34, 56, 78]}
]
```

It returns:

```json
{"scores": [0.97], "labels": [1], "boxes": [[12, 34, 56, 78]]}
```

For drawing, convert `scores`, `labels`, and `boxes` to NumPy arrays or tensors before calling `trex.visualize`, because the renderer calls `.item()` on each score. The bundled scripts perform this conversion when `--visualization-output` is requested. For rendering-only tasks, route to [visualization-and-demo](../../visualization-and-demo/SKILL.md).
