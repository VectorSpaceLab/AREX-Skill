# Python API workflows

## Purpose

Read this when you need to use DragGAN from your own Python code instead of the browser demo.

## Minimal generation flow

```python
import torch
from draggan import draggan as dg
from draggan import utils

# CUDA is the verified backend for the drag loop.
device = torch.device("cuda")

# Use a cached checkpoint name or a direct path.
G = dg.load_model(utils.get_path("ada/afhqcat.pkl"), device=device)
W = dg.generate_W(G, seed=1, device=device)
image, features = dg.generate_image(W, G, device=device)
```

## Minimal drag loop

```python
import torch
from draggan import draggan as dg
from draggan import utils

device = torch.device("cuda")
G = dg.load_model(utils.get_path("ada/afhqcat.pkl"), device=device)
W = dg.generate_W(G, seed=1, device=device)

handle_points = [torch.tensor([120, 160], device=device).float()]
target_points = [torch.tensor([120, 220], device=device).float()]

for image, W_out, tracked_points in dg.drag_gan(
    W,
    G,
    handle_points,
    target_points,
    mask=None,
    max_iters=20,
):
    print(image.size, W_out.shape, tracked_points)
```

## How to prepare points

- Use `torch.tensor([y, x], device=device).float()` for each point.
- Keep the handle and target lists the same length.
- Convert arrays or tuples to tensors before calling `drag_gan()`.
- Use the point helpers in `draggan.utils` if you need masks or overlays for your own UI.

## Checkpoint and device notes

- `utils.get_path()` accepts a relative checkpoint name and auto-downloads if missing.
- The default `load_model()` URL is not the same as the browser demo default checkpoint.
- `drag_gan()` hardcodes CUDA inside the current implementation, so the model and point tensors must stay on GPU.

## Workflow reminder

If you want the browser UI instead of code, switch to the `web-demo` sub-skill.
