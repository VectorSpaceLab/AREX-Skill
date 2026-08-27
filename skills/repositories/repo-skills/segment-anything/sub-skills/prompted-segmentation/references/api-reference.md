# Prompted Segmentation API Reference

This reference covers prompt-based prediction with Segment Anything v1.0. It is intentionally scoped to `SamPredictor`, model construction, prompt transforms, direct torch/batch prediction, and embedding handoff.

## Imports and Model Construction

```python
from segment_anything import SamPredictor, sam_model_registry
from segment_anything import build_sam, build_sam_vit_h, build_sam_vit_l, build_sam_vit_b
```

Available registry keys are:

- `default`: ViT-H builder, equivalent to `vit_h`.
- `vit_h`: ViT-H builder.
- `vit_l`: ViT-L builder.
- `vit_b`: ViT-B builder.

Construction pattern:

```python
sam = sam_model_registry[model_type](checkpoint=checkpoint_path)
sam.to(device=device)
predictor = SamPredictor(sam)
```

The checkpoint must match the model type. A ViT-B checkpoint loaded with `vit_h`, for example, fails during `load_state_dict` because parameter shapes and names do not match.

## `SamPredictor`

### Constructor

```python
SamPredictor(sam_model: Sam) -> None
```

`SamPredictor` wraps a `Sam` model, computes one image embedding with `set_image(...)`, and reuses that embedding for efficient repeated mask predictions from prompts.

### `set_image`

```python
SamPredictor.set_image(image: numpy.ndarray, image_format: str = "RGB") -> None
```

Inputs:

- `image`: `numpy.ndarray` with shape `H x W x 3`, dtype normally `uint8`, pixel values in `[0, 255]`.
- `image_format`: exactly `"RGB"` or `"BGR"`. If it differs from the model's `image_format` (`"RGB"` in SAM), channels are reversed internally.

Behavior:

- Resizes the image with `ResizeLongestSide(sam_model.image_encoder.img_size)`; SAM v1 models use a longest side of `1024`.
- Converts to a torch tensor on `predictor.device`, permutes to `1 x 3 x H' x W'`, preprocesses, and stores `predictor.features`.
- Must be called before `predict(...)`, `predict_torch(...)`, or `get_image_embedding()`.

### `predict`

```python
SamPredictor.predict(
    point_coords=None,
    point_labels=None,
    box=None,
    mask_input=None,
    multimask_output=True,
    return_logits=False,
) -> tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]
```

Prompt inputs use original image pixel coordinates before SAM resizing:

- `point_coords`: optional `N x 2` NumPy array of `(x, y)` coordinates.
- `point_labels`: required when `point_coords` is supplied; length `N`, with `1` foreground and `0` background.
- `box`: optional length-4 NumPy array in `XYXY` order: `[x0, y0, x1, y1]`.
- `mask_input`: optional low-resolution logits from a previous SAM prediction, shape `1 x 256 x 256` for the NumPy API.
- `multimask_output`: when `True`, returns 3 candidate masks; when `False`, returns 1 mask.
- `return_logits`: when `False`, output masks are boolean thresholded by `sam.mask_threshold`; when `True`, output masks are unthresholded logits at original image resolution.

Return values:

- `masks`: `C x H x W` NumPy array, where `(H, W)` is the original image size and `C` is `3` if `multimask_output=True`, else `1`.
- `iou_predictions`: length-`C` NumPy array of SAM's predicted mask quality scores.
- `low_res_masks`: `C x 256 x 256` NumPy array of low-resolution logits suitable for iterative refinement.

### `predict_torch`

```python
SamPredictor.predict_torch(
    point_coords: torch.Tensor | None,
    point_labels: torch.Tensor | None,
    boxes: torch.Tensor | None = None,
    mask_input: torch.Tensor | None = None,
    multimask_output: bool = True,
    return_logits: bool = False,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]
```

Use this when prompts are already torch tensors and already transformed to SAM's resized input frame. Shapes are batched:

- `point_coords`: `B x N x 2` transformed coordinates.
- `point_labels`: `B x N` labels.
- `boxes`: `B x 4` transformed `XYXY` boxes.
- `mask_input`: `B x 1 x 256 x 256` low-res logits.
- Returns `masks` as `B x C x H x W`, scores as `B x C`, and low-res logits as `B x C x 256 x 256`.

The predictor exposes `predictor.transform`, a `ResizeLongestSide` instance. For torch boxes from original image coordinates:

```python
boxes = torch.tensor([[425, 600, 700, 875]], device=predictor.device, dtype=torch.float)
transformed_boxes = predictor.transform.apply_boxes_torch(boxes, image.shape[:2])
masks, scores, low_res = predictor.predict_torch(
    point_coords=None,
    point_labels=None,
    boxes=transformed_boxes,
    multimask_output=False,
)
```

## Direct `Sam.forward` Batch API

`SamPredictor` is recommended for interactive prompting. Direct `sam(...)` is useful for batch inputs that already have transformed images and transformed prompts.

```python
outputs = sam(batched_input, multimask_output=False)
```

Each record in `batched_input` is a dictionary with:

- `image`: torch tensor shaped `3 x H' x W'`, already resized to SAM's input frame.
- `original_size`: `(H, W)` tuple for the original image.
- Optional `point_coords`: `B x N x 2`, already transformed.
- Optional `point_labels`: `B x N`.
- Optional `boxes`: `B x 4`, already transformed.
- Optional `mask_inputs`: `B x 1 x 256 x 256`.

Each output dictionary contains:

- `masks`: `B x C x H x W` boolean masks.
- `iou_predictions`: `B x C` scores.
- `low_res_logits`: `B x C x 256 x 256` logits.

## Image Embeddings

```python
embedding = predictor.get_image_embedding()
```

Returns a torch tensor with shape `1 x C x H_e x W_e`; for SAM v1 this is typically `1 x 256 x 64 x 64`. The method requires `set_image(...)` first. Use this for repeated prompt work or to prepare an embedding for ONNX/browser mask decoder workflows; do not use it as a replacement for full-image automatic mask generation.
