# Models and transforms reference

## Model API examples

```python
from torchgeo.models import get_model, get_model_weights, list_models

print(list_models())
model = get_model('resnet18', weights=None, in_channels=3, num_classes=10)
weights_enum = get_model_weights('resnet18')
print([str(w) for w in weights_enum])
```

Use exact constructor parameters from the model builder source. Different model families expose different names for `in_channels`, `num_classes`, image size, or pretrained configuration.

## Weight loading in tasks

Task classes accept `weights` as:

- `None` or `False`: random initialization;
- `True`: upstream ImageNet/timm/SMP weights where supported;
- a TorchGeo `WeightsEnum` value;
- a string representation accepted by `get_weight`;
- a local checkpoint path for task-specific backbone extraction paths.

Avoid weight downloads in tests unless network/cache are part of the acceptance criteria.

## Spectral index example

```python
import torch
from torchgeo.transforms import AppendNDVI

# Example band order: [blue, green, red, nir]
image = torch.rand(2, 4, 64, 64)
transform = AppendNDVI(index_nir=3, index_red=2)
out = transform(image)
assert out.shape[1] == 5
```

## Verification candidates

- `tests/models/test_api.py`: registry list/get weight behavior.
- `tests/models/test_resnet.py`, `test_vit.py`, `test_swin.py`, and family-specific tests: builder signatures and weights.
- `tests/transforms/test_indices.py`: spectral index channel append behavior.
- `tests/transforms/test_sar.py`, `test_color.py`, `test_spatial.py`, `test_temporal.py`: transform-specific semantics.
- `tests/tasks/test_classification.py` and `test_segmentation.py`: integration of model weights into task modules.

## Common pitfalls

- Assuming every model builder accepts the same parameter names.
- Loading pretrained RGB weights into multispectral inputs without checking adaptation support.
- Forgetting that `SemanticSegmentation(model='fcn')` is not the SMP encoder path and does not support pretrained weights.
- Applying an index transform before confirming band order; wrong channel indexes silently create meaningless features.
- Importing optional model families in environments that only installed the core package.
