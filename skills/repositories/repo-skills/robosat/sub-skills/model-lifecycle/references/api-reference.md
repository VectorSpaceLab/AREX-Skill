# API reference

## Shape contract

- Inputs are RGB images with 3 channels.
- Training masks are integer class indices with shape `[N, H, W]`.
- Model outputs are logits with shape `[N, C, H, W]`.
- Prediction buffers tiles and later removes the border overlap before writing files.
- Keep square image and tile sizes divisible by 32.

## Model blocks

| Object | Signature | Notes |
| --- | --- | --- |
| `ConvRelu` | `ConvRelu(num_in, num_out)` | 3x3 convolution with padding 1, followed by ReLU. Used as the basic decoder block. |
| `DecoderBlock` | `DecoderBlock(num_in, num_out)` | Nearest-neighbor upsample by 2, then `ConvRelu`. |
| `UNet` | `UNet(num_classes, num_filters=32, pretrained=True)` | ResNet50 encoder plus decoder blocks. The forward pass asserts that height and width are divisible by 32. |

### `UNet` notes

- `num_classes` controls the output channel count.
- `num_filters` sets the base decoder width.
- `pretrained=True` can trigger an ImageNet ResNet50 download on first use.
- The model expects three-channel RGB input.
- The forward pass returns logits; downstream code applies `argmax` or `softmax` as needed.

## Losses

| Object | Signature | Notes |
| --- | --- | --- |
| `CrossEntropyLoss2d` | `CrossEntropyLoss2d(weight=None)` | Wraps `NLLLoss` on `log_softmax(inputs, dim=1)`. `weight` should have one entry per class. |
| `FocalLoss2d` | `FocalLoss2d(gamma=2, weight=None)` | Uses the same input and target shapes as cross-entropy, but down-weights easy examples. `gamma=0` reduces to cross-entropy behavior. |
| `mIoULoss2d` | `mIoULoss2d(weight=None)` | Builds one-hot masks from the targets and returns the larger of the IoU loss and the NLL loss term. Useful mainly for binary segmentation. |
| `LovaszLoss2d` | `LovaszLoss2d()` | Lovasz-style loss with no class-weight argument. |

### Loss input assumptions

- `inputs` should be logits of shape `[N, C, H, W]`.
- `targets` should be integer labels of shape `[N, H, W]` with class ids starting at zero.
- The weighted losses expect weights to line up with `dataset.common.classes`.

## Metrics

| Object | Signature | Notes |
| --- | --- | --- |
| `Metrics` | `Metrics(labels)` | Accumulates binary-style counts and exposes `get_miou()`, `get_fg_iou()`, and `get_mcc()`. |

### `Metrics` notes

- `add(actual, predicted)` expects a single-sample ground-truth mask and the corresponding predicted logits or probabilities.
- The implementation is effectively binary-focused and is best matched to a background/foreground task.
- The `labels` constructor argument is kept for context but is not heavily used in the count logic.

## Transforms

| Object | Signature | Notes |
| --- | --- | --- |
| `ImageToTensor` | alias of `torchvision.transforms.ToTensor` | Converts a PIL RGB image to a float tensor in `[0, 1]`. |
| `MaskToTensor` | `MaskToTensor()` | Converts a PIL mask to a `long` tensor of class ids. |
| `ConvertImageMode` | `ConvertImageMode(mode)` | Converts a PIL image to a requested mode such as `RGB` or `P`. |
| `JointCompose` | `JointCompose(transforms)` | Applies a list of joint `(images, mask)` transforms in sequence. |
| `JointTransform` | `JointTransform(image_transform, mask_transform)` | Applies separate image and mask transforms while keeping them aligned. |
| `JointRandomVerticalFlip` | `JointRandomVerticalFlip(p)` | Randomly flips images and mask vertically with probability `p`. |
| `JointRandomHorizontalFlip` | `JointRandomHorizontalFlip(p)` | Randomly flips images and mask horizontally with probability `p`. |
| `JointRandomRotation` | `JointRandomRotation(p, degree)` | Randomly rotates images and mask by 90, 180, or 270 degrees with probability `p`. |

### Transform notes

- `JointRandomRotation` only accepts `90`, `180`, or `270` degrees.
- Training uses `ConvertImageMode("RGB")` for images and `ConvertImageMode("P")` for masks.
- Training and prediction both normalize RGB inputs with ImageNet mean and std.
- Training also uses `Resize`, `CenterCrop`, random flips, and random right-angle rotations from torchvision.

## Dataset and tile helpers

| Object | Signature | Notes |
| --- | --- | --- |
| `SlippyMapTiles` | `SlippyMapTiles(root, transform=None)` | Reads a slippy-map directory of files in `z/x/y.*` layout and yields `(image, tile)` pairs. |
| `SlippyMapTilesConcatenation` | `SlippyMapTilesConcatenation(inputs, target, joint_transform=None)` | Loads one or more input slippy-map roots plus a target mask root, checks tile alignment, and returns concatenated tensors. |
| `BufferedSlippyMapDirectory` | `BufferedSlippyMapDirectory(root, transform=None, size=512, overlap=32)` | Builds buffered tiles with border context for prediction or serving. |

### Dataset notes

- `SlippyMapTilesConcatenation` asserts that every input root has the same number of tiles and that the tile ids match between inputs and labels.
- The concatenation helper returns `(images, mask, tiles)` where `images` is the channel-concatenated tensor.
- `BufferedSlippyMapDirectory` requires `size >= 256` and `overlap >= 0`.
- The overlap should stay within neighboring tiles; it is intended to add context without spanning arbitrary gaps.
- `BufferedSlippyMapDirectory.unbuffer(probs)` expects `[C, H, W]` probabilities and removes the border overlap from every side.
- The prediction pipeline converts the tile coordinates to integers from the returned tensor-like tile id.

## Config helpers

| Object | Signature | Notes |
| --- | --- | --- |
| `load_config` | `load_config(path)` | Loads a TOML file into a Python dictionary. No extra validation is added. |
| `save_config` | `save_config(attrs, path)` | Writes a Python dictionary back to TOML. |

## Palette helpers

| Object | Signature | Notes |
| --- | --- | --- |
| `make_palette` | `make_palette(*colors)` | Builds a PIL palette from Mapbox color names. Used by mask rendering. |
| `continuous_palette_for_color` | `continuous_palette_for_color(color, bins=256)` | Builds the gradient palette used by probability PNG outputs. |

### Palette notes

- `colors` values in the dataset config must be valid names from the `Mapbox` color enum.
- Batch prediction encodes foreground probability into a single-channel palette PNG using a pink gradient.
- Serving uses the dataset palette to colorize mask outputs.
