# pytorch-semseg model zoo and API reference

This reference is self-contained runtime guidance for selecting architectures, building `get_model` payloads, and using package registries without reopening source files.

## Scope boundaries

- Model/API selection and registry inspection belong here.
- Dataset layouts and YAML validation belong to `data-and-configs`.
- Training and validation execution belong to `training-and-evaluation`.
- Single-image `test.py` inference belongs to `single-image-inference`.

## Model registry ids

`ptsemseg.models.get_model(model_dict, n_classes, version=None)` reads `model_dict["arch"]`, removes `arch`, and forwards the remaining keys to the selected model constructor. The `version` argument on `get_model` itself is not forwarded by the dispatcher; put version-like options inside `model_dict` when the constructor supports them.

| Model id | Constructor target | Verified constructor signature | Practical `get_model` payload | Notes |
| --- | --- | --- | --- | --- |
| `fcn32s` | `fcn32s` | `(self, n_classes=21, learned_billinear=False)` | `{"arch": "fcn32s"}` | `get_model` constructs the model and then calls `torchvision.models.vgg16(pretrained=True)` to initialize VGG layers. Avoid for smoke tests unless VGG weights are already cached or downloads are allowed. |
| `fcn16s` | `fcn16s` | `(self, n_classes=21, learned_billinear=False)` | `{"arch": "fcn16s"}` | Same implicit VGG pretrained side effect as `fcn32s`. |
| `fcn8s` | `fcn8s` | `(self, n_classes=21, learned_billinear=True)` | `{"arch": "fcn8s", "learned_billinear": True}` | Same implicit VGG pretrained side effect. Small inputs can fail in the VGG-like classifier path; use realistic segmentation sizes. |
| `unet` | `unet` | `(self, feature_scale=4, n_classes=21, is_deconv=True, in_channels=3, is_batchnorm=True)` | `{"arch": "unet", "feature_scale": 4, "is_deconv": True}` | No pretrained download in `get_model`. Good for lightweight constructor checks, though real forward sizes should still be large enough for downsampling. |
| `segnet` | `segnet` | `(self, n_classes=21, in_channels=3, is_unpooling=True)` | `{"arch": "segnet", "is_unpooling": True}` | `get_model` calls `torchvision.models.vgg16(pretrained=True)` and copies VGG parameters. Avoid by default in automated smoke tests. |
| `pspnet` | `pspnet` | `(self, n_classes=21, block_config=[3, 4, 23, 3], input_size=(473, 473), version=None)` | `{"arch": "pspnet", "version": "pascal"}` or explicit `n_classes`/`input_size` values | `version` may be `pascal`, `cityscapes`, or `ade20k` to load built-in specs. Importing this module needs compatible protobuf for generated Caffe metadata. |
| `icnet` | `icnet` | `(self, n_classes=19, block_config=[3, 4, 6, 3], input_size=(1025, 2049), version=None, is_batchnorm=True)` | `{"arch": "icnet", "version": "cityscapes"}` or explicit options | No VGG download in `get_model`; large default input sizes reflect the original architecture. |
| `icnetBN` | `icnet` | `(self, n_classes=19, block_config=[3, 4, 6, 3], input_size=(1025, 2049), version=None, is_batchnorm=True)` | `{"arch": "icnetBN", "is_batchnorm": True}` | Registry alias to the same `icnet` constructor. Set `is_batchnorm` explicitly when a user asks about batch normalization. |
| `linknet` | `linknet` | `(self, feature_scale=4, n_classes=21, is_deconv=True, in_channels=3, is_batchnorm=True)` | `{"arch": "linknet", "feature_scale": 4}` | No pretrained download in `get_model`. |
| `frrnA` | `frrn` | `(self, n_classes=21, model_type='B', group_norm=False, n_groups=16)` | `{"arch": "frrnA", "model_type": "A"}` | Required explicit `model_type`: the shared constructor defaults to `B`, so `{"arch": "frrnA"}` silently creates a B-spec FRRN. Safe no-download CPU smoke target. |
| `frrnB` | `frrn` | `(self, n_classes=21, model_type='B', group_norm=False, n_groups=16)` | `{"arch": "frrnB", "model_type": "B"}` | Explicit `model_type` avoids ambiguity and documents intent. Safe no-download CPU smoke target. |

### Unknown model ids

The registry contains only:

```text
fcn32s, fcn16s, fcn8s, unet, segnet, pspnet, icnet, icnetBN, linknet, frrnA, frrnB
```

If a different `arch` is supplied, the original dispatcher attempts to raise a string rather than an exception object. Modern Python may therefore surface a confusing `TypeError` instead of a clean "model not available" exception. First check spelling and capitalization.

## Safe instantiation examples

### FRRN A smoke without downloads

```python
from ptsemseg.models import get_model

model = get_model({"arch": "frrnA", "model_type": "A"}, n_classes=2)
model.eval()
```

To run a tiny CPU forward smoke from this sub-skill, use:

```bash
python scripts/smoke_model_registry.py --smoke --model-id frrnA --n-classes 2 --height 64 --width 64
```

### UNet constructor path without downloads

```python
from ptsemseg.models import get_model

model = get_model(
    {"arch": "unet", "feature_scale": 4, "is_deconv": True, "is_batchnorm": True},
    n_classes=21,
)
```

### PSPNet/ICNet version note

Pass `version` inside `model_dict`, not as the third argument to `get_model`:

```python
psp = get_model({"arch": "pspnet", "version": "pascal"}, n_classes=21)
ic = get_model({"arch": "icnet", "version": "cityscapes"}, n_classes=19)
```

