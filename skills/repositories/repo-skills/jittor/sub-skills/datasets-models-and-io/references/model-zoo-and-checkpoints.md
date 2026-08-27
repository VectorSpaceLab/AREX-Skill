# Model zoo and checkpoints

This reference covers Jittor model-zoo constructors, pretrained weight behavior, and safe checkpoint I/O. Keep data layout guidance in the data reference; keep training loops in the training sub-skill.

## Model-zoo constructor pattern

```python
import jittor as jt
import jittor.models as models

net = models.resnet18(pretrained=False, num_classes=1000)
net.eval()
x = jt.random((1, 3, 224, 224))
y = net(x)
assert list(y.shape) == [1, 1000]
```

Common assumptions:

- Constructors default to `pretrained=False` and most accept extra architecture kwargs such as `num_classes`.
- Image classifiers expect NCHW input (`batch, channels, height, width`) with three channels.
- Use `model.eval()` for inference or smoke checks so dropout/batch-norm behavior is deterministic enough for shape checks.
- Use small synthetic inputs for constructor/shape smoke. Do not use `pretrained=True` in offline checks.

## Available constructor families

| Family | Public constructor examples | Notes |
| --- | --- | --- |
| ResNet / ResNeXt / Wide ResNet | `resnet18`, `resnet34`, `resnet26`, `resnet38`, `resnet50`, `resnet101`, `resnet152`, `resnext50_32x4d`, `resnext101_32x8d`, `wide_resnet50_2`, `wide_resnet101_2` | `resnet18(pretrained=False, **kwargs)` and siblings construct ImageNet-style classifiers. |
| VGG | `vgg11`, `vgg11_bn`, `vgg13`, `vgg13_bn`, `vgg16`, `vgg16_bn`, `vgg19`, `vgg19_bn` | VGG classifiers default to 1000 classes and include dropout in the classifier; call `eval()` for inference smoke. |
| AlexNet / SqueezeNet | `alexnet`, `squeezenet1_0`, `squeezenet1_1` | Lightweight constructor choices relative to deeper ResNets/VGGs. |
| DenseNet | `densenet121`, `densenet161`, `densenet169`, `densenet201` | Constructors accept `pretrained=False` and DenseNet-specific kwargs. |
| GoogLeNet / Inception | `googlenet`, `inception_v3` | Inception-style models may need larger image sizes than a tiny smoke input for realistic use. Use only for constructor checks unless the task needs this family. |
| Mobile / efficient backbones | `mobilenet_v2`, `mnasnet0_5`, `mnasnet0_75`, `mnasnet1_0`, `mnasnet1_3`, `shufflenet_v2_x0_5`, `shufflenet_v2_x1_0`, `shufflenet_v2_x1_5`, `shufflenet_v2_x2_0` | Good candidates when a task asks for a smaller classifier. |
| Res2Net | `res2net50`, `res2net101` plus named variants exposed by the module | Use when a task specifically requests Res2Net-style blocks; verify constructor signature before passing uncommon kwargs. |

The installed package exposes both class-style names (`Resnet18`, `AlexNet`) and lowercase constructor aliases. Prefer lowercase functions in task code unless matching existing project style.

## Pretrained weights and `jittorhub://`

The model-zoo modules implement pretrained loading by calling `model.load("jittorhub://<checkpoint>.pkl")` when `pretrained=True`.

Operational consequences:

1. `pretrained=True` may use the network to fetch a checkpoint if it is not already cached.
2. Downloads require a writable Jittor checkpoint cache and enough disk space.
3. A failed or partial download can later look like a corrupt checkpoint.
4. Offline smoke tests must use `pretrained=False`; if pretrained weights are required offline, pre-stage a verified local checkpoint and call `model.load(local_path)` explicitly.

Use this decision rule:

- Shape/API smoke: `pretrained=False`.
- Reproducing a pretrained result with network permitted: `pretrained=True`, then verify output semantics.
- Reproducing a pretrained result with network forbidden: provide a local checkpoint, verify checksum/provenance outside the smoke, then call `model.load(path)`.

