# API Reference

## Purpose

Use this when you need the verified class and helper signatures for the source
modules. It keeps the root router short while giving future agents enough detail
to reason about inputs, outputs, and backend behavior.

## Model classes

### `model.Base(backbone, in_channels, out_channels)`
Generic encoder-decoder base network used internally by the matting models.
Backbone choices are `resnet50`, `resnet101`, and `mobilenetv2`.

### `model.MattingBase(backbone: str)`
Coarse matting model for source/background pairs.

- Input: `src`, `bgr` with identical `B,3,H,W` shapes.
- Output: `pha`, `fgr`, `err`, `hid`.
- Inference users normally consume `pha` and `fgr` only.

### `model.MattingRefine(backbone: str, backbone_scale: float = 0.25, refine_mode: str = 'sampling', refine_sample_pixels: int = 80000, refine_threshold: float = 0.1, refine_kernel_size: int = 3, refine_prevent_oversampling: bool = True, refine_patch_crop_method: str = 'unfold', refine_patch_replace_method: str = 'scatter_nd')`
Full-resolution refinement model.

- `backbone_scale` must be `<= 0.5`.
- `refine_mode` accepts `sampling`, `thresholding`, or `full`.
- `refine_patch_crop_method` accepts `unfold`, `roi_align`, or `gather`.
- `refine_patch_replace_method` accepts `scatter_nd` or `scatter_element`.
- Input `src` and `bgr` must have the same shape and height/width divisible by 4.
- Output tuple: `pha`, `fgr`, `pha_sm`, `fgr_sm`, `err_sm`, `ref_sm`.

### `model.Refiner(mode, sample_pixels, threshold, kernel_size=3, prevent_oversampling=True, patch_crop_method='unfold', patch_replace_method='scatter_nd')`
Internal patch refiner used by `MattingRefine`.

### Encoders and decoder
- `model.ResNetEncoder(in_channels, variant='resnet101')`
- `model.MobileNetV2Encoder(in_channels, norm_layer=None)`
- `model.Decoder(channels, feature_channels)`

## Dataset helpers

### `dataset.ImagesDataset(root, mode='RGB', transforms=None)`
Recursively collects `*.jpg` and `*.png` from `root` and returns PIL images or
transformed tensors.

### `dataset.VideoDataset(path, transforms=None)`
Reads a video file with OpenCV and exposes random access by frame index.

### `dataset.SampleDataset(dataset, samples)`
Downsamples a dataset to a bounded number of evenly spaced samples.

### `dataset.ZipDataset(datasets, transforms=None, assert_equal_length=False)`
Zips multiple datasets together and optionally asserts pairwise equal length.

## Utility

### `inference_utils.HomographicAlignment`
OpenCV/ORB-based alignment helper for matching the background to the source
image before matting.

### `model.utils.load_matched_state_dict(model, state_dict, print_stats=True)`
Loads only matching state-dict keys and shapes. Useful for partial checkpoint
compatibility, especially when adapting pretraining or older checkpoints.

## High-value facts

- `MattingRefine` is the main inference class for HD/4K use cases.
- `MattingBase` is the coarse-only model used during training and inference.
- `ImagesDataset` and `VideoDataset` are the only repo-owned data loaders needed
  for the public demo workflows.
- `ZipDataset` is important because the CLIs pair source and background inputs.
