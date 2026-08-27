# Model API Reference

## Purpose

Read this when you need exact runtime contracts for model construction in pytorch-cifar100 without reopening the source tree.

## Network factory contract

The repository's public model entry point is the helper that the CLIs call:

```python
from argparse import Namespace
from utils import get_network

args = Namespace(net="resnet18", gpu=False)
net = get_network(args)
```

Required fields on `args`:

| Field | Type | Meaning |
| --- | --- | --- |
| `net` | `str` | Exact lowercase architecture token from `model-catalog.md`. |
| `gpu` | `bool` | When true, `get_network` calls `.cuda()` on the created model. |

Behavior:

- The factory imports the selected model module lazily.
- Unsupported names print `the network name you have entered is not supported yet` and terminate with `sys.exit()`.
- The returned object is a `torch.nn.Module` whose CIFAR-100 head emits 100 logits.
- The training, evaluation, and LR-finder entry points all route through the same factory.

## Direct factory notes

Most direct factories take no arguments and return a 100-class CIFAR-100 model. The notable direct defaults are:

| Factory | Default note |
| --- | --- |
| `models.squeezenet.squeezenet(class_num=100)` | Class count is configurable but the CLI uses the default 100. |
| `models.mobilenet.mobilenet(alpha=1, class_num=100)` | Width multiplier and class count are configurable in direct use. |
| `models.wideresidual.wideresnet(depth=40, widen_factor=10)` | README reports this as `wideresnet-40-10`; the CLI token is just `wideresnet`. |
| `models.nasnet.nasnet()` | Source default builds `NasNetA(4, 2, 44, 44)`. |

Prefer `get_network` for CLI-compatible workflows so the same token will work with `train.py` and `test.py`.

## Input/output shape

The repository adapts ImageNet-era CNN families to CIFAR-100. Use:

```python
x = torch.randn(batch_size, 3, 32, 32)
y = net(x)
assert tuple(y.shape) == (batch_size, 100)
```

Verified representative CPU smoke checks returned `(1, 100)` for `vgg16`, `resnet18`, `mobilenetv2`, `squeezenet`, and `googlenet`.

## Parameter-count checks

`test.py` reports parameters with:

```python
sum(p.numel() for p in net.parameters())
```

Use the bundled `scripts/model_smoke.py` helper when you need a quick parameter count plus output-shape check before a long train/eval run.

## Using CUDA safely

For CLI-compatible construction, `gpu=True` moves the model to CUDA immediately. Only set it when a CUDA-capable PyTorch runtime is available. If you just need to inspect architecture definitions, use CPU mode and avoid calling `.cuda()`.