## Jittor save/load APIs

| API | Use for | Behavior and cautions |
| --- | --- | --- |
| `jt.save(obj, path)` | Saving a dictionary/list of Jittor parameters or other supported pickleable objects. | Writes Jittor's safe pickle format with checksum. Prefer `model.save(path)` for full model state dictionaries. |
| `jt.load(path)` | Loading a Jittor pickle file or supported checkpoint file. | Returns the loaded object. For `.pth`, `.pt`, or `.bin`, dispatches to Jittor's PyTorch checkpoint loader. |
| `model.state_dict(to=None)` | Inspecting/exporting parameters by name. | `to=None` returns Jittor Vars; `to="numpy"` returns NumPy arrays; `to="torch"` constructs Torch tensors and therefore requires PyTorch. |
| `model.load_parameters(params)` / `model.load_state_dict(params)` | Loading an in-memory parameter dictionary. | Converts NumPy/list/Jittor Var/PyTorch tensor values when possible. Missing keys and shape mismatches are logged and skipped; the method does not provide strict PyTorch-style failure reporting. |
| `model.save(path)` | Saving `model.state_dict()` in Jittor format. | Use for Jittor-to-Jittor round trips. |
| `model.load(path)` | Loading Jittor format, `jittorhub://`, URL-backed checkpoint, or supported PyTorch-style file into the model. | Calls `jt.load(path)` then `load_parameters`. Always inspect warnings for skipped keys or shape mismatches. |

Minimal strictness check before loading:

```python
expected = model.state_dict()
loaded = jt.load(path)
missing = sorted(set(expected) - set(loaded))
extra = sorted(set(loaded) - set(expected))
shape_mismatch = [k for k in expected.keys() & loaded.keys() if list(expected[k].shape) != list(loaded[k].shape)]
if missing or extra or shape_mismatch:
    raise ValueError({"missing": missing, "extra": extra, "shape_mismatch": shape_mismatch})
model.load_parameters(loaded)
```

## PyTorch checkpoint interop

Jittor includes helper code for PyTorch-style state dictionaries, but interop is narrower than native PyTorch serialization.

### Loading `.pth`, `.pt`, and `.bin`

- `jt.load(path)` dispatches to the PyTorch loader for these extensions.
- The loader is designed for tensor/state-dict checkpoints, including zip-format and older storage layouts.
- It reconstructs tensors as Jittor Vars and handles common storage dtypes and strides.
- It is not a guarantee for arbitrary Python objects, full PyTorch modules with custom classes, optimizer internals, quantized/sparse exotic states, or checkpoints that rely on project-specific import code.
- A file with the wrong extension is not treated as a PyTorch checkpoint by the helper.

### Loading PyTorch tensors directly

`model.load_parameters(torch_model.state_dict())` is supported when PyTorch is installed because Jittor converts values through `.cpu().detach().numpy()`. Use this for direct in-process parity checks, then compare outputs numerically if exact model equivalence matters.

### Saving for PyTorch consumers

The helper `jittor_utils.save_pytorch.save_pytorch(path, obj)` can serialize Jittor Vars into a PyTorch-style archive for simple state dictionaries. It imports PyTorch and maps a limited dtype set. Prefer it only when a downstream PyTorch consumer is required; otherwise keep native Jittor checkpoints.

## Recommended checkpoint workflows

### Native Jittor round trip

```python
model = models.resnet18(pretrained=False)
model.save("model.pkl")
model.load("model.pkl")
```

### Local pretrained/offline load

```python
model = models.resnet18(pretrained=False)
state = jt.load("verified_local_weights.pkl")
model.load_parameters(state)
```

### PyTorch state dict, when PyTorch is available

```python
# torch_model is a matching PyTorch architecture already in memory.
model = models.resnet18(pretrained=False)
model.load_parameters(torch_model.state_dict())
```

After any non-native checkpoint load, check logs for skipped parameters and run a small forward pass with known input shape.
