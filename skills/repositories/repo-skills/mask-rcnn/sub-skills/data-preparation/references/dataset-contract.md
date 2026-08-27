# Dataset Contract

## Required subclass methods

A Mask_RCNN dataset class normally derives from `mrcnn.utils.Dataset` and defines a loader plus mask/reference methods.

```python
from mrcnn import utils

class MyDataset(utils.Dataset):
    def load_my_data(self, dataset_dir, subset):
        self.add_class("mydata", 1, "object")
        # for each image
        self.add_image("mydata", image_id="image-001", path="/data/image-001.png", extra="metadata")

    def load_mask(self, image_id):
        info = self.image_info[image_id]
        mask = ...       # [height, width, instance_count]
        class_ids = ...  # [instance_count]
        return mask.astype(bool), class_ids.astype("int32")

    def image_reference(self, image_id):
        return self.image_info[image_id].get("path", "")
```

Call `prepare()` after loading and before training/inference helper use:

```python
dataset = MyDataset()
dataset.load_my_data("/data/mydata", "train")
dataset.prepare()
print(dataset.class_names)
```

## Image contract

- `load_image(image_id)` returns an RGB `uint8`-like array of shape `[height, width, 3]`.
- The base implementation reads `image_info[image_id]['path']`, converts grayscale to RGB, and strips alpha channels.
- Override `load_image` for generated data such as Shapes, not for ordinary image files unless necessary.

## Mask contract

- `load_mask(image_id)` returns `(mask, class_ids)`.
- `mask` shape is `[height, width, instance_count]`.
- `class_ids` length equals `instance_count` and contains internal dataset class ids after `add_class`, not arbitrary labels.
- A mask may be `bool`, `uint8`, or 0/1 numeric, but downstream code expects binary behavior.
- Empty masks should be intentional; otherwise they will produce zero boxes and no positives.

`utils.extract_bboxes(mask)` computes `[y1, x1, y2, x2]` boxes from masks. Coordinates use the convention that `y2` and `x2` are outside the box in pixel space.

## Source and class ids

- `source` names must not contain a dot, because source/class keys are formed as `source.class_id`.
- Background class `BG` is always id 0.
- `add_class("balloon", 1, "balloon")` means the model's foreground class id for balloon is 1 after `prepare()`.
- `prepare()` builds mappings such as `class_from_source_map`, `image_from_source_map`, and `source_class_ids`.

## Resizing and mini-masks

`mrcnn.model.load_image_gt()` loads image/mask, resizes them consistently, optionally augments, extracts bboxes, builds `active_class_ids`, and optionally minimizes masks.

Config choices:

- `IMAGE_RESIZE_MODE = "square"`: resize and pad to a square, common for training/prediction.
- `IMAGE_RESIZE_MODE = "pad64"`: pad to multiples of 64, useful for inference on arbitrary sizes.
- `IMAGE_RESIZE_MODE = "crop"`: random crop; training only.
- `USE_MINI_MASK = True`: store instance masks in `MINI_MASK_SHAPE` to save memory; expand when needed.

## Augmentation safety

`load_image_gt(..., augmentation=...)` applies deterministic imgaug augmentation to image and mask. Only mask-safe augmenters should be used. The source allows classes named `Sequential`, `SomeOf`, `OneOf`, `Sometimes`, `Fliplr`, `Flipud`, `CropAndPad`, `Affine`, and `PiecewiseAffine`; test augmentations on masks before training.

## Validation checklist

- Dataset loader adds at least one class and one image.
- Every image path exists, unless `load_image` is intentionally synthetic.
- `dataset.prepare()` is called exactly after loading, before use.
- For several image ids, `load_image` returns `[H,W,3]` and `load_mask` returns `[H,W,N]`, `[N]` with matching `H`, `W`, and `N`.
- `utils.extract_bboxes(mask)` has positive-area boxes for non-empty instances.
- `load_image_gt` succeeds with the target Config and does not silently drop every instance after resize/crop.
