# FCOS Inference API Reference

## Public constructor

The high-level package exposes `fcos.FCOS`:

```python
FCOS(model_name="fcos_R_50_FPN_1x", nms_thresh=0.6, cpu_only=False)
```

Verified from the package source and inspection:

- `model_name`: high-level API key used to choose a bundled config and pretrained weight URL.
- `nms_thresh`: copied into `cfg.MODEL.FCOS.NMS_TH` before model construction.
- `cpu_only`: when true, sets `cfg.MODEL.DEVICE = "cpu"`; otherwise uses `"cuda"`.

Model construction builds the detection model, loads the configured weight URL, creates transforms, and moves the model to the selected device. It may trigger network downloads and compiled extension imports.

## Methods

### `detect(im, min_confidence=None)`

- Input: a BGR `numpy.ndarray` image with shape `(H, W, 3)` as OpenCV would produce.
- Internal preprocessing: `ToPILImage`, tensor conversion, BGR/RGB transform according to config, normalization using config pixel mean/std, then `to_image_list` padding by size divisibility.
- Output: a list of dictionaries:

```python
{
  "box": [x1, y1, x2, y2],
  "score": 0.93,
  "label_name": "person",
  "label_id": 1
}
```

If `min_confidence` is `None`, the method uses a per-class threshold table stored for the selected model. A float applies the same threshold to every class.

### `show_bboxes(im, bbox_results)`

Draws boxes and class labels on a copy of the image and opens an OpenCV display window. Avoid this in headless automation; prefer serializing `detect` results instead.

### Helper conversions

- `_bbox_list_to_py_bbox_list(predictions)` converts FCOS `BoxList` predictions to ordinary Python dictionaries.
- `_py_bbox_list_to_bbox_list(py_bbox_list, im_size)` converts dictionaries back into `BoxList` with labels and scores.
- `list_available_models()` prints high-level API model keys.

## High-level API model keys

The inspected high-level API catalog contains:

- `fcos_R_50_FPN_1x`
- `fcos_syncbn_bs32_c128_MNV2_FPN_1x`

The repository also has many training/evaluation YAML configs under `configs/fcos`, but those are not automatically valid `model_name` keys for `FCOS(...)` unless they also appear in the high-level model-info dictionary.

## Color and size expectations

- The installed `fcos` command reads an image through image I/O as RGB, asserts 3 channels, flips to BGR, and resizes so the shorter side is 800.
- If you already use OpenCV (`cv2.imread`), the array is usually BGR and should not be flipped again before `FCOS.detect`.
- If you use PIL/skimage/imageio and get RGB, flip channels once before calling `detect`.
