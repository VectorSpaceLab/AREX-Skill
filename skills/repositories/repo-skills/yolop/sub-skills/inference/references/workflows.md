# YOLOP PyTorch Inference Workflows

## When to read

Read this when running the PyTorch demo, adapting image/video inference, interpreting output files, or deciding whether to use the source script or the bundled helper.

## Source demo command

From a YOLOP checkout root:

```bash
PYTHONPATH=. python tools/demo.py \
  --source inference/images \
  --weights weights/End-to-end.pth \
  --img-size 640 \
  --conf-thres 0.25 \
  --iou-thres 0.45 \
  --device cpu \
  --save-dir inference/output
```

`--source` can be a file, folder, video, glob, or numeric camera id in the source script. In headless automation, prefer image/folder/video paths and avoid numeric camera ids unless a display/camera runtime is available.

## Bundled helper

The generated skill includes a safer helper:

```bash
python sub-skills/inference/scripts/run_demo_inference.py \
  --repo-root /path/to/YOLOP \
  --weights /path/to/YOLOP/weights/End-to-end.pth \
  --source /path/to/YOLOP/inference/images \
  --save-dir /tmp/yolop-demo-output \
  --device cpu \
  --max-items 3
```

It adapts the source demo but:

- Accepts `--repo-root` instead of assuming the checkout root.
- Does not delete an existing output directory by default.
- Rejects numeric camera sources by default because camera/GUI runtime is not a safe smoke.
- Uses explicit output paths suitable for temporary verification.

## Preprocessing path

The demo uses `LoadImages`/`LoadStreams` from `lib/dataset/DemoDataset.py`:

1. Resolve file/folder/glob/video/camera source.
2. Read image frames with OpenCV.
3. Letterbox to the requested `--img-size` using `letterbox_for_img`.
4. Convert to a contiguous numpy array.
5. Apply torchvision `ToTensor()` and ImageNet normalization with mean `[0.485, 0.456, 0.406]` and std `[0.229, 0.224, 0.225]`.

The source loader leaves frames in OpenCV BGR order before the transform. Preserve source behavior when comparing to native outputs.

## Model and postprocessing path

`tools/demo.py`:

1. Builds `get_net(cfg)`.
2. Loads `checkpoint["state_dict"]` from the weights path.
3. Moves the model to the selected device and uses half precision only when the device is not CPU.
4. Runs model inference under `torch.no_grad()`.
5. Takes `inf_out, _ = det_out` from the eval-mode detection tuple.
6. Applies `non_max_suppression` with `--conf-thres` and `--iou-thres`.
7. Crops letterbox padding from drivable and lane segmentation outputs.
8. Interpolates segmentation masks back to source frame size.
9. Blends segmentation masks and draws detection boxes.

## Save outputs

- Image mode: one output image per input file, named after the input basename.
- Video mode: writes an mp4 output to the save directory.
- Stream mode in the source script: displays GUI frames; avoid in non-interactive/headless contexts.

## When no boxes are found

YOLOP still writes segmentation overlays even when NMS returns zero boxes. Treat empty detections as a model/confidence/input condition, not necessarily a script failure. Lowering `--conf-thres` can help diagnose whether predictions exist.
