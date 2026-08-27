# Pytorch-UNet prediction and evaluation workflows

Use these workflows to run or adapt Pytorch-UNet prediction/evaluation without relying on repository docs at runtime.

## 1. Prepare a checkpoint for prediction

A prediction checkpoint must be loadable into the same U-Net architecture that produced it.

```python
import torch
from unet import UNet

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
classes = 2
bilinear = False
net = UNet(n_channels=3, n_classes=classes, bilinear=bilinear)
net.to(device=device)

state_dict = torch.load("checkpoint_epoch5.pth", map_location=device)
mask_values = state_dict.pop("mask_values", [0, 1])
net.load_state_dict(state_dict)
```

Decision points:

- Use the `model-api` sub-skill if you need to identify the correct `n_channels`, `n_classes`, or `bilinear` settings from architecture/checkpoint evidence.
- Keep `mask_values` after loading. It is the palette/value map used by `mask_to_image`.
- If `mask_values` is missing, default `[0, 1]` is only a fallback for known binary or two-class index masks.

## 2. Predict one image with the API

```python
import torch
from PIL import Image
from unet import UNet
from predict import predict_img, mask_to_image

checkpoint = "checkpoint_epoch5.pth"
image_path = "image.jpg"
out_path = "image_mask.png"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
net = UNet(n_channels=3, n_classes=2, bilinear=False).to(device=device)
state_dict = torch.load(checkpoint, map_location=device)
mask_values = state_dict.pop("mask_values", [0, 1])
net.load_state_dict(state_dict)

img = Image.open(image_path)
mask = predict_img(net=net, full_img=img, device=device, scale_factor=0.5, out_threshold=0.5)
result = mask_to_image(mask, mask_values)
result.save(out_path)
```

Validation checks:

```python
assert mask.shape == (img.size[1], img.size[0])
assert result.size == img.size
```

Use the API path instead of the CLI when you need custom `n_channels`, custom preprocessing, a nonstandard palette, extra validation, or integration inside a larger pipeline.

## 3. Predict many images safely

The stock CLI loops over images one at a time. You can follow the same pattern in Python for better validation:

```python
from pathlib import Path
from PIL import Image
from predict import predict_img, mask_to_image

inputs = [Path("image1.jpg"), Path("image2.jpg")]
outputs = [p.with_name(p.stem + "_OUT.png") for p in inputs]

for image_path, output_path in zip(inputs, outputs):
    img = Image.open(image_path)
    mask = predict_img(net, img, device, scale_factor=0.5, out_threshold=0.5)
    pil_mask = mask_to_image(mask, mask_values)
    assert pil_mask.size == img.size
    pil_mask.save(output_path)
```

Guardrails:

- Make sure output parent directories exist.
- Ensure the number of explicit outputs equals the number of inputs.
- Do not assume the CLI batches tensors; it does per-image inference.

## 4. Use the prediction CLI wrapper for quick prediction

Preview a single-image prediction command against a user checkout:

```bash
python scripts/prediction_cli_wrapper.py --repo-root "$REPO_ROOT" -- --model checkpoint_epoch5.pth --input image.jpg --output image_mask.png --classes 2
```

Preview multiple images with automatic output names:

```bash
python scripts/prediction_cli_wrapper.py --repo-root "$REPO_ROOT" -- --model checkpoint_epoch5.pth --input image1.jpg image2.jpg image3.jpg --classes 2
```

Preview visualization without saving:

```bash
python scripts/prediction_cli_wrapper.py --repo-root "$REPO_ROOT" -- --model checkpoint_epoch5.pth --input image1.jpg image2.jpg --viz --no-save --classes 2
```

Add `--execute` to `prediction_cli_wrapper.py` only after the user approves reading checkpoint/images and any mask writes.

Remember:

- `--classes` and `--bilinear` must match the checkpoint.
- `--mask-threshold` affects only `--classes 1` checkpoints.
- `--scale` changes inference size, then prediction is resized back to original output size.

## 5. Convert class-index masks to output images

Use `mask_to_image` whenever your prediction is a class-index mask and you need a saved or displayable image.

Scalar palette example:

```python
mask_values = [0, 255]
mask = np.array([[0, 1], [1, 0]], dtype=np.int64)
img = mask_to_image(mask, mask_values)
assert img.size == (2, 2)
```

