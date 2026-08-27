# YOLOP Model Overview

## When to read

Read this when a task asks what YOLOP predicts, how `get_net(cfg)` is assembled, why training/inference/export see different detection outputs, or how checkpoints and Torch Hub-style loading fit into the repo.

## Core model facts

- Public project purpose: one model jointly handles traffic-object detection, drivable-area segmentation, and lane-line segmentation for driving scenes.
- Source import root: `lib`.
- Main Python factory: `from lib.models import get_net`; call `get_net(cfg)` with `cfg` from `lib.config`.
- Main class: `MCnet` in `lib/models/YOLOP.py`.
- Default architecture list: `YOLOP` in `lib/models/YOLOP.py` with output indices `[24, 33, 42]`.
- Detection head: `Detect` in `lib/models/common.py`, YOLO-style anchor/grid output with `nc=1` by default (traffic object vs background) and three detection scales.
- Segmentation heads: two class-logit maps for drivable area and lane line. The model applies sigmoid in `lib/models/YOLOP.py` before returning segmentation tensors.

## Forward outputs

`lib.models.YOLOP.MCnet.forward(x)` returns a list-like value with three logical heads:

1. `det_out`: detection head output.
   - In training mode the detection head returns the raw per-scale tensors needed by `MultiHeadLoss`.
   - In eval mode the `Detect` module returns a tuple `(concatenated_predictions, raw_per_scale_outputs)`.
2. `da_seg_out`: drivable-area segmentation tensor with shape similar to `[batch, 2, height, width]`.
3. `ll_seg_out`: lane-line segmentation tensor with shape similar to `[batch, 2, height, width]`.

The source `export_onnx.py` defines its own export-focused `MCnet` wrapper that returns exactly `(det_out, drive_area_seg, lane_line_seg)` in eval mode. Prefer that wrapper for ONNX export so the exported model has the expected output names instead of extra flattened detection feature-map outputs.

## Checkpoints and weights

- PyTorch training checkpoints are dictionaries with at least `epoch`, `model`, `state_dict`, and `optimizer` when saved by `save_checkpoint`.
- The README and demos use `weights/End-to-end.pth` as the default pretrained multitask checkpoint.
- Exported ONNX files are named by resolution in the source repo convention: `yolop-320-320.onnx`, `yolop-640-640.onnx`, `yolop-1280-1280.onnx`.
- TensorRT preparation uses a text `.wts` file produced by serializing every tensor in the PyTorch `state_dict` as big-endian float hex values.

## Torch Hub-style loading

`hubconf.py` exposes `yolop(pretrained=True, device="cpu")`:

- It builds `get_net(cfg)`.
- When `pretrained=True`, it loads `weights/End-to-end.pth` relative to the `hubconf.py` file.
- It calls `select_device(device=...)` and moves the model to that device.

For agent workflows, direct `get_net(cfg)` plus explicit checkpoint loading is usually easier to debug because it keeps the repo root, checkpoint path, device, and config object visible.

## Model variants present in source

`lib/models/YOLOP.py` contains several commented architecture lists for ablations: shared segmentation branches, no-share branches, feedback variants, and sharpen/lane variants. The active default at the bottom of the file is the no-share YOLOP architecture with detection head at index 24 and segmentation heads at 33 and 42.

Do not assume changing one architecture list automatically changes `get_net`; check which list `m_block_cfg = YOLOP` references.

## Verification notes

A CPU dummy forward with an input tensor shaped `[1, 3, 128, 128]` verified that the active `get_net(cfg)` model constructs and returns detection plus two segmentation outputs. That smoke validates API shape, not checkpoint quality, BDD100K metrics, CUDA speed, or TensorRT compatibility.
