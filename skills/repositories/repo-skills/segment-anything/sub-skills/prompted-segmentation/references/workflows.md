# Prompted Segmentation Workflows

## Choose Checkpoint, Model Type, and Device

Use `sam_model_registry` with a model type matching the checkpoint filename or user metadata.

```python
import torch
from segment_anything import SamPredictor, sam_model_registry

device = "cuda" if torch.cuda.is_available() else "cpu"
sam = sam_model_registry["vit_b"](checkpoint="/path/to/checkpoint.pth")
sam.to(device=device)
predictor = SamPredictor(sam)
```

Guidance:

- Prefer CUDA for production or large images when available; CPU works for correctness but can be slow.
- Keep the SAM model and torch prompt tensors on the same device.
- The NumPy `predict(...)` API handles moving prompt arrays to `predictor.device` internally.

## Load and Set the Image

`SamPredictor.set_image(...)` expects a NumPy image in `H x W x 3` layout.

```python
image = load_image_somehow()  # RGB uint8, shape H x W x 3
predictor.set_image(image, image_format="RGB")
```

Validation checklist:

- Shape is exactly 3-dimensional with 3 channels.
- Coordinate prompts are in original image pixels, not resized SAM pixels.
- `image_format` is exactly `"RGB"` or `"BGR"`.
- Call `set_image(...)` again whenever the image changes; previous embeddings are reset.

## Point Prompts

Foreground labels are `1`; background labels are `0`.

```python
point_coords = np.array([[500, 375]], dtype=np.float32)
point_labels = np.array([1], dtype=np.int32)
masks, scores, low_res_masks = predictor.predict(
    point_coords=point_coords,
    point_labels=point_labels,
    multimask_output=True,
)
best_index = int(np.argmax(scores))
best_mask = masks[best_index]
```

Use `multimask_output=True` for a single ambiguous point and pick the highest `scores` index if only one candidate is needed.

## Box Prompts

Boxes use `XYXY` order in original image pixels.

```python
box = np.array([425, 600, 700, 875], dtype=np.float32)
masks, scores, low_res_masks = predictor.predict(
    box=box,
    multimask_output=False,
)
mask = masks[0]
```

Use `multimask_output=False` for a well-specified box when the user expects one mask.

## Combine Box, Foreground Points, and Background Points

Use combined prompts to isolate a part inside a larger box or to suppress nearby distractors.

```python
box = np.array([425, 600, 700, 875], dtype=np.float32)
point_coords = np.array([[575, 750], [650, 820]], dtype=np.float32)
point_labels = np.array([1, 0], dtype=np.int32)
masks, scores, low_res_masks = predictor.predict(
    point_coords=point_coords,
    point_labels=point_labels,
    box=box,
    multimask_output=False,
)
```

## Iterative Refinement with `low_res_masks`

For a user who starts with one ambiguous point, then adds a box and foreground/background points:

```python
first_masks, first_scores, first_low_res = predictor.predict(
    point_coords=np.array([[500, 375]], dtype=np.float32),
    point_labels=np.array([1], dtype=np.int32),
    multimask_output=True,
)
best = int(np.argmax(first_scores))
mask_input = first_low_res[best][None, :, :]  # 1 x 256 x 256

refined_masks, refined_scores, refined_low_res = predictor.predict(
    point_coords=np.array([[500, 375], [530, 410]], dtype=np.float32),
    point_labels=np.array([1, 0], dtype=np.int32),
    box=np.array([450, 320, 700, 620], dtype=np.float32),
    mask_input=mask_input,
    multimask_output=False,
)
refined_mask = refined_masks[0]
```

Important shape rule: `predict(...)` expects a single selected low-res logit mask as `1 x 256 x 256`, not the whole `C x 256 x 256` array unless `C` is already `1`.

## Reuse Image Embeddings for Multiple Prompts

Do this when a user asks to try several prompts on the same image:

```python
predictor.set_image(image, image_format="RGB")
for box in boxes_xyxy:
    masks, scores, low_res = predictor.predict(
        box=np.asarray(box, dtype=np.float32),
        multimask_output=False,
    )
    collect(masks[0], scores[0])
```

`set_image(...)` is the expensive embedding step; repeated `predict(...)` calls reuse `predictor.features` until a new image is set or `reset_image()` is called.

## Torch Batch Boxes for One Image

For many boxes on the same image, use `predict_torch(...)` with transformed boxes.

```python
input_boxes = torch.tensor(boxes_xyxy, device=predictor.device, dtype=torch.float)
transformed_boxes = predictor.transform.apply_boxes_torch(input_boxes, image.shape[:2])
masks, scores, low_res = predictor.predict_torch(
    point_coords=None,
    point_labels=None,
    boxes=transformed_boxes,
    multimask_output=False,
)
```

Expected shapes for `B` boxes are `masks: B x 1 x H x W`, `scores: B x 1`, and `low_res: B x 1 x 256 x 256`.

## Embedding Handoff

```python
predictor.set_image(image, image_format="RGB")
image_embedding = predictor.get_image_embedding()
```

The embedding is typically `1 x 256 x 64 x 64` for SAM v1. Use it for advanced prompt reuse or ONNX mask-decoder handoff. For ONNX export, browser inference, and demo integration, route to `../onnx-and-browser/`.

## Use the Bundled Helper Template

The bundled script accepts a user checkpoint, image path, model type, prompt arguments, and optional output path. It performs no downloads and `--help` is safe:

```bash
python sub-skills/prompted-segmentation/scripts/predictor_prompt_template.py --help
```
