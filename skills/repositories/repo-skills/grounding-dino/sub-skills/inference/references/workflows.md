# GroundingDINO Inference Workflows

Use these workflows for single images only. COCO AP evaluation, folder pseudo-label export, web demos, and image-editing integrations are routed to sibling sub-skills.

## Choose The Interface

| Interface | Best fit | Trade-offs |
| --- | --- | --- |
| Bundled CLI helper | One-off image inference, validation, JSON output, reproducible handoff commands. | Requires config/checkpoint/image paths and writes files. |
| Function API | Custom Python control over transformed tensors, normalized boxes, annotation, and phrase extraction. | You manage model reuse and output conversion. |
| `Model` wrapper | Application code that wants `supervision.Detections` and class IDs. | Less control over token spans and phrase extraction internals. |

## Bundled CLI Helper

The helper lives at `scripts/grounding_dino_infer.py` under this sub-skill. It adapts the original single-image demo with safer parsing and explicit validation. It imports the installed `groundingdino` package but does not assume a source checkout exists.

Check help without weights:

```bash
python sub-skills/inference/scripts/grounding_dino_infer.py --help
```

Validate paths, thresholds, spans, image readability, and device before loading weights:

```bash
python sub-skills/inference/scripts/grounding_dino_infer.py \
  --config-file /path/to/GroundingDINO_SwinT_OGC.py \
  --checkpoint-path /path/to/groundingdino_swint_ogc.pth \
  --image-path /path/to/image.jpg \
  --text-prompt "cat . dog ." \
  --output-dir outputs/infer \
  --cpu-only \
  --validate-only
```

Run inference and write annotated image plus JSON:

```bash
python sub-skills/inference/scripts/grounding_dino_infer.py \
  --config-file /path/to/GroundingDINO_SwinT_OGC.py \
  --checkpoint-path /path/to/groundingdino_swint_ogc.pth \
  --image-path /path/to/image.jpg \
  --text-prompt "chair . person . dog ." \
  --output-dir outputs/infer \
  --box-threshold 0.35 \
  --text-threshold 0.25 \
  --device cuda \
  --json-output
```

Use class-list prompt construction:

```bash
python sub-skills/inference/scripts/grounding_dino_infer.py \
  --config-file /path/to/GroundingDINO_SwinT_OGC.py \
  --checkpoint-path /path/to/groundingdino_swint_ogc.pth \
  --image-path /path/to/image.jpg \
  --classes cat dog "traffic light" \
  --output-dir outputs/classes \
  --cpu-only \
  --json-output detections.json
```

The helper writes:

| Output | Meaning |
| --- | --- |
| `raw_image.jpg` | RGB copy of the input image after validation. |
| `pred.jpg` | Annotated image with pixel `xyxy` boxes and confidence labels. |
| JSON output | Caption, device, thresholds, token spans, output paths, normalized `cxcywh` boxes, pixel `xyxy` boxes, phrase labels, and confidences. |

## Token-Span CLI Workflow

Use token spans when the user wants exact phrases inside a sentence instead of free phrase extraction:

```bash
python sub-skills/inference/scripts/grounding_dino_infer.py \
  --config-file /path/to/GroundingDINO_SwinT_OGC.py \
  --checkpoint-path /path/to/groundingdino_swint_ogc.pth \
  --image-path /path/to/cat_dog.jpeg \
  --text-prompt "There is a cat and a dog in the image ." \
  --token-spans "[[[9, 10], [11, 14]], [[19, 20], [21, 24]]]" \
  --output-dir outputs/token-spans \
  --box-threshold 0.3 \
  --cpu-only \
  --json-output
```

When `--token-spans` is set, the helper ignores `--text-threshold` and filters phrase logits with `--box-threshold`, matching the demo behavior but using `ast.literal_eval` instead of unsafe `eval`.

## Python Function API Workflow

1. Pick a config/checkpoint pair that matches the desired backbone.
2. Call `load_model(config, checkpoint, device)` once and reuse the model.
3. Call `load_image(image_path)` for each image.
4. Build a lowercase prompt with category separators: `cat . dog . person .`.
5. Call `predict(model, image, caption, box_threshold, text_threshold, device)`.
6. Use `annotate(image_source, boxes, logits, phrases)` for a BGR visualization or convert boxes yourself.

Validation checks before running:

- Config, checkpoint, and image paths exist and are files.
- `torch.cuda.is_available()` is true before choosing `cuda`.
- Thresholds are floats in `[0, 1]`.
- Prompt is non-empty after stripping.
- Categories are separated by periods when multiple object classes are requested.

## Python Model Wrapper Workflow

Use this when integrating with code that expects `supervision.Detections`:

```python
import cv2
from groundingdino.util.inference import Model

image = cv2.imread("/path/to/image.jpg")
model = Model("/path/to/GroundingDINO_SwinT_OGC.py", "/path/to/groundingdino_swint_ogc.pth", device="cuda")
detections, labels = model.predict_with_caption(
    image=image,
    caption="cat . dog .",
    box_threshold=0.35,
    text_threshold=0.25,
)
```

For class IDs:

```python
detections = model.predict_with_classes(
    image=image,
    classes=["cat", "dog"],
    box_threshold=0.35,
    text_threshold=0.25,
)
```

`predict_with_classes` stores class indices in `detections.class_id`, based on phrase substring matching. Inspect labels if classes overlap textually.

## Output Interpretation

- More permissive `box_threshold` keeps more object queries; lower values can increase recall and false positives.
- More permissive `text_threshold` includes more prompt tokens in phrase labels; lower values can produce longer or noisier phrases.
- A valid run can produce zero detections. That usually means thresholds are too strict, the prompt does not match visible objects, or the checkpoint/config pair is wrong.
- The raw `predict` boxes are normalized `cxcywh`. Convert to pixel `xyxy` before drawing or integrating with many CV libraries.
- The helper's JSON emits both normalized `cxcywh` and pixel `xyxy`, making it safer for downstream agents to verify coordinate assumptions.
