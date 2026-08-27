# Datasets, IO, and Visualization Troubleshooting

## `download=True` races or network failures

Symptoms:

- Partial archives, corrupted extracted files, or intermittent `Dataset not found or corrupted` after a distributed run.
- Multiple workers or ranks all attempt the same download/extraction.
- Tests or scripts unexpectedly reach the network.

Fixes:

- Do not use `download=True` inside worker processes, distributed ranks, or library code that may be called repeatedly.
- Trigger downloads once in a single process before initializing distributed training, then construct datasets with `download=False`.
- For generated examples and smoke checks, prefer `FakeData` or tiny temporary fixtures.
- If download failed mid-way, remove partial archives/extracted directories before retrying.
- Treat inaccessible upstream URLs as an environment/network issue; do not silently change the dataset class or root layout.

## Dataset root layout errors

Symptoms:

- `FileNotFoundError: Couldn't find any class folder` from `ImageFolder` or `DatasetFolder`.
- `Found no valid file for the classes ... Supported extensions are ...`.
- `Dataset not found` or `Dataset not found or corrupted` from a built-in dataset.
- Labels differ from expected numeric ids.

Fixes:

- For `ImageFolder`, point `root` at the directory whose immediate children are class folders, not at a parent like `data/` if the real split is `data/train/`.
- Remember class ids are assigned by sorted class folder names; create or inspect `dataset.class_to_idx` instead of assuming an order.
- Use supported image extensions or pass `is_valid_file` if extension filtering is too strict.
- Set `allow_empty=True` only when empty class folders are intentional; otherwise populate or remove empty folders.
- For official datasets, inspect the dataset-specific expected layout; many benchmark datasets are not `ImageFolder`-compatible.

## Custom dataset transform errors

Symptoms:

- `ValueError: Only transforms or transform/target_transform can be passed as argument`.
- v2 transforms fail because boxes, masks, images, or videos are plain tensors without metadata.
- Detection target dictionaries lose `canvas_size` or box format information.

Fixes:

- With `VisionDataset`, pass either combined `transforms(sample, target)` or separate `transform` and `target_transform`, not both.
- Use `wrap_dataset_for_transforms_v2()` for supported built-in detection, segmentation, video, and classification datasets.
- If the wrapper does not support a dataset/mode, write a small adapter that returns `tv_tensors.Image`, `BoundingBoxes`, `Mask`, or `Video` objects. Route metadata details to `../transforms-and-tv-tensors/`.

## Image extension or codec failures

Symptoms:

- `RuntimeError: Couldn't load the image extension`.
- JPEG/PNG decoding fails even for simple files.
- AVIF or HEIC decode asks for `torchvision-extra-decoders`.
- WebP, AVIF, HEIC, or CUDA JPEG support differs across machines.

Fixes:

- Confirm the installed TorchVision image extension can load by decoding a tiny PNG or running `scripts/check_dataset_io.py`.
- If built from source, ensure libjpeg and libpng were found at build time; set `TORCHVISION_WARN_WHEN_EXTENSION_LOADING_FAILS=1` and retry for more detail.
- Use `decode_image(path, mode="RGB")` for JPEG/PNG/WebP/GIF where supported; use `decode_avif` or `decode_heic` directly for AVIF/HEIC and install `torchvision-extra-decoders` only when allowed.
- For robust application code, catch decode failures and fall back to PIL for common formats when TorchVision image ops are unavailable.
- Do not assume CUDA JPEG decode exists; it requires a compatible build and CUDA stack.

## Tensor dtype, shape, and channel mistakes

Symptoms:

- Encoders raise `Input tensor dtype should be uint8`.
- Encoders reject tensors with shape `H,W`, `B,C,H,W`, or unsupported channel counts.
- Visualization helpers raise `Pass individual images, not batches` or `Pass an RGB image`.
- Colors look wrong after drawing or saving.

Fixes:

- Decode output is channel-first `C,H,W`; most encoders want a single image tensor, not a batch.
- Encode PNG/JPEG with `torch.uint8` tensors in byte range; convert normalized floats before writing.
- `draw_bounding_boxes` accepts grayscale or RGB single images, but `draw_segmentation_masks` and `draw_keypoints` require RGB `3,H,W` images.
- Masks for `draw_segmentation_masks` must be boolean and shaped `H,W` or `N,H,W` with the same spatial size as the image.
- If using `make_grid`, pass a list of same-sized image tensors or a `B,C,H,W` batch.

## Video dataset and TorchCodec issues

Symptoms:

- Video dataset construction warns that TorchVision video decoding moved to TorchCodec.
- Clip extraction fails because `torchcodec` is missing.
- Legacy `torchvision.io.read_video`, `write_video`, or video reader examples no longer work in newer installations.

Fixes:

- For new code, use TorchCodec for video/audio decoding and keep TorchVision responsible for dataset classes and transform-compatible sample structures.
- Install TorchCodec only when the user approves the dependency and the environment supports it.
- When a task is about image datasets or image IO, avoid importing video helpers just to smoke-test TorchVision.
- Treat C++ video/IO examples as public high-level limitations unless a maintainer explicitly asks to port them.

## Visualization label and color errors

Symptoms:

- `Number of boxes and labels mismatch`.
- Color parsing errors for tuples or lists.
- Box drawing complains about box order.
- Font size appears ignored.

Fixes:

- Provide exactly one label per box, or omit labels entirely.
- Use a single color (`"red"` or `(255, 0, 0)`) for all objects, or a list with one color per object.
- For axis-aligned boxes, pass absolute `XYXY` boxes where `xmin <= xmax` and `ymin <= ymax`; use `torchvision.ops.box_convert` for other formats.
- Set `font` when setting `font_size`; otherwise font size may be ignored by the default font.
