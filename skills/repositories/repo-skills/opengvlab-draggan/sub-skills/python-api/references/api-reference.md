# API reference

## Purpose

Read this when you need the verified function signatures, tensor shapes, and return values for the DragGAN Python API.

## Core module

All of the functions below live in `draggan.draggan` unless noted otherwise.

| Function | Verified signature | Return value | Notes |
| --- | --- | --- | --- |
| `load_model` | `network_pkl='https://nvlabs-fi-cdn.nvidia.com/stylegan2-ada-pytorch/pretrained/afhqdog.pkl', device=torch.device('cuda'), fp16=True` | `torch.nn.Module` | Loads a StyleGAN2-ADA generator and registers a forward hook on the synthesis layer at index 6. |
| `generate_W` | `_G, seed=0, network_pkl=None, truncation_psi=1.0, truncation_cutoff=None, device=torch.device('cuda')` | `numpy.ndarray` | Returns a W+ latent with shape `[1, num_ws, 512]` for the provided generator. |
| `forward_G` | `G, W, device` | `(image_tensor, feature_tensor)` | Used internally by the image generator and drag loop. |
| `generate_image` | `W, _G=None, network_pkl=None, class_idx=None, device=torch.device('cuda')` | `(PIL.Image.Image, torch.Tensor)` | Converts the generator output to a PIL image and returns the feature map. |
| `drag_gan` | `W, G, handle_points, target_points, mask, max_iters=1000, r1=3, r2=12, lam=20, d=2, lr=2e-3` | generator yielding `(image, W_out, handle_points)` | Iterative drag optimization; optimizes only the first 6 W layers in the current build. |
| `motion_supervison` | `handle_points, target_points, F, r1, device` | scalar loss tensor | Internal loss used by the drag loop. |
| `point_tracking` | `F, F0, handle_points, handle_points0, r2=3, device=torch.device('cuda')` | updated handle point tensor | Tracks each handle point by feature similarity. |

## Helper functions in `draggan.utils`

| Function | Verified signature | Return value | Notes |
| --- | --- | --- | --- |
| `get_path` | `base_path` | `str` | Resolves and auto-downloads checkpoints under `DRAGGAN_HOME` or `~/draggan/checkpoints-pkl`. |
| `tensor_to_PIL` | `img` | `PIL.Image.Image` | Converts a generator image tensor to a PIL image. |
| `create_circular_mask` | `h, w, center=None, radius=None` | `torch.Tensor` | Boolean circular mask helper. |
| `create_square_mask` | `height, width, center, radius` | `torch.Tensor` | Boolean square mask helper; center uses `[y, x]` order. |
| `draw_handle_target_points` | `img, handle_points, target_points, radius=5` | NumPy array | Draws the handle/target annotations used by the UI. |

## Shape and device notes

- `generate_W()` returns a NumPy array; the drag loop converts it back to a CUDA tensor internally.
- `generate_image()` returns a PIL image plus the intermediate feature tensor used for point tracking.
- Point tensors are expected in `[y, x]` order, not `[x, y]`.
- All tensors passed to `drag_gan()` should already live on the same CUDA device.
- The `mask` argument is present in the signature but is currently unused in the live implementation.

## When to read the source package again

Only read the source code again if a future refresh changes the function signatures, return shapes, or checkpoint catalog.
