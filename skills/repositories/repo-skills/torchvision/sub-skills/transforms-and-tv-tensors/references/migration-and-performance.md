# Migration and Performance

## v1 to v2 Migration

For most classification pipelines, migration starts by changing the import:

```python
# Old
from torchvision import transforms

# New
from torchvision.transforms import v2
```

Then replace classes with v2 equivalents and prefer explicit dtype/range conversion:

```python
import torch
from torchvision.transforms import v2

pipeline = v2.Compose([
    v2.ToImage(),
    v2.Resize((256, 256), antialias=True),
    v2.CenterCrop((224, 224)),
    v2.ToDtype(torch.float32, scale=True),
    v2.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])
```

Key migration differences:
- Prefer `v2.ToImage()` over legacy PIL/tensor conversion chains when entering a tensor-first v2 pipeline.
- Prefer `v2.ToDtype(dtype, scale=True)` over ambiguous dtype conversions when range scaling matters.
- Use one transform call on the full sample instead of separately transforming image and target.
- Wrap boxes, masks, and keypoints with `tv_tensors` before geometry transforms.
- Add `SanitizeBoundingBoxes` or `SanitizeKeyPoints` after crops that can remove annotations.

## Migrating a PIL Pipeline

Legacy v1 PIL-style pipelines often look like `Resize -> CenterCrop -> ToTensor -> Normalize`. A v2 tensor-first replacement is:

```python
import torch
from torchvision.transforms import v2

pipeline = v2.Compose([
    v2.ToImage(),
    v2.Resize(256, antialias=True),
    v2.CenterCrop(224),
    v2.ToDtype(torch.float32, scale=True),
    v2.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])
```

If the source image is already a `torch.uint8` tensor in `C,H,W`, `ToImage()` is harmless and `ToDtype(float32, scale=True)` replaces the `[0,255] -> [0,1]` behavior commonly expected from `ToTensor()`.

## Detection Migration

Old code often transforms the image only and manually updates boxes. In v2, wrap target fields and let geometry transforms update them:

```python
from torchvision import tv_tensors
from torchvision.transforms import v2

height, width = image.shape[-2:]
target["boxes"] = tv_tensors.BoundingBoxes(target["boxes"], format="XYXY", canvas_size=(height, width))
if "masks" in target:
    target["masks"] = tv_tensors.Mask(target["masks"])

pipeline = v2.Compose([
    v2.RandomHorizontalFlip(p=0.5),
    v2.RandomIoUCrop(),
    v2.SanitizeBoundingBoxes(),
])
image, target = pipeline(image, target)
```

## Functionals and Kernels

Use class transforms for ordinary pipelines. Use `torchvision.transforms.v2.functional` when:
- Writing custom transforms with already-sampled parameters.
- Sharing an exact deterministic operation across multiple fields.
- Avoiding class-transform scripting surprises.

Low-level kernels such as type-specific resize or crop kernels are public but not the first-choice API. Use them mainly for advanced TorchScript cases involving boxes or masks.

## TorchScript Constraints

- `v2.Compose` is an eager Python composition utility, not the TorchScript composition primitive.
- For simple tensor-only scripted pipelines, compose scriptable modules with `torch.nn.Sequential`.
- Scripting a v2 class transform can produce a scripted v1-equivalent transform, which may differ slightly from eager v2 behavior.
- For v2-specific scripted logic, prefer scripting v2 functionals for pure tensor images.
- Functionals treat pure tensors as images in TorchScript; use low-level kernels for non-image types such as boxes or masks.
- Custom scripted transforms should inherit from `torch.nn.Module` and avoid arbitrary Python structures in scripted paths.

## Performance Defaults

Torchvision guidance favors:
- v2 transforms over v1 transforms.
- Tensor inputs over PIL images.
- `torch.uint8` for resize-heavy augmentation before final float conversion.
- Bilinear or bicubic resize modes with `antialias=True` where appropriate.
- `DataLoader(num_workers > 0)` for typical training input pipelines.

A good high-throughput pattern is:

```python
pipeline = v2.Compose([
    v2.ToImage(),
    v2.ToDtype(torch.uint8, scale=True),
    v2.RandomResizedCrop((224, 224), antialias=True),
    v2.RandomHorizontalFlip(),
    v2.ToDtype(torch.float32, scale=True),
    v2.Normalize(mean, std),
])
```

## Memory Format and Compile Notes

Transforms can be sensitive to input strides and memory format. Some preserve memory format, but not all details are guaranteed. Resizing operations often prefer channels-last inputs and may not benefit from `torch.compile`. Elementwise transforms such as normalization can be better candidates for compilation if the surrounding project already uses `torch.compile`.

Do not add `torch.compile` to small data preprocessing code by default. Benchmark in the target application before keeping it.

## Random Determinism

For reproducible debugging:

```python
import torch

torch.manual_seed(0)
out1 = pipeline(sample)
torch.manual_seed(0)
out2 = pipeline(sample)
```

For multi-worker data loading, seed workers through the DataLoader/worker initialization strategy used by the project. Avoid separately calling the same random transform on image and target, because it can sample different parameters.

## Custom Transform Migration

- If the old custom transform expects `(image, label)` or `(image, target)`, it can often remain a `torch.nn.Module` in a v2 `Compose`.
- If it must operate on arbitrary nested structures like built-in v2 transforms, subclass `v2.Transform`.
- Use `make_params(flat_inputs)` for random choices that must be shared across image, boxes, masks, and keypoints.
- Use `tv_tensors.wrap(output, like=input)` after tensor arithmetic that should preserve TVTensor metadata.
