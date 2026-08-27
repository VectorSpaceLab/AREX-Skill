---
name: framework-integration
description: "Integrate Albumentations with PyTorch-style datasets, tensor
  conversion, optional extras, and DataLoader reproducibility."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Framework Integration

Use this sub-skill when a task involves PyTorch dataset integration, tensor outputs, optional framework extras, or errors importing `ToTensorV2` / `ToTensor3D`.

## Route Here For

- Adding Albumentations to a `torch.utils.data.Dataset.__getitem__` while keeping augmentation before tensor conversion.
- Fixing image, mask, batch, or volume tensor shapes produced by `ToTensorV2` or `ToTensor3D`.
- Explaining `pip install albumentations[pytorch]`, `albumentations[hub]`, and `albumentations[text]` optional dependencies.
- Debugging missing `A.ToTensorV2`, HWC/CHW confusion, mask transposition, `Normalize` ordering, dtype/range issues, or DataLoader worker reproducibility.

## Start With These References

- `references/pytorch-integration.md`: PyTorch dataset placement, `ToTensorV2`, `ToTensor3D`, shapes, dtypes, normalization, bboxes/keypoints, and worker seeding.
- `references/optional-dependencies.md`: Optional extras, import checks, and safe install guidance for PyTorch, Hub, and text features.
- `references/troubleshooting.md`: Symptom-to-fix playbooks for import, shape, dtype/range, mask, and reproducibility failures.
- `scripts/pytorch_dataset_template.py`: A tiny self-contained template/checker for dataset-style Albumentations pipelines.

## Boundaries

- For `Compose`, `ReplayCompose`, `strict`, `additional_targets`, and seed mechanics beyond PyTorch workers, use `../pipeline-composition/`.
- For selecting transforms such as crops, flips, color, dropout, or text augmentations, use `../transform-catalog/`.
- For bbox/keypoint coordinate formats, labels, volumes, and target validation contracts, use `../targets-and-formats/`.
- Keep model training loops, loss functions, optimizers, schedulers, and framework-specific trainer code out of scope unless they affect augmentation placement or returned sample format.

## Minimal Pattern

```python
import albumentations as A
from albumentations.pytorch import ToTensorV2

train_transform = A.Compose(
    [
        A.Resize(256, 256),
        A.HorizontalFlip(p=0.5),
        A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        ToTensorV2(),
    ],
    strict=True,
)

sample = train_transform(image=image_np, mask=mask_np)
image_tensor = sample["image"]  # C,H,W torch.Tensor
mask_tensor = sample["mask"]    # H,W torch.Tensor unless transpose_mask=True
```

## Checklist

- Install PyTorch support explicitly when tensor transforms are needed: `pip install "albumentations[pytorch]"` or install compatible `torch` separately.
- Keep Albumentations inputs as NumPy arrays in `H,W,C` images, `H,W` or `H,W,C` masks, and `D,H,W[,C]` volumes until the final tensor transform.
- Put `Normalize` before `ToTensorV2`; `ToTensorV2` does not scale or normalize values by itself.
- Use `transpose_mask=True` only when channel-first masks are expected by downstream code.
- Return bbox/keypoint values from Albumentations as metadata/list fields; `ToTensorV2` converts image/mask targets, not bbox/keypoint lists.