## Registry and utility tables

### Loss registry

Import path: `ptsemseg.loss`.

| Registry key | Function | Verified callable signature | Notes |
| --- | --- | --- | --- |
| `cross_entropy` | `cross_entropy2d` | `(input, target, weight=None, size_average=True)` | Uses `ignore_index=250`; upsamples logits only when both height and width differ from target. |
| `bootstrapped_cross_entropy` | `bootstrapped_cross_entropy2d` | `(input, target, K, weight=None, size_average=True)` | Requires `K`; computes top-K pixel loss per image. |
| `multi_scale_cross_entropy` | `multi_scale_cross_entropy2d` | `(input, target, weight=None, size_average=True, scale_weight=None)` | Accepts a tuple of logits for PSPNet/ICNet auxiliary outputs. |

`get_loss_function(cfg)` expects `cfg["training"]["loss"]` to be either `None` or a dict with `name` plus function-specific parameters. Unknown names raise `NotImplementedError`.

### Optimizer registry

Import path: `ptsemseg.optimizers`.

| Registry key | Torch optimizer class |
| --- | --- |
| `sgd` | `torch.optim.SGD` |
| `adam` | `torch.optim.Adam` |
| `adamax` | `torch.optim.Adamax` |
| `asgd` | `torch.optim.ASGD` |
| `adadelta` | `torch.optim.Adadelta` |
| `adagrad` | `torch.optim.Adagrad` |
| `rmsprop` | `torch.optim.RMSprop` |

`get_optimizer(cfg)` returns SGD when `cfg["training"]["optimizer"] is None`; otherwise it expects `cfg["training"]["optimizer"]["name"]`.

### Scheduler registry

Import path: `ptsemseg.schedulers`.

| Registry key | Scheduler class | Important params |
| --- | --- | --- |
| `constant_lr` | `ConstantLR` | `(optimizer, last_epoch=-1)` |
| `poly_lr` | `PolynomialLR` | `(optimizer, max_iter, decay_iter=1, gamma=0.9, last_epoch=-1)` |
| `multi_step` | `torch.optim.lr_scheduler.MultiStepLR` | Use PyTorch's `milestones`, `gamma`, etc. |
| `cosine_annealing` | `torch.optim.lr_scheduler.CosineAnnealingLR` | Use PyTorch's `T_max`, `eta_min`, etc. |
| `exp_lr` | `torch.optim.lr_scheduler.ExponentialLR` | Use PyTorch's `gamma`, etc. |

`get_scheduler(optimizer, scheduler_dict)` returns `ConstantLR` when `scheduler_dict is None`. Otherwise it pops `name` from `scheduler_dict`, so pass a copy if the original config must be preserved. Warmup is enabled when `warmup_iters` is present; source keys are `warmup_iters`, `warmup_mode`, and `warmup_factor`.

### Augmentation registry

Import path: `ptsemseg.augmentations`.

| Registry key | Class | Parameter shape |
| --- | --- | --- |
| `gamma` | `AdjustGamma` | numeric gamma range multiplier |
| `hue` | `AdjustHue` | numeric hue range |
| `brightness` | `AdjustBrightness` | numeric brightness factor range |
| `saturation` | `AdjustSaturation` | numeric saturation factor range |
| `contrast` | `AdjustContrast` | numeric contrast factor range |
| `rcrop` | `RandomCrop` | int or `(height, width)` |
| `hflip` | `RandomHorizontallyFlip` | probability float |
| `vflip` | `RandomVerticallyFlip` | probability float |
| `scale` | `Scale` | integer long-side size in source implementation |
| `rsize` | `RandomSized` | integer size |
| `rsizecrop` | `RandomSizedCrop` | integer size |
| `rotate` | `RandomRotate` | max degree |
| `translate` | `RandomTranslate` | `(delta_x, delta_y)` |
| `ccrop` | `CenterCrop` | int or `(height, width)` |

`get_composed_augmentations(aug_dict)` returns `None` for `None`; otherwise it constructs augmentations in dict iteration order. Unknown keys raise `KeyError`.

### Metrics and utility APIs

| API | Signature | Use |
| --- | --- | --- |
| `ptsemseg.metrics.runningScore` | `(self, n_classes)` | Maintains a confusion matrix. Call `update(label_trues, label_preds)`, then `get_scores()` for overall accuracy, mean accuracy, frequency-weighted accuracy, mean IoU, and per-class IoU. |
| `ptsemseg.metrics.averageMeter` | `(self)` | Tracks current value, sum, count, and average via `update(val, n=1)` and `reset()`. |
| `ptsemseg.utils.convert_state_dict` | `(state_dict)` | Removes a leading `module.` prefix from keys saved by `torch.nn.DataParallel`; returns the original dict unchanged when keys are already unprefixed. |

Example:

```python
from ptsemseg.utils import convert_state_dict

checkpoint = {"module.encoder.weight": "..."}
clean = convert_state_dict(checkpoint)
assert "encoder.weight" in clean
```

## Practical registry inspection snippet

```python
from ptsemseg.loss import key2loss
from ptsemseg.optimizers import key2opt
from ptsemseg.schedulers import key2scheduler
from ptsemseg.augmentations import key2aug

print("losses", sorted(key2loss))
print("optimizers", sorted(key2opt))
print("schedulers", sorted(key2scheduler))
print("augmentations", sorted(key2aug))
```

Prefer the bundled helper when the goal is a repeatable, no-download check:

```bash
python scripts/smoke_model_registry.py --list-only
```
