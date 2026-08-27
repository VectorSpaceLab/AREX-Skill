# PyTorch Workflows

This page distills the common PyTorch workflows that matter to future agents.

## 1) Safe local smoke: no pretrained weights

Use the bundled helper when you want a fast offline-first check that the package imports and the model forward path works.

```bash
python scripts/pytorch_tiny_inference.py --model resnest50 --image-size 64 --batch-size 1 --classes 1000 --check-splat
```

What this checks:

- the requested factory is importable;
- the classifier forward path returns the expected `(batch, classes)` output shape;
- `SplAtConv2d` runs a tiny shape smoke when `--check-splat` is set.

Why this is the safest default:

- it uses `pretrained=False` unless you request otherwise;
- it does not need ImageNet files;
- it does not need network access.

## 2) Torch Hub or package loading

Use the package namespace when the caller already has `resnest` installed.

```python
from resnest.torch import resnest50
model = resnest50(pretrained=False)
```

Use Torch Hub when the caller wants the public GitHub model entry point.

```python
import torch
model = torch.hub.load('zhanghang1989/ResNeSt', 'resnest50', pretrained=False)
```

Guidance:

- keep `pretrained=False` for offline and cache-safe checks;
- use `pretrained=True` only when you want the official ImageNet weights and accept cache/download behavior;
- the `root='~/.encoding/models'` signature value is not a reliable download target in this build.

## 3) Pretrained-weight smoke

If a caller explicitly wants pretrained weights, make the risk visible first.

```bash
python scripts/pytorch_tiny_inference.py --model resnest50 --pretrained
```

Constraints:

- `--pretrained` may download from the model weight host through the PyTorch Hub cache;
- classifier output must stay at 1000 classes for the pretrained load to succeed;
- if the environment is offline, retry with `--pretrained` omitted.

## 4) ImageNet verification flow

The repository's original verification recipe is a full validation pass over ImageNet-style raw image folders. This sub-skill only documents the required shape of that workflow; it does not ship a full ImageNet launcher.

Required ingredients:

- image folders laid out as `.../ILSVRC2012/train/<class>/...` and `.../ILSVRC2012/val/<class>/...`;
- validation transform stack: center crop, tensor conversion, and ImageNet normalization;
- a model factory call with `pretrained=True`;
- top-1 / top-5 accumulation in evaluation mode.

Useful interpretation notes:

- the verification path is for reporting ImageNet metrics, not for tiny smoke checks;
- the validation helper in the source tree uses a crop-style center crop and `DataParallel` when CUDA is enabled;
- it is normal for pretrained verification to require cache or network access.

## 5) When to use registry names versus direct factories

- Use direct factories from `resnest.torch` for `resnest50`, `resnest101`, `resnest200`, `resnest269`, and the fast variants.
- Use `get_model(name)` for registry-backed names such as `resnet50`, `resnet101`, `resnet152`, or the canonical ResNeSt names when you are wiring a config-driven training path.
- Do not expect the fast ablation factories to resolve through `get_model()` in this release.

## 6) When to stop and route elsewhere

- If the task is about MXNet / Gluon, route to the Gluon sub-skill.
- If the task is about Detectron2 backbones or COCO configs, route to the Detectron2 sub-skill.
- If the task is about full ImageNet or COCO dataset preparation, keep the heavy setup in the training/config references and avoid bundling a downloader.
