# Pytorch-UNet prediction and evaluation API reference

This reference distills the callable prediction, mask conversion, evaluation, and Dice metric contracts for Pytorch-UNet semantic segmentation. It is self-contained; it does not require opening repository source files.

## Imports

```python
import torch
from PIL import Image
from unet import UNet
from predict import predict_img, mask_to_image
from evaluate import evaluate
from utils.dice_score import dice_coeff, multiclass_dice_coeff, dice_loss
```

The repository is not packaged with console entry points. In a checkout-style use, run from a directory where top-level modules such as `predict`, `evaluate`, `unet`, and `utils` are importable, or install/place the checkout on `PYTHONPATH`.

## `predict_img`

Signature verified from the runtime source:

```python
predict_img(net, full_img, device, scale_factor=1, out_threshold=0.5)
```

| Argument | Expected value | Notes |
| --- | --- | --- |
| `net` | A `UNet`-compatible module | Must expose `n_classes` and return logits shaped `(N, C, h, w)`. The function calls `net.eval()` and runs under `torch.no_grad()`. |
| `full_img` | `PIL.Image.Image` | Width/height are used to resize prediction output back to the original image size. RGB images are the default CLI assumption because CLI constructs `UNet(3, ...)`. |
| `device` | `torch.device` | Model and preprocessed input must be on the same device. CPU is enough for functional inference; CUDA is optional acceleration. |
| `scale_factor` | `float`, default `1` | Passed to `BasicDataset.preprocess(None, full_img, scale_factor, is_mask=False)`. Must produce nonzero resized width and height. |
| `out_threshold` | `float`, default `0.5` | Used only when `net.n_classes == 1`; ignored for multiclass prediction. |

Return value:

- A NumPy array containing integer class IDs or a binary mask.
- Spatial shape is the original PIL image `(height, width)` after interpolation back to `full_img.size`.
- For `net.n_classes > 1`, prediction is `argmax(dim=1)` over logits.
- For `net.n_classes == 1`, prediction is `torch.sigmoid(output) > out_threshold`, then converted to `long` and squeezed.

Important behavior:

1. Input preprocessing scales and normalizes images through the same static preprocessing helper used by the dataset loader: HWC images become CHW arrays, grayscale images gain a channel axis, and values larger than 1 are divided by 255.
2. Network logits are interpolated to the original image size with `torch.nn.functional.interpolate(..., mode="bilinear")` before thresholding or `argmax`.
3. `predict_img` returns class indices, not display colors and not original mask pixel values. Use `mask_to_image` to convert indices to a PIL image.
4. The prediction CLI always constructs `UNet(n_channels=3, n_classes=args.classes, bilinear=args.bilinear)`. For grayscale or custom channel counts, use the API route with a matching `UNet(n_channels=...)` instead of the stock CLI.

## `mask_to_image`

Signature:

```python
mask_to_image(mask: np.ndarray, mask_values)
```

Purpose: convert predicted class indices into a `PIL.Image.Image` using the `mask_values` stored in a training checkpoint or inferred by a dataset loader.

Input conventions:

| Input | Meaning |
| --- | --- |
| `mask` 2-D array `(H, W)` | Class ID per pixel. Values are expected to be integer IDs such as `0`, `1`, `2`, ... |
| `mask` 3-D array | Collapsed by `np.argmax(mask, axis=0)` before mapping values. This supports class-score/probability style arrays shaped `(C, H, W)`. |
| `mask_values == [0, 1]` | Produces a bool-mode array before PIL conversion. This is the common binary Carvana-style mapping. |
| `mask_values` list of scalar values | Produces an 8-bit grayscale-like array and assigns each class ID `i` to value `mask_values[i]`. |
| `mask_values` list of lists | Produces an 8-bit multichannel RGB/RGBA-like array with channel count `len(mask_values[0])`. |

Mapping rule:

```python
for i, v in enumerate(mask_values):
    out[mask == i] = v
```

Consequences:

- Class IDs are positions in `mask_values`, not necessarily the pixel values themselves.
- If a predicted class ID is greater than or equal to `len(mask_values)`, no assignment handles it and those pixels remain zero in the output image.
- For RGB-like palettes, every item in `mask_values` should have the same channel length and values represent output bytes.
- For binary `[0, 1]`, PIL receives a bool array. If a downstream format needs visible 0/255 masks, convert explicitly after `mask_to_image` or use `mask_values=[0, 255]` when that matches the training labels.

## Prediction checkpoint loading

Training saves a raw model `state_dict` and adds non-parameter metadata:

```python
state_dict = model.state_dict()
state_dict["mask_values"] = dataset.mask_values
torch.save(state_dict, checkpoint_path)
```

