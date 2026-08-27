# Datamodules and tasks reference

## Constructor patterns

### Classification task

```python
from torchgeo.tasks import Classification

task = Classification(
    model='resnet18',
    weights=None,
    in_channels=3,
    task='multiclass',
    num_classes=10,
    loss='ce',
    lr=1e-3,
)
```

Use `weights=True` for ImageNet/timm weights when network/cache are acceptable. Use a TorchGeo weight enum string or enum object when loading geospatial pretrained backbones.

### Semantic segmentation task

```python
from torchgeo.tasks import SemanticSegmentation

task = SemanticSegmentation(
    model='unet',
    backbone='resnet18',
    weights=None,
    in_channels=4,
    task='multiclass',
    num_classes=5,
    loss='ce',
    ignore_index=0,
)
```

Use `model='fcn'` for TorchGeo's lightweight FCN path. Pretrained weights are not supported by the FCN branch.

## Verification candidates

- `tests/datamodules/test_geo.py`: `GeoDataModule` split/sampler/dataloader behavior.
- `tests/datamodules/test_utils.py`: datamodule utility collate and misconfiguration behavior.
- `tests/tasks/test_classification.py`: classification constructors, losses, trainer smoke, plotting.
- `tests/tasks/test_segmentation.py`: SMP/FCN segmentation variants, loss settings, trainer smoke, plotting.
- `tests/tasks/test_detection.py`, `test_change.py`, `test_regression.py`, `test_mae.py`, and self-supervised task tests: task-specific batch schemas.
- `tests/test_main.py`: command-line entry point behavior.

## Lightning gotchas

- Keep downloads in `prepare_data` and object construction/splits in `setup`.
- Do not rely on `self.trainer` inside constructors. Augmentation routing happens after the trainer attaches.
- If a plot hook logs images, close figures in tests to avoid matplotlib resource leaks.
- For CPU smoke, make trainer settings small and deterministic. Do not use checkpoint-downloading weights in routine tests.

## Config review checklist

When reviewing a TorchGeo training config, verify:

1. Dataset/datamodule paths and `download`/`checksum` choices are intentional.
2. `in_channels` matches selected bands and any appended spectral indices.
3. `num_classes`/`num_labels`, `task`, `loss`, `ignore_index`, and label names match the dataset target.
4. Batch collation matches the target type.
5. Weights do not trigger an unapproved network download.
6. Trainer accelerator settings match available hardware but CPU fallback remains possible for smoke checks.
