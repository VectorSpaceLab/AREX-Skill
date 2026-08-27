# Feature Extraction

`torchvision.models.feature_extraction` uses `torch.fx` tracing to return intermediate activations from model nodes. Use it when a task needs ResNet layer features, backbone outputs for an FPN, model inspection, or named intermediate tensors.

## Core APIs

```python
from torchvision.models import resnet50
from torchvision.models.feature_extraction import create_feature_extractor, get_graph_node_names

model = resnet50(weights=None).eval()
train_nodes, eval_nodes = get_graph_node_names(model)
extractor = create_feature_extractor(model, return_nodes={"layer4": "feat"}).eval()
```

Important signatures:

| API | Purpose |
| --- | --- |
| `get_graph_node_names(model, tracer_kwargs=None, suppress_diff_warning=False, concrete_args=None)` | Returns `(train_nodes, eval_nodes)` in execution order. |
| `create_feature_extractor(model, return_nodes=None, train_return_nodes=None, eval_return_nodes=None, tracer_kwargs=None, suppress_diff_warning=False, concrete_args=None)` | Returns a `GraphModule` whose forward returns a dict of requested activations. |

## Node Naming Rules

- Node names are dot-separated paths through the module hierarchy, without the top-level module name.
- Repeated operations receive suffixes such as `_1` and `_2`.
- A truncated node name can be used as a shortcut. For example, `"layer4"` selects the last executed descendant of `layer4`.
- Truncated names are convenient but can surprise users when a layer has multiple operations or outputs. For debugging, inspect full names with `get_graph_node_names()`.
- Train and eval node lists may differ for modules with mode-dependent control flow. Use `train_return_nodes` and `eval_return_nodes` when needed.

## ResNet Feature Example

```python
import torch
from torchvision.models import resnet50
from torchvision.models.feature_extraction import create_feature_extractor, get_graph_node_names

model = resnet50(weights=None).eval()
_, eval_nodes = get_graph_node_names(model)
print([name for name in eval_nodes if name.startswith("layer4")][-5:])

return_nodes = {
    "layer1": "layer1",
    "layer2": "layer2",
    "layer3": "layer3",
    "layer4": "layer4",
}
extractor = create_feature_extractor(model, return_nodes=return_nodes).eval()
with torch.no_grad():
    outputs = extractor(torch.randn(1, 3, 224, 224))
print({name: tuple(value.shape) for name, value in outputs.items()})
```

## FPN Backbone Pattern

For FPNs, map backbone stages to string keys expected by downstream code and run a dry pass to derive channel counts.

```python
import torch
from torchvision.models import resnet50
from torchvision.models.feature_extraction import create_feature_extractor
from torchvision.ops.feature_pyramid_network import FeaturePyramidNetwork, LastLevelMaxPool

body = create_feature_extractor(
    resnet50(weights=None),
    return_nodes={"layer1": "0", "layer2": "1", "layer3": "2", "layer4": "3"},
).eval()

with torch.no_grad():
    sample_outputs = body(torch.randn(1, 3, 224, 224))
in_channels_list = [feature.shape[1] for feature in sample_outputs.values()]
fpn = FeaturePyramidNetwork(
    in_channels_list=in_channels_list,
    out_channels=256,
    extra_blocks=LastLevelMaxPool(),
)
```

If the FPN receives unexpected shapes or missing keys, print the extractor output keys and compare them to the `return_nodes` mapping. For detection backbones, keys such as `"0"`, `"1"`, `"2"`, `"3"` are commonly expected by FPN-related helper code.

## Train vs Eval Nodes

When `get_graph_node_names()` warns that train and eval graphs differ, do not force a single `return_nodes` mapping unless the requested nodes exist in both graphs. Use explicit mappings:

```python
extractor = create_feature_extractor(
    model,
    train_return_nodes={"dropout": "dropout_train"},
    eval_return_nodes={"features": "features_eval"},
)
```

Both `train_return_nodes` and `eval_return_nodes` must be supplied together. If only one mode matters, put the model in that mode and use `return_nodes` after confirming node names.

## Tracing Custom or Difficult Models

- Use `tracer_kwargs={"leaf_modules": [MyCustomModule]}` to avoid tracing through modules with unsupported Python control flow.
- Use `tracer_kwargs={"autowrap_functions": [my_helper]}` or autowrap modules for helper functions that FX cannot trace directly.
- Use `concrete_args` for arguments that should not become FX proxies.
- TorchVision automatically treats many `torchvision.ops` modules as leaves for feature extraction.

## Debug Checklist

1. Instantiate with `weights=None` first to avoid network activity while debugging node names.
2. Call `model.eval()` if the intended use is inference or backbone feature extraction.
3. Print a filtered suffix of `eval_nodes`, for example names starting with `layer3` or `layer4`.
4. Prefer full node names when correctness matters; use truncated names only after confirming the last descendant is the desired output.
5. Check output dict keys and tensor shapes immediately after creating the extractor.
