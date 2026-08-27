# Models and Weights Troubleshooting

## Version Mismatch

Symptoms:

- `Unknown model ...` from `get_model()` or `get_model_builder()`.
- A documented weight enum or model builder is missing.
- Import errors or custom operator errors when constructing detection models.

Checks:

```python
import torch, torchvision
print(torch.__version__)
print(torchvision.__version__)
print(torchvision.models.list_models(include="*resnet*")[:5])
```

Use APIs that exist in the installed TorchVision version. `DEFAULT` weight aliases and available model names can differ between releases. For compiled operator problems, route low-level diagnostics to `../ops-and-detection/`.

## Deprecated `pretrained` Flag

Symptoms:

- Warnings about `pretrained` being deprecated.
- Confusion over `model(True)` or `pretrained=True` behavior.

Fix:

```python
from torchvision.models import ResNet50_Weights, resnet50

model = resnet50(weights=ResNet50_Weights.IMAGENET1K_V1)
model = resnet50(weights=None)  # no pretrained weights
```

Use `weights=...` explicitly. Pin a concrete enum member for reproducible results; use `DEFAULT` only when the best current weight for the installed version is acceptable.

## Accidental Weight Downloads

Symptoms:

- Tests hang or fail without network.
- First model construction is slow.
- Cache permission errors or unexpected disk usage.

Fixes:

- Use `weights=None` in tests and smoke checks.
- For detection/segmentation builders, also set `weights_backbone=None` when present.
- Do not call `weights.get_state_dict()` in no-network contexts.
- If downloads are intended, set or document `TORCH_HOME` so the cache location is explicit.

```python
from torchvision.models.detection import fasterrcnn_resnet50_fpn

model = fasterrcnn_resnet50_fpn(weights=None, weights_backbone=None).eval()
```

## Wrong Preprocessing or Labels

Symptoms:

- Poor predictions from a pretrained classifier.
- Unexpected input size, dtype, or normalization issues.
- Labels do not match logits.

Fix:

```python
weights = ResNet50_Weights.DEFAULT
preprocess = weights.transforms()
categories = weights.meta.get("categories")
```

Always pair the exact weight member with its own `transforms()` and metadata. Do not mix preprocessing from one weight enum with another model or task.

## Detection Models Need TorchVision Ops

Symptoms:

- Errors mentioning `torchvision::nms`, ROIAlign, missing C++ ops, or incompatible binaries.
- Detection model construction works but inference fails during NMS/postprocessing.

Fixes:

- Confirm `torch` and `torchvision` versions/builds are compatible.
- Use a wheel or source build that includes TorchVision custom operators.
- Route detailed operator checks and smoke tests to `../ops-and-detection/`.

Detection models included in TorchVision depend on installed TorchVision ops; PyTorch Hub-only usage is not enough for those models.

## Feature Extraction Node Surprises

Symptoms:

- `create_feature_extractor()` says a return node does not exist.
- Output keys or shapes do not match an FPN or downstream head.
- Train and eval node lists differ.

Fixes:

```python
from torchvision.models.feature_extraction import get_graph_node_names

train_nodes, eval_nodes = get_graph_node_names(model)
print([name for name in eval_nodes if name.startswith("layer4")])
```

- Use `get_graph_node_names()` in the model mode you care about.
- Avoid relying on truncated node names until you inspect full node names.
- For FPNs, map stages to expected keys such as `{"layer1": "0", "layer2": "1", "layer3": "2", "layer4": "3"}`.
- If train/eval graphs differ, pass both `train_return_nodes` and `eval_return_nodes`.

## Train vs Eval Mode

Symptoms:

- Detection models return losses instead of predictions.
- BatchNorm/dropout behavior differs from expected inference behavior.
- Feature extractor node names differ between modes.

Fix:

```python
model.eval()
with torch.no_grad():
    output = model(inputs)
```

Use `model.train()` only for training. Detection models generally expect images and targets in training mode, and images only in eval mode.

## Weight Enum Name Errors

Symptoms:

- `Invalid weight name provided` from `get_weight()`.
- `KeyError` for an enum member.
- `TypeError` saying the wrong weight class was provided.

Fixes:

- `get_weight()` expects a full enum member name like `"ResNet50_Weights.IMAGENET1K_V2"`.
- Builder `weights="IMAGENET1K_V2"` accepts member names for that builder's own enum.
- Do not pass `MobileNet_V3_Large_Weights.DEFAULT` to `resnet50()`; use the matching enum class.

## Licensing and Terms

Pretrained weights may carry dataset- or recipe-derived license and usage terms. Agents should surface this risk for production, redistribution, or commercial use. Inspect `weights.meta` for recipe and category metadata, but do not assume the metadata fully answers legal questions.
