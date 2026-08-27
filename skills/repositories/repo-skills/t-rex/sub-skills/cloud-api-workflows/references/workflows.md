# T-Rex2 Cloud API Workflows

The commands below use only the generated skill's bundled scripts and the installed `trex` package. They do not require the original repository checkout.

## Shared inputs

### Token handling

Live API calls require a DeepDataSpace T-Rex2 API token. Supply it by either method:

```bash
export T_REX_API_TOKEN='...'
```

or pass `--token '...'` to the script. Do not put tokens in prompt JSON, output JSON, shell history snippets, or logs that may be shared.

Use `--dry-run` first when building payloads. Dry-run mode validates files and schemas, converts images to data-URI payloads in memory, prints a compact payload summary, and makes no network request.

### Prompt JSON

Use a list of prompt-image objects:

```json
[
  {
    "image": "reference_or_target_image.jpg",
    "interactions": [
      {"type": "rect", "category_id": 1, "rect": [100, 120, 220, 260]}
    ]
  }
]
```

For generic visual prompting, include multiple prompt-image objects or one prompt image that is different from the target image. For interactive prompting, use the target image as the prompt image. Relative prompt-image paths are resolved from the prompt JSON file directory when possible.

## 1. Interactive visual prompt detection

Interactive prompting uses the same image for `--target-image` and the prompt object's `image` field.

Dry-run:

```bash
python sub-skills/cloud-api-workflows/scripts/run_visual_prompt_inference.py \
  --target-image images/example.jpg \
  --prompt-json prompts/interactive_prompt.json \
  --output-json outputs/interactive_detections.json \
  --dry-run
```

Live call:

```bash
python sub-skills/cloud-api-workflows/scripts/run_visual_prompt_inference.py \
  --target-image images/example.jpg \
  --prompt-json prompts/interactive_prompt.json \
  --output-json outputs/interactive_detections.json \
  --visualization-output outputs/interactive_annotated.jpg \
  --box-threshold 0.3
```

The output JSON contains the raw detection dictionary under `detections`:

```json
{
  "schema_version": 1,
  "workflow": "visual_prompt_inference",
  "return_type": ["bbox"],
  "prompt_images": 1,
  "detections": {
    "scores": [0.97],
    "labels": [1],
    "boxes": [[12, 34, 56, 78]]
  }
}
```

When `--visualization-output` is requested, the script filters detections by `--box-threshold`, converts lists to NumPy arrays, and calls `trex.visualize`. For additional rendering-only work, route to [visualization-and-demo](../../visualization-and-demo/SKILL.md).

## 2. Generic multi-reference visual prompt detection

Generic prompting detects on a target image using one or more reference images in the prompt JSON.

Example prompt JSON:

```json
[
  {
    "image": "references/ref1.jpg",
    "interactions": [
      {"type": "rect", "category_id": 1, "rect": [692, 338, 725, 459]},
      {"type": "rect", "category_id": 1, "rect": [561, 231, 634, 351]}
    ]
  },
  {
    "image": "references/ref2.jpg",
    "interactions": [
      {"type": "rect", "category_id": 1, "rect": [561, 231, 634, 351]}
    ]
  }
]
```

Run the same script as the interactive case:

```bash
python sub-skills/cloud-api-workflows/scripts/run_visual_prompt_inference.py \
  --target-image images/target.jpg \
  --prompt-json prompts/generic_prompt.json \
  --output-json outputs/generic_detections.json \
  --dry-run
```

Remove `--dry-run` only after confirming the payload summary and token availability.

## 3. Create a visual prompt embedding

Use this when the user wants a reusable visual embedding for a category from one or more prompted images. The script requests `return_type=['embedding']` in live mode and writes the returned base64 embedding text to the requested file.

Dry-run:

```bash
python sub-skills/cloud-api-workflows/scripts/create_visual_embedding.py \
  --target-image images/target.jpg \
  --prompt-json prompts/generic_prompt.json \
  --output-embedding outputs/category_embedding.txt \
  --dry-run
```

Live call:

```bash
python sub-skills/cloud-api-workflows/scripts/create_visual_embedding.py \
  --target-image images/target.jpg \
  --prompt-json prompts/generic_prompt.json \
  --output-embedding outputs/category_embedding.txt
```

The embedding output is a base64 text string suitable for `run_embedding_inference.py`. It is not a rendered image and should not be treated as a binary model checkpoint unless an external API response explicitly provides a different artifact.

## 4. Embedding-based detection

Use a base64 embedding text file created by the embedding script or otherwise obtained from a compatible T-Rex2 API response.

Dry-run:

```bash
python sub-skills/cloud-api-workflows/scripts/run_embedding_inference.py \
  --target-image images/new_target.jpg \
  --embedding-file outputs/category_embedding.txt \
  --output-json outputs/embedding_detections.json \
  --dry-run
```

Live call with optional visualization:

```bash
python sub-skills/cloud-api-workflows/scripts/run_embedding_inference.py \
  --target-image images/new_target.jpg \
  --embedding-file outputs/category_embedding.txt \
  --output-json outputs/embedding_detections.json \
  --visualization-output outputs/embedding_annotated.jpg \
  --box-threshold 0.3
```

## Choosing between workflows

| Need | Use |
|---|---|
| Detect more objects in the same image from drawn boxes/points | Interactive visual prompt detection |
| Detect in a target image using one or more reference images | Generic visual prompt detection |
| Reuse a visual category concept across future target images | Create a visual prompt embedding |
| Detect from a saved base64 embedding | Embedding-based detection |
| Draw, threshold, or convert an existing detection JSON | [visualization-and-demo](../../visualization-and-demo/SKILL.md) |

## Output handling

- Detection boxes are pixel coordinates `[x1, y1, x2, y2]` from the API postprocess step.
- `labels` are integer category ids inherited from the prompt interactions.
- `scores` are confidence scores. Use `--box-threshold` only for visualization filtering; the JSON output preserves the raw API detections.
- Live calls write only the explicitly requested output files. Dry-runs print summaries and do not write detection or embedding outputs.
