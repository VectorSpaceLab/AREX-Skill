# IO and Visualization

## Image decode and encode APIs

TorchVision image IO lives in `torchvision.io`. The main modern decoder is `decode_image`; `read_image` is retained as an obsolete convenience wrapper.

| API | Use for | Input | Output / constraints |
| --- | --- | --- | --- |
| `read_file(path)` | Raw file bytes | Path-like string | 1-D `torch.uint8` tensor. |
| `write_file(path, data)` | Raw bytes write | Path and 1-D `torch.uint8` tensor | Writes bytes. |
| `decode_image(input, mode="RGB")` | General image decode | Path-like string or encoded 1-D `torch.uint8` tensor | `C,H,W` tensor, usually `torch.uint8`; supports JPEG, PNG, GIF, WebP; AVIF/HEIC need specific decoders. |
| `decode_jpeg`, `decode_png`, `decode_webp`, `decode_gif` | Format-specific decode | Encoded byte tensor | Format-specific modes and options. JPEG supports CUDA decode when built and available. |
| `decode_avif`, `decode_heic` | AVIF / HEIC decode | Encoded byte tensor | Requires `torchvision-extra-decoders` on supported Linux systems. |
| `encode_png`, `write_png` | PNG encode/write | `uint8` image tensor in `C,H,W` or grayscale layout | Channels must be valid for PNG; compression level `0..9`. |
| `encode_jpeg`, `write_jpeg` | JPEG encode/write | `uint8` image tensor in `C,H,W` | Channels must be `1` or `3`; quality `1..100`. |

Prefer `decode_image(path, mode="RGB")` when you want tensor-native loading from a path. Prefer `read_file()` followed by a format-specific decoder when the caller already has bytes, needs lower-level control, or wants CUDA JPEG decode.

```python
from torchvision.io import decode_image, write_png

image = decode_image("sample.png", mode="RGB")
assert image.dtype == torch.uint8 and image.ndim == 3 and image.shape[0] == 3
write_png(image, "copy.png")
```

## Decode mode and dtype conventions

- `mode="RGB"`, `mode="RGBA"`, `mode="GRAY"`, and `mode="UNCHANGED"` are accepted string aliases for `ImageReadMode` values.
- Decoders return channel-first tensors, usually `torch.uint8` in `[0, 255]`.
- Some 16-bit PNG, AVIF, or HEIC inputs can return `torch.uint16`; convert deliberately before transforms or models.
- Encoders expect `torch.uint8`, not normalized `float32`; convert floats back to byte range before writing.
- For v2 transform pipelines, route dtype/range conversion details to `../transforms-and-tv-tensors/`.

## Video and audio IO boundary

TorchVision image IO is still public, but video decoding and encoding capabilities have been deprecated or migrated. For new video/audio decoding work, use TorchCodec. Dataset classes that rely on clip extraction may require TorchCodec availability. Keep legacy TorchVision video examples as reference-only unless the user explicitly needs migration help.

## Visualization utilities

`torchvision.utils` provides small tensor visualization helpers. These are useful for debugging data and model outputs, not for model inference itself.

| API | Input requirements | Common use |
| --- | --- | --- |
| `make_grid(tensor_or_list, nrow=8, padding=2, normalize=False, value_range=None, scale_each=False)` | 2-D image, `C,H,W` image, `B,C,H,W` batch, or list of same-sized image tensors | Build a single grid tensor for saving or plotting. |
| `save_image(tensor, fp, ...)` | Image or batch tensor | Save a grid/image through PIL. |
| `draw_bounding_boxes(image, boxes, labels=None, colors=None, fill=False, width=1, ...)` | Single `C,H,W` image, `uint8` `[0,255]` or float `[0,1]`; channels `1` or `3`; boxes in `XYXY` or rotated 8-point absolute coordinates | Draw boxes and optional labels. |
| `draw_segmentation_masks(image, masks, alpha=0.8, colors=None)` | RGB `3,H,W` image; masks as bool `H,W` or `N,H,W` | Overlay semantic or instance masks. |
| `draw_keypoints(image, keypoints, connectivity=None, colors=None, radius=2, width=3, visibility=None)` | RGB `3,H,W` image; keypoints `N,K,2`; optional visibility `N,K` | Draw keypoints and skeleton edges. |
| `flow_to_image(flow)` | Flow tensor with compatible layout and finite values | Convert optical flow to RGB visualization. |

## Safe visualization pattern

```python
import torch
from torchvision.utils import draw_bounding_boxes, make_grid

image = torch.zeros((3, 64, 64), dtype=torch.uint8)
boxes = torch.tensor([[8, 8, 40, 40]], dtype=torch.float32)
annotated = draw_bounding_boxes(image, boxes, labels=["object"], colors="red", width=2)
grid = make_grid([image, annotated], nrow=2)
```

## Interop with PIL and Matplotlib

- `torchvision.io.decode_image` returns tensor data directly; no PIL conversion is needed for tensor transforms.
- `ImageFolder` default loading returns PIL images unless a custom loader is supplied.
- To display a tensor grid with Matplotlib, convert with `torchvision.transforms.functional.to_pil_image(grid)` or permute to `H,W,C` and convert carefully.
- If a visualization helper returns `uint8`, save it as PNG/JPEG or convert to PIL for display.