Prediction loading pattern:

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
net = UNet(n_channels=3, n_classes=classes, bilinear=bilinear)
net.to(device=device)
state_dict = torch.load(checkpoint_path, map_location=device)
mask_values = state_dict.pop("mask_values", [0, 1])
net.load_state_dict(state_dict)
```

Keep `mask_values` after popping it; it is required for accurate output image reconstruction. If it is absent, `[0, 1]` is only a safe default for a known binary/class-index mask workflow.

Checkpoint compatibility requires the same model construction choices used during training: input channels, class count, bilinear flag, and any architecture modifications. A `n_classes=2` checkpoint will not load into `UNet(..., n_classes=1)`, and default transposed-convolution checkpoints do not match `bilinear=True` models.

## `evaluate`

Signature:

```python
evaluate(net, dataloader, device, amp)
```

Purpose: compute mean validation Dice over a dataloader.

Dataloader contract:

- `len(dataloader)` must be available; the function uses it for the progress bar and denominator.
- Each batch is a mapping with keys:
  - `"image"`: tensor shaped `(N, C, H, W)`.
  - `"mask"`: integer label tensor shaped `(N, H, W)`.
- Images are moved to `device` as `float32` with channels-last memory format.
- Masks are moved to `device` as `long`.

Execution behavior:

1. Sets `net.eval()` and uses `@torch.inference_mode()`.
2. Wraps the loop with `torch.autocast(device.type if device.type != "mps" else "cpu", enabled=amp)`.
3. For `net.n_classes == 1`:
   - Asserts mask labels are in `[0, 1]`.
   - Applies `sigmoid` and threshold `0.5`.
   - Adds `dice_coeff(mask_pred, mask_true, reduce_batch_first=False)`.
4. For `net.n_classes > 1`:
   - Asserts mask labels are in `[0, n_classes[`; in Python terms, labels must satisfy `0 <= label < n_classes`.
   - One-hot encodes true masks and argmax predictions.
   - Computes `multiclass_dice_coeff` on `[:, 1:]`, so background class `0` is ignored.
5. Restores `net.train()` before returning.
6. Returns `dice_score / max(num_val_batches, 1)`. Empty dataloaders return zero-like accumulated score divided by `1`.

Evaluation returns a PyTorch scalar/tensor-like value, not a Python float unless the caller converts it with `float(score)` or `score.item()`.

## Dice metric helpers

### `dice_coeff`

```python
dice_coeff(input: torch.Tensor, target: torch.Tensor, reduce_batch_first=False, epsilon=1e-6)
```

- Asserts `input.size() == target.size()`.
- Accepts a single 2-D mask or higher dimensions according to `reduce_batch_first`.
- If both masks are empty for a reduction slice, it replaces the set sum with the intersection so the coefficient is well-defined.
- Returns the mean Dice coefficient across the reduced dimensions.

Use for binary predictions after applying sigmoid/threshold, or for already-aligned masks.

### `multiclass_dice_coeff`

```python
multiclass_dice_coeff(input, target, reduce_batch_first=False, epsilon=1e-6)
```

- Flattens class and batch dimensions with `input.flatten(0, 1)` and delegates to `dice_coeff`.
- Use with one-hot or probability/class-channel tensors shaped `(N, C, H, W)`.
- Evaluation ignores background externally by slicing `[:, 1:]` before calling it.

### `dice_loss`

```python
dice_loss(input, target, multiclass=False)
```

- Selects `multiclass_dice_coeff` when `multiclass=True`; otherwise uses `dice_coeff`.
- Calls the selected function with `reduce_batch_first=True`.
- Returns `1 - dice`, suitable as an additive loss term after converting logits to probabilities/one-hot-compatible tensors.

Training-style usage patterns:

```python
# Binary: logits shape (N, 1, H, W), target shape (N, H, W)
loss = dice_loss(torch.sigmoid(logits.squeeze(1)), target.float(), multiclass=False)

# Multiclass: logits shape (N, C, H, W), target labels shape (N, H, W)
probs = torch.softmax(logits, dim=1).float()
target_oh = torch.nn.functional.one_hot(target, num_classes).permute(0, 3, 1, 2).float()
loss = dice_loss(probs, target_oh, multiclass=True)
```

## Binary versus multiclass summary

| Mode | Model output | Prediction conversion | Evaluation target | Dice behavior |
| --- | --- | --- | --- | --- |
| Binary foreground | `n_classes == 1`, logits `(N,1,H,W)` | `sigmoid(logits) > threshold`; threshold flag matters | labels in `[0,1]` | `dice_coeff` over binary mask |
| Two-class/multiclass | `n_classes > 1`, logits `(N,C,H,W)` | `argmax(dim=1)`; threshold flag ignored | labels `0 <= y < C` | one-hot Dice over classes `1..C-1`, background class `0` ignored |

The repository's default prediction CLI uses `--classes 2`, so it follows the multiclass branch unless the user explicitly passes `--classes 1` and loads a matching one-channel checkpoint.
