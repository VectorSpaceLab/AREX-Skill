# Inference Workflows

## Purpose

Read this for end-to-end recipes that load OFA models, sample subnets, and
validate the result on an ImageNet-style folder.

## 1. Fast supernet smoke

Use this when you only need to prove that the installed package can build an OFA
model and run a forward pass.

```python
from ofa.model_zoo import ofa_net
import torch

net = ofa_net('ofa_resnet50', pretrained=False)
x = torch.zeros(1, 3, 224, 224)
with torch.no_grad():
    y = net(x)
print(y.shape)
```

If the model exposes `sample_active_subnet()`, you can sample a subnet first and
then evaluate the materialized subnet returned by `get_active_subnet()`.

## 2. ImageNet-style subnet evaluation

Use this when the user asks for `eval_ofa_net.py`-style behavior or wants to
validate a sampled subnet against an `ImageFolder` validation split.

Typical steps:

1. Build the supernet with `ofa_net`.
2. Sample or set the active subnet.
3. Materialize the active subnet with `get_active_subnet(preserve_weight=True)`.
4. Load an ImageNet-style folder containing the validation split.
5. Run the bundled `scripts/evaluate_ofa.py` wrapper.

The bundled helper defaults to a smoke-sized evaluation unless you give it a
data root and a larger batch limit.

## 3. Specialized-model evaluation

Use this when the user names a concrete `ofa_specialized` id such as a FLOPs,
latency, or device-family target.

Typical steps:

1. Load the model with `ofa_specialized(net_id, pretrained=True)`.
2. Read the returned `image_size`.
3. Build the corresponding evaluation transforms.
4. Evaluate on an ImageNet-style `val/` folder.
5. Record top-1 and top-5 accuracy.

The bundled helper can run this as a forward smoke or a small evaluation.

## 4. Hub shortcuts

The repo's `hubconf.py` exposes ready-made partials for the supernet and several
specialized ResNet50D models. Use them when the task names a model family rather
than a raw `net_id`.

## When to use the workflow reference

- When the user needs exact command shapes.
- When you need to distinguish supernet smoke from benchmark-style evaluation.
- When the user needs the return value or resolution contract of specialized
  models.
