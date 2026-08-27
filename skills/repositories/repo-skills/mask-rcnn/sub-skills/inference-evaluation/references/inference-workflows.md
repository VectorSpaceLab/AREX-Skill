# Inference Workflows

## Minimal inference shape

```python
from mrcnn.config import Config
from mrcnn import model as modellib

class InferenceConfig(Config):
    NAME = "my_dataset"
    GPU_COUNT = 1
    IMAGES_PER_GPU = 1
    DETECTION_MIN_CONFIDENCE = 0
    NUM_CLASSES = 1 + 1
    IMAGE_MIN_DIM = 512
    IMAGE_MAX_DIM = 512

config = InferenceConfig()
model = modellib.MaskRCNN(mode="inference", config=config, model_dir="logs")
model.load_weights("weights.h5", by_name=True)
result = model.detect([image])[0]
```

`detect()` returns one dict per image with these keys:

- `rois`: `[N, 4]` bounding boxes in pixel coordinates.
- `class_ids`: integer class ids.
- `scores`: class probabilities.
- `masks`: `[H, W, N]` instance masks aligned to the original image shape.

## Image batching rules

- The input to `detect()` is a list of images.
- Its length must equal `config.BATCH_SIZE`.
- All images in the batch must have the same shape after resizing.
- `mold_inputs()` handles resize/pad/normalize and image metadata construction.
- `get_anchors(image_shape)` derives anchors for the resized image.

## Color splash

The Balloon sample's color splash postprocessing keeps predicted mask pixels in color and converts the rest to grayscale. The reusable rule is simple:

```python
gray = skimage.color.gray2rgb(skimage.color.rgb2gray(image)) * 255
mask = np.sum(masks, axis=-1, keepdims=True) >= 1
splash = np.where(mask, image, gray).astype(np.uint8)
```

The bundled `scripts/apply_color_splash.py` implements this from `image.npy` plus `mask.npy` or from a single image and a precomputed mask array.

## Inference config defaults

- `GPU_COUNT = 1`
- `IMAGES_PER_GPU = 1`
- `DETECTION_MIN_CONFIDENCE = 0` for inspection/debug workflows
- `IMAGE_RESIZE_MODE = "pad64"` is common for notebook-style inspection so arbitrary input sizes can be handled safely

## Practical checks

Before running on real images:

1. Load one image and visualize the shape after `resize_image()`.
2. Confirm the batch size matches the number of images passed to `detect()`.
3. Confirm the model loaded the expected checkpoint.
4. If detection masks are empty, inspect `NUM_CLASSES`, weight source, and input size/resize mode.
