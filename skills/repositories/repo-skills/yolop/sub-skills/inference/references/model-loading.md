# YOLOP Model Loading Reference

## When to read

Read this when deciding how to build a YOLOP model, load `End-to-end.pth`, handle checkpoint formats, use `hubconf.py`, or select CPU/CUDA devices.

## Direct source loading

The most debuggable pattern is:

```python
import sys
sys.path.insert(0, "/path/to/YOLOP")
import torch
from lib.config import cfg
from lib.models import get_net

model = get_net(cfg)
checkpoint = torch.load("/path/to/weights/End-to-end.pth", map_location="cpu")
model.load_state_dict(checkpoint["state_dict"])
model.eval()
```

Use `strict=False` only when you intentionally changed architecture variants or are diagnosing mismatched keys.

## Checkpoint variants

- Epoch checkpoints saved by `save_checkpoint` include `state_dict` and `optimizer`.
- `final_state.pth` is a bare model state dict.
- The source demo and test scripts expect a dictionary with `state_dict`.
- `MODEL.PRETRAINED_DET` loading in `tools/train.py` filters state dict keys by parameter index ranges to initialize the detection branch.

## Torch Hub-style helper

`hubconf.py` exposes:

```python
yolop(pretrained=True, device="cpu")
```

It builds `get_net(cfg)`, optionally loads `weights/End-to-end.pth` relative to `hubconf.py`, moves the model to the selected device, and returns the model.

Use it when working through torch hub conventions. Use direct loading when you need explicit control over repo root, checkpoint path, map location, or partial loading.

## Device choices

`select_device` accepts `cpu` or CUDA device strings. Source demos default to CPU, but training/evaluation choose CUDA automatically when available unless debug paths force CPU.

For reliable automated inference checks:

```bash
--device cpu
```

For CUDA:

1. Install a CUDA-capable torch/torchvision pair.
2. Verify `torch.cuda.is_available()`.
3. Verify a tiny allocation before loading a large checkpoint.
4. Keep image size and batch size within available VRAM.

## Half precision

The source demo sets `half = device.type != 'cpu'` and calls `model.half()` on CUDA. If you see dtype errors, disable half precision in a local adaptation or keep inputs/model in the same dtype.
