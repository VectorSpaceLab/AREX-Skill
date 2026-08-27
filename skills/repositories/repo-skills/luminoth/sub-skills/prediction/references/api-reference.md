# Prediction API Reference

## Purpose

Use this reference when the task is to call Luminoth from Python instead of the
CLI.

## Verified public signatures

- `Detector(checkpoint=None, config=None, prob=0.7, classes=None)`
- `Detector.predict(images, prob=None, classes=None)`
- `read_image(path)`
- `vis_objects(image, objects, colormap=None, labels=True, scale=1, fill=30)`

## Detector

`Detector` is the main public inference wrapper.

### Behavior

- If neither `checkpoint` nor `config` is provided, it falls back to the
  `accurate` checkpoint alias.
- If `checkpoint` is provided, the detector resolves it through the checkpoint
  index before constructing the model.
- If `classes` is provided, it must be a subset of the model's class labels.
- The default probability threshold is `0.7`.
- The detector only supports the `fasterrcnn` and `ssd` model families.

### Return shape

`predict` returns either:

- a list of detected objects for one image, or
- a list of lists for multiple images.

Each object looks like this:

```python
{
    'bbox': [x_min, y_min, x_max, y_max],
    'label': 'person' or 0..C,
    'prob': 0.9876,
}
```

## `read_image(path)`

Returns raw image bytes read through TensorFlow's file APIs. It is the helper
used by the prediction path before PIL converts the bytes into an RGB image.

## `vis_objects(image, objects, ...)`

Returns a PIL image with bounding boxes and labels drawn.

### Important parameters

- `image`: NumPy array with shape `(H, W, 3)`.
- `objects`: one object dictionary or a list of objects.
- `labels`: set to `False` if you want boxes without labels.
- `scale`: enlarges or shrinks the drawn annotations.
- `fill`: alpha channel for the box fill color.

## Useful constraints

- The image and video CLI paths are not production serving paths.
- The demo server is for quick inspection and returns JSON only for POST image
  requests.
- Prediction cannot use arbitrary model types; only Faster R-CNN and SSD are
  supported by the public prediction code.

## What to read next

- `references/workflows.md` for CLI and server usage.
- `references/troubleshooting.md` for common inference failures.
- `../checkpoints/SKILL.md` if the checkpoint is missing or needs to be
  downloaded first.
