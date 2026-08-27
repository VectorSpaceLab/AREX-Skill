# Framework Integration Troubleshooting

## `A.ToTensorV2` Is Missing

Symptoms:

- `AttributeError: module 'albumentations' has no attribute 'ToTensorV2'`
- `ModuleNotFoundError` or `ImportError` when running `from albumentations.pytorch import ToTensorV2`

Likely cause: the optional PyTorch dependency is not installed or cannot be imported. The base package suppresses PyTorch import failures when populating the top-level namespace.

Fix:

```bash
pip install "albumentations[pytorch]"
```

Or install a project-compatible `torch` build first, then verify:

```python
import albumentations as A
from albumentations.pytorch import ToTensorV2
assert hasattr(A, "ToTensorV2")
```

## Image Tensor Has `H,W,C` or Wrong Channel Count

Likely causes:

- The input image was already `C,H,W` before Albumentations.
- `ToTensorV2` was not the final transform.
- The dataset returned the pre-transform image instead of `result["image"]`.

Fix:

```python
assert image_np.ndim in {2, 3}
assert image_np.ndim == 2 or image_np.shape[-1] in {1, 3, 4}
result = transform(image=image_np)
assert result["image"].shape[0] in {1, 3, 4}
```

Albumentations image inputs should be `H,W,C` or `H,W`; `ToTensorV2` returns `C,H,W` or `1,H,W`.

## Mask Shape Is Not Channel-First

Default behavior is intentional: `ToTensorV2` keeps masks in their original shape unless `transpose_mask=True` and the mask has a channel dimension.

Use default behavior for class-index segmentation masks:

```python
ToTensorV2()  # H,W mask stays H,W
```

Use channel-first mask behavior only when the model expects mask channels:

```python
ToTensorV2(transpose_mask=True)  # H,W,C mask becomes C,H,W
```

For stacked masks, `N,H,W,C` becomes `N,C,H,W` only when `transpose_mask=True`; `N,H,W` remains `N,H,W`.

## Values Are `uint8` Instead of Float

`ToTensorV2` converts arrays to tensors but does not scale or normalize. If image tensors are `torch.uint8` in `[0, 255]`, add `Normalize` or `ToFloat` before tensor conversion.

```python
A.Compose([
    A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
    ToTensorV2(),
])
```

Keep masks out of image normalization. Integer masks should usually remain integer labels.

## `Normalize` After `ToTensorV2` Fails or Does Nothing Useful

Albumentations transforms before `ToTensorV2` operate on NumPy arrays. Place tensor conversion last:

```python
# Correct order
A.Compose([A.Resize(256, 256), A.Normalize(), ToTensorV2()])
```

If a project needs torch-native postprocessing, do that outside Albumentations after the dataset receives `result["image"]`.

## Bboxes or Keypoints Are Not Tensors

`ToTensorV2` converts images and masks, not bboxes, keypoints, or label fields. Convert those in dataset code after augmentation:

```python
result = transform(image=image, bboxes=bboxes, labels=labels)
image = result["image"]
boxes = torch.as_tensor(result["bboxes"], dtype=torch.float32)
labels = torch.as_tensor(result["labels"], dtype=torch.long)
```

If boxes disappear or labels desynchronize, route to `../targets-and-formats/` for bbox/keypoint format and filtering rules.

## 3D Volume Shape Is Wrong

`ToTensor3D` expects `volume` and `mask3d` keys, not `image` and `mask` keys. It accepts `D,H,W,C` or `D,H,W` and returns `C,D,H,W` with a channel dimension added for single-channel input.

Validation:

```python
result = transform(volume=volume_np, mask3d=mask_np)
assert result["volume"].ndim == 4
assert result["mask3d"].ndim == 4
```

If a 3D mask must remain `D,H,W` or `D,H,W,C`, do not use `ToTensor3D` for that target; convert it manually after Albumentations or adapt the model input contract.

## DataLoader Workers Repeat the Same Augmentations

Use `A.Compose(seed=...)` for Albumentations-managed reproducibility. In PyTorch worker processes, Compose combines the base seed with `torch.initial_seed()` and resynchronizes after worker unpickling.

If repeated samples persist:

1. Check that one `Compose` instance is used in the dataset rather than manually reseeding transforms on every `__getitem__` call.
2. Remove calls to global `random.seed()` or `np.random.seed()` inside `__getitem__`.
3. Seed custom non-Albumentations randomness through PyTorch `worker_init_fn` or a `Generator`.
4. Confirm the DataLoader is not intentionally using `num_workers=0` plus a fixed sample order during a reproducibility test.

## Optional Hub or Text Imports Fail

- Hub serialization helpers need `huggingface_hub` or `albumentations[hub]`.
- Text rendering transforms need Pillow or `albumentations[text]`.
- These extras are independent of PyTorch. Installing `albumentations[pytorch]` does not install Hub or text dependencies.