RGB palette example:

```python
mask_values = [[0, 0, 0], [255, 0, 0], [0, 255, 0]]
mask = np.array([[0, 1], [2, 0]], dtype=np.int64)
img = mask_to_image(mask, mask_values)
```

When adapting outputs for another tool, verify the exact image mode and pixel values expected by that tool. The binary checkpoint default `[0, 1]` is not the same as a high-contrast `[0, 255]` display mask.

## 6. Evaluate a validation dataloader

```python
import torch
from torch.utils.data import DataLoader
from evaluate import evaluate

# dataset must yield {"image": tensor(C,H,W), "mask": tensor(H,W)}
loader = DataLoader(dataset, batch_size=1, shuffle=False, drop_last=False)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
net.to(device=device)
score = evaluate(net, loader, device=device, amp=False)
print(float(score))
```

Dataloader requirements:

- Each batch dictionary must contain `image` and `mask`.
- Image channel count must equal `net.n_channels`.
- Mask labels must already be class IDs, not arbitrary grayscale/RGB palette values. Dataset preprocessing maps raw mask pixel values to class IDs via `mask_values`; if building a custom dataloader, reproduce that mapping.
- Binary mode requires labels in `[0, 1]`.
- Multiclass mode requires labels `0 <= label < net.n_classes`.

Evaluation returns the average over batches. It restores `net.train()` before returning, which is useful during training loops but surprising if you expected the model to remain in eval mode.

## 7. Compute Dice metrics directly

Binary Dice from masks:

```python
import torch
from utils.dice_score import dice_coeff

pred = torch.tensor([[[1, 0], [1, 1]]], dtype=torch.float32)
true = torch.tensor([[[1, 0], [0, 1]]], dtype=torch.float32)
score = dice_coeff(pred, true, reduce_batch_first=False)
```

Multiclass Dice from one-hot tensors:

```python
import torch
import torch.nn.functional as F
from utils.dice_score import multiclass_dice_coeff, dice_loss

labels = torch.tensor([[[0, 1], [2, 1]]], dtype=torch.long)
logits = torch.randn(1, 3, 2, 2)
probs = F.softmax(logits, dim=1).float()
target = F.one_hot(labels, 3).permute(0, 3, 1, 2).float()
score = multiclass_dice_coeff(probs[:, 1:], target[:, 1:], reduce_batch_first=False)
loss = dice_loss(probs, target, multiclass=True)
```

Use direct Dice calls when debugging loss/metric behavior or comparing synthetic masks. Use `evaluate` when validating a model over a dataloader.

## 8. Build a tiny no-download prediction smoke

The bundled script implements this sequence:

1. Create a synthetic RGB PIL image.
2. Instantiate `UNet(3, classes, bilinear)` on CPU by default.
3. Save a temporary dummy `state_dict` with `mask_values`.
4. Load the checkpoint and pop `mask_values`.
5. Call `predict_img` and verify mask dimensions and class ID bounds.
6. Call `mask_to_image` and verify output image size.
7. Optionally save the converted mask.
8. Print JSON for automation.

Run it before adapting a more expensive real prediction workflow:

```bash
python sub-skills/prediction-evaluation/scripts/prediction_smoke.py --classes 2 --width 32 --height 32
```

## 9. Decide CPU, CUDA, and AMP use

Functional prediction and Dice evaluation are CPU-capable. CUDA is optional acceleration and can improve throughput for larger images or validation sets when a compatible PyTorch build and GPU are present.

AMP appears in evaluation through `torch.autocast(..., enabled=amp)`. Treat AMP as optional:

- Set `amp=False` for portable CPU checks.
- Set `amp=True` when the runtime and device support autocast and the user wants acceleration.
- AMP does not change checkpoint format, mask conversion, class count, or Dice definitions.

## 10. Route adjacent work

- For architecture construction, checkpoint parameter compatibility, torch.hub model loading, or forward tensor shape checks, use `model-api`.
- For data directory layout, `BasicDataset`, `CarvanaDataset`, mask suffixes, data download cautions, and training/checkpoint creation, use `data-training`.
- Stay in this sub-skill for prediction CLI/API, output masks, evaluation dataloaders, and Dice metrics.
